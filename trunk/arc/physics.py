# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.


# this thread:
#  receives changes by ATOMIC updates to 'changed' eg. self.changed.add(offset)
#  sends changes by queueing updates in blockstore eg. self.blockstore.in_queue.put([TASK_BLOCKSET, (x, y, z), chr(block), True])
#  reads but doesn't not modify self.blockstore.raw_blocks[]

# optimised by only checking blocks near changes, advantages are a small work set and very upto date


import sys, time
from threading import Thread

from twisted.internet import reactor

from arc.constants import *
from arc.logger import ColouredLogger

import logging

debug = (True if "--debug" in sys.argv else False)

CHR_WATER = chr(BLOCK_WATER)
CHR_LAVA = chr(BLOCK_LAVA)
CHR_AIR = chr(BLOCK_AIR)
CHR_STILLWATER = chr(BLOCK_STILLWATER)
CHR_DIRT = chr(BLOCK_DIRT)
CHR_GLASS = chr(BLOCK_GLASS)
CHR_GRASS = chr(BLOCK_GRASS)
CHR_SPONGE = chr(BLOCK_SPONGE)
CHR_LEAVES = chr(BLOCK_LEAVES)
CHR_SAND = chr(BLOCK_SAND)

BLOCK_SPOUT = BLOCK_DARKBLUE
BLOCK_LAVA_SPOUT = BLOCK_ORANGE
BLOCK_SAND_SPOUT = BLOCK_WHITE
CHR_SPOUT = chr(BLOCK_SPOUT)
CHR_LAVA_SPOUT = chr(BLOCK_LAVA_SPOUT)
CHR_SAND_SPOUT = chr(BLOCK_SAND_SPOUT)

# checks are more expensive here then updates (not sure about for the server and client)
LIMIT_CHECKS = 256*256*256 
LIMIT_UNFLOOD = 256*256*256

class Popxrange():  # there is probably a way to do this without this class but where?
    def __init__(self, start, end):
        self._i = iter(xrange(start, end))
    def pop(self):
        try:
            return self._i.next()
        except StopIteration:
            raise KeyError
    def __len__(self):
        return self._i.__length_hint__()

class Physics(Thread):
    """
    Given a BlockStore, works out what needs doing (water, grass etc.)
    and send the changes back to the BlockStore.
    """

    def __init__(self, blockstore):
        Thread.__init__(self)
        self.blockstore = blockstore
        #self.setDaemon(True) # means that python can terminate even if still active
        #self.work = Event()    # TODO use event to start and stop
        self.last_lag = 0
        self.running = True
        self.was_physics = False
        self.was_unflooding = False
        self.changed = set()
        self.working = set() # could be a list or a sorted list but why bother (world updates may appear in random order but most of the time so many get updated it should be unnoticable)
        self.sponge_locations = set()
        self.logger = ColouredLogger(debug)

    def stop(self):
        self.running = False
        self.join()

    def run(self):
        while self.running:
            if self.blockstore.physics:
                if self.blockstore.unflooding:
                    # Do n fluid removals
                    updates = 0
                    for offset, block in enumerate(self.blockstore.raw_blocks):
                        if block == CHR_LAVA or block == CHR_WATER or block == CHR_STILLWATER or block == CHR_SPOUT or block == CHR_LAVA_SPOUT:
                            x, y, z = self.blockstore.get_coords(offset)
                            self.set_block((x, y, z), BLOCK_AIR)
                            updates += 1
                            if updates >= LIMIT_UNFLOOD:
                                break
                    else:
                        # Unflooding complete.
                        self.blockstore.unflooding = False
                        self.blockstore.world_message(COLOUR_YELLOW + "Unflooding complete.")
                        self.changed.clear()
                        self.working = set()
                else:
                    # If this is the first of a physics run, redo the queues from scratch
                    if not self.was_physics or self.was_unflooding:
                        self.logger.debug("Queue everything for '%s'." % self.blockstore.world_name)
                        self.changed.clear()
                        self.working = Popxrange(0, (self.blockstore.x*self.blockstore.y*self.blockstore.z))

                    # if working list is empty then copy changed set to working set
                    # otherwise keep using the working set till empty
                    elif len(self.working) == 0:
                        self.logger.debug("Performing expand checks for '%s' with %d changes." % (self.blockstore.world_name, len(self.changed)))
                        changedfixed = self.changed # 'changedfixed' is 'changed' so gets all updates
                        self.changed = set()        # until 'changed' is a new set. This and the above statment are ATOMIC
                        self.working = set()         # changes from a Popxrange to a set
                        while len(changedfixed) > 0:
                            self.expand_checks(changedfixed.pop())

                    self.logger.debug("Starting physics run for '%s' with %d checks." % (self.blockstore.world_name, len(self.working)))

                    updates = 0
                    try:
                        for x in xrange(LIMIT_CHECKS):
                            offset = self.working.pop()
                            updates += self.handle(offset)
                    except KeyError:
                        pass

                    #if overflow and (time.time() - self.last_lag > self.LAG_INTERVAL):
                        #self.blockstore.admin_message("Physics is currently lagging in %(id)s.")
                        #self.last_lag = time.time()
                    self.logger.debug("Ended physics run for '%s' with %d updates and %d checks remaining." % (self.blockstore.world_name, updates, len(self.working)))
            else:
                if self.was_physics:
                    self.blockstore.unflooding = False
                    self.changed.clear()
                    self.working = set()
            self.was_physics = self.blockstore.physics
            self.was_unflooding = self.blockstore.unflooding
            # Wait till next iter
            time.sleep(0.7) # TODO change this so takes into account run time

    def handle_change(self, offset, block): # must be ATOMIC
        "Gets called when a block is changed, with its offset and type."
        self.changed.add(offset)

    def set_block(self, (x, y, z), block): # only place blockstore is updated
        "Call to queue a block change, with its position and type."
        self.blockstore.in_queue.put([TASK_BLOCKSET, (x, y, z), chr(block), True])

    def expand_checks(self, offset):
        self.working.add(offset)
        block = self.blockstore.raw_blocks[offset]
        x, y, z = self.blockstore.get_coords(offset)
        #if block == oldblock:
            #return
        # radius of 2 (because of sponge) should be enough
        for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(2)):
            self.working.add(new_offset)
        # handle grass and dirt under
        # if block and oldblock are both either see though or not then ignore
        #bseethough = (block == CHR_AIR) or (block == CHR_GLASS) or (block == CHR_LEAVES)
        #oseethough = (oldblock == CHR_AIR) or (oldblock == CHR_GLASS) or (oldblock == CHR_LEAVES)
        #if bseethough == oseethough:
            #return
        # find first block under that isn't see through
        blocker_offset = offset
        blocker_block = block
        for ny in xrange(y-1, -1, -1):
            test_offset = self.blockstore.get_offset(x, ny, z)
            test_block = self.blockstore.raw_blocks[test_offset]
            if not (test_block == CHR_AIR or test_block == CHR_GLASS or test_block == CHR_LEAVES):
                blocker_offset = test_offset
                blocker_block = test_block
                break
        # if dirt or grass add
        if blocker_offset != offset and (blocker_block == CHR_DIRT or blocker_block == CHR_GRASS):
            self.working.add(blocker_offset)

    def block_radius(self, r):
        "Returns blocks within the radius"
        for x in range(-r, r+1):
            for y in range(-r, r+1):
                for z in range(-r, r+1):
                    if x or y or z:
                        yield (x, y, z)

    def get_blocks(self, x, y, z, deltas):
        "Given a starting point and some deltas, returns all offsets which exist."
        for dx, dy, dz in deltas:
            try:
                new_offset = self.blockstore.get_offset(x+dx, y+dy, z+dz)
                yield x+dx, y+dy, z+dz, new_offset
            except AssertionError:
                pass

    def is_blocked(self, x, y, z):
        "Given coords, determines if the block can see the sky."
        blocked = False
        for ny in xrange(y+1, self.blockstore.y):
            blocker_offset = self.blockstore.get_offset(x, ny, z)
            blocker_block = self.blockstore.raw_blocks[blocker_offset]
            if not ((blocker_block == CHR_AIR) or (blocker_block == CHR_GLASS) or (blocker_block == CHR_LEAVES)):
                blocked = True
                break
        return blocked

    def sponge_within_radius(self, x, y, z, r):
        for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(r)):
            if new_offset in self.sponge_locations:
                if self.blockstore.raw_blocks[new_offset] != CHR_SPONGE:
                    self.sponge_locations.discard(new_offset)
                    continue
                return True
        return False

    def handle(self, offset):
        block = self.blockstore.raw_blocks[offset]
        x, y, z = self.blockstore.get_coords(offset)
        updates = 0

        if block == CHR_DIRT:
            # See if there's any grass next to us
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)]):
                if self.blockstore.raw_blocks[new_offset] == CHR_GRASS:
                    # Alright, can we see the sun?
                    if not self.is_blocked(x, y, z):
                        self.set_block((x, y, z), BLOCK_GRASS)
                        return updates + 1
                    return updates

        elif block == CHR_GRASS:
            # Alright, can we see the sun?
            if self.is_blocked(x, y, z):
                self.set_block((x, y, z), BLOCK_DIRT)
                updates += 1

        # Spouts produce water, lava or sand in finite mode
        elif block == CHR_SPOUT or block == CHR_LAVA_SPOUT or block == CHR_SAND_SPOUT:
            # If there's a gap below, produce water
            if self.blockstore.finite_water:
                try:
                    below = self.blockstore.get_offset(x, y-1, z)
                    if self.blockstore.raw_blocks[below] == CHR_AIR:
                        if block == CHR_SPOUT:
                            self.set_block((x, y-1, z), BLOCK_WATER)
                        elif block == CHR_LAVA_SPOUT:
                            self.set_block((x, y-1, z), BLOCK_LAVA)
                        else:
                            self.set_block((x, y-1, z), BLOCK_SAND)
                        updates += 1
                except AssertionError:
                    pass # At bottom of world

        # Handles sand falling. If there's air below it, it behaves like finite water but stacks instead of spreading.
        elif block == CHR_WATER or block == CHR_STILLWATER or block == CHR_LAVA or block == CHR_SAND:
            # OK, so, can it drop?
            try:
                below = self.blockstore.get_offset(x, y-1, z)
                if self.blockstore.finite_water:
                    if self.blockstore.raw_blocks[below] == CHR_AIR:
                        self.set_block((x, y-1, z), ord(block))
                        self.set_block((x, y, z), BLOCK_AIR)
                        return updates + 2
                    elif self.blockstore.raw_blocks[below] == CHR_SPONGE:
                        self.set_block((x, y, z), BLOCK_AIR)
                        return updates + 1
                else:
                    if self.blockstore.raw_blocks[below] == CHR_AIR and not self.sponge_within_radius(x, y-1, z, 2):
                        self.set_block((x, y-1, z), ord(block))
                        self.set_block((x, y, z), BLOCK_AIR)
                        return updates + 2
            except AssertionError:
                pass # At bottom of world

            # Noice. Now, can it spread?
            if self.blockstore.finite_water:
                # Finite water first tries to move downwards and straight TODO randomise or water will spread in one direction
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, -1, 1), (0, -1, -1), (1, -1, 0), (-1, -1, 0)]):
                    above_offset = self.blockstore.get_offset(nx, ny+1, nz)
                    if self.blockstore.raw_blocks[above_offset] == CHR_AIR:
                        # Air? Fall.
                        if self.blockstore.raw_blocks[new_offset] == CHR_AIR:
                            self.set_block((nx, ny, nz), ord(block))
                            self.set_block((x, y, z), BLOCK_AIR)
                            return updates + 2
                        # Sponge? Absorb.
                        if self.blockstore.raw_blocks[new_offset] == CHR_SPONGE:
                            self.set_block((x, y, z), BLOCK_AIR)
                            return updates + 1
                # Then it tries a diagonal
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(1, -1, 1), (1, -1, -1), (-1, -1, 1), (-1, -1, -1)]):
                    above_offset = self.blockstore.get_offset(nx, ny+1, nz)
                    left_offset = self.blockstore.get_offset(x, ny+1, nz)
                    right_offset = self.blockstore.get_offset(nx, ny+1, z)
                    if self.blockstore.raw_blocks[above_offset] == CHR_AIR and \
                        (self.blockstore.raw_blocks[left_offset] == CHR_AIR or \
                        self.blockstore.raw_blocks[right_offset] == CHR_AIR):
                        # Air? Fall.
                        if self.blockstore.raw_blocks[new_offset] == CHR_AIR:
                            self.set_block((nx, ny, nz), ord(block))
                            self.set_block((x, y, z), BLOCK_AIR)
                            return updates + 2
                        # Sponge? Absorb.
                        if self.blockstore.raw_blocks[new_offset] == CHR_SPONGE:
                            self.set_block((x, y, z), BLOCK_AIR)
                            return updates + 1
                if block == CHR_SAND:
                    return updates
                # TODO got to stop water from stacking, water on water pushes out

            else:
                if block == CHR_SAND:
                    return updates
                # Infinite water spreads in the 4 horiz directions.
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)]):
                    if self.blockstore.raw_blocks[new_offset] == CHR_AIR and not self.sponge_within_radius(nx, ny, nz, 2):
                        self.set_block((nx, ny, nz), ord(block))
                        updates += 1
                # TODO make water levels the same even if tunnel to water is lower then surface

        elif block == CHR_SPONGE:   # TODO check if sponge adding and (below) removal requires re-animation
            # OK, it's a sponge. Add it to sponge locations.
            self.sponge_locations.add(offset)
            # Make sure all the water blocks around it go away
            if not self.blockstore.finite_water:
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(2)):
                    block = self.blockstore.raw_blocks[new_offset]
                    if block == CHR_WATER and block == CHR_LAVA and block == CHR_SAND:
                        self.set_block((nx, ny, nz), BLOCK_AIR)
                        updates += 1
            # If it's finite water, re-animate anything at the edges.
            #if self.blockstore.finite_water:
                #for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(1)):
                    #block = self.blockstore.raw_blocks[new_offset]
                    #if block == CHR_WATER or block == CHR_LAVA:
                        #self.current[FLUID].add(new_offset)

        elif block == CHR_AIR:
            if offset in self.sponge_locations:
                self.sponge_locations.discard(offset)
                ## See if there's some water or lava that needs reanimating
                #for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(3)):
                    #block = self.blockstore.raw_blocks[new_offset]
                    #if block == CHR_WATER or block == CHR_LAVA:
                        #self.current[FLUID].add(new_offset)

        return updates
