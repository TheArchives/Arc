# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor, threads

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class BlbPlugin(ProtocolPlugin):
    commands = {
        "blb": "commandBlb",
        "draw": "commandBlb",
        "cuboid": "commandBlb",
        "cub": "commandBlb",
        "box": "commandBlb",
        "bhb": "commandHBlb",
        "hbox": "commandHBlb",
        "bwb": "commandWBlb",
        "bcb": "commandBcb",
        "bhcb": "commandBhcb",
        "bfb": "commandFBlb",
        "newblb": "commandNBlb",
        "oblb": "commandOneBlb",
        "bob": "commandOneBlb",
        }

    @config("category", "build")
    @config("rank", "builder")
    def commandOneBlb(self, parts, fromloc, overriderank):
        "/bob blockname [x y z] - Builder\nAliases: oblb\nSets block to blocktype.\nClick 1 block then do the command."
        if len(parts) < 5 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly a coord triple)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last block place
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked a block yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            try:
                if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                    return
                self.client.world[x, y, z] = block
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=self.client.world)
                self.client.sendBlock(x, y, z, block)
            except AssertionError:
                self.client.sendServerMessage("Out of bounds bob error.")
                return
            else:
                if fromloc == "user":
                    self.client.sendServerMessage("Your bob just finished.")

    @config("category", "build")
    @config("rank", "director")
    def commandNBlb(self, parts, fromloc, overriderank):
        "/newblb blockname [x y z x2 y2 z2] - Director\nSets all blocks in this area to block.\nClick 2 corners then do the command."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            realLimit = (x2 - x) * (y2 - y) * (z2 - z)
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if (realLimit > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to blb (Limit is %s)" % limit)
                    return
            world = self.client.world
            if realLimit >= 45565: # To test it out first, will try a bigger one later - tyteen
                self.client.sendServerMessage("BLB has been started.")

                def doBlocks():
                    # This implements 2 new things: Respawn method and try-the-whole-loop.
                    # Since the loop stops when an AssertionErrors pops up, so we just
                    # go and check the whole loop, so there isn't a need to try the block
                    # Everytime.
                    # The respawn method changes the BLB proceedures as follows:
                    # 1. Change the block but DOES NOT send it to users
                    # 2. Respawn the users in world
                    # Since this method does not send blocks one by one but respawns to download
                    # the map at one time, it saves time.
                    # All clients will get respawned too.
                    # Credits to UberFoX for this idea. Thanks Stacy!
                    try:
                        for i in range(x, x2 + 1):
                            for j in range(y, y2 + 1):
                                for k in range(z, z2 + 1):
                                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                        return
                                    world[i, j, k] = block
                        self.client.sendServerMessage("BLB finished. Respawning...")
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds blb error.")
                        return

                d = threads.deferToThread(doBlocks)
                # Now the fun part. Respawn them all!
                def blbCallback():
                    for client in world.clients.values():
                        client.sendPacked(TYPE_INITIAL, 6,
                            ("%s: %s" % (self.client.factory.server_name, self.client.world.id)),
                            "Reloading the world...", self.client.canBreakAdminBlocks() and 100 or 0)
                    if fromloc == "user":
                        self.client.sendServerMessage("Your blb just completed.")

                d.addCallback(blbCallback)
            else:
                def generate_changes():
                    try:
                        for i in range(x, x2 + 1):
                            for j in range(y, y2 + 1):
                                for k in range(z, z2 + 1):
                                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                        return
                                    world[i, j, k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                    self.client.sendBlock(i, j, k, block)
                                    yield
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds blb error.")
                        return

                block_iter = iter(generate_changes())

                def do_step():
                    try:
                        for x in range(10):
                            block_iter.next()
                        reactor.callLater(0.01, do_step)
                    except StopIteration:
                        if fromloc == "user":
                            self.client.sendServerMessage("Your blb just completed.")
                        pass

                do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandBlb(self, parts, fromloc, overriderank):
        "/blb blockname [x y z x2 y2 z2] - Builder\nAliases: box, cub, cuboid, draw\nSets all blocks in this area to block.\nClick 2 corners then do the command."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to blb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                try:
                    for i in range(x, x2 + 1):
                        for j in range(y, y2 + 1):
                            for k in range(z, z2 + 1):
                                if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                    return
                                world[i, j, k] = block
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds blb error.")
                    return

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your blb just completed.")
                    pass

            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandHBlb(self, parts, fromloc, overriderank):
        "/bhb blockname [x y z x2 y2 z2] - Builder\nAliases: hbox\nSets all blocks in this area to block, hollow."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to bhb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                try:
                    for i in range(x, x2 + 1):
                        for j in range(y, y2 + 1):
                            for k in range(z, z2 + 1):
                                if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                    return
                                if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
                                    world[i, j, k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                    self.client.sendBlock(i, j, k, block)
                                    yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds bhb error.")
                    return

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your bhb just completed.")
                    pass

            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandWBlb(self, parts, fromloc, overriderank):
        "/bwb blockname [x y z x2 y2 z2] - Builder\nBuilds four walls between the two areas.\nHollow, with no roof or floor."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type.")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
                # TODO: Fix the formula
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to bwb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                return
                            if i == x or i == x2 or k == z or k == z2:
                                try:
                                    world[i, j, k] = block
                                    self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bwb error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your bwb just completed.")
                    pass

            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandBcb(self, parts, fromloc, overriderank):
        "/bcb blockname blockname2 [x y z x2 y2 z2] - Builder\nSets all blocks in this area to block, checkered."
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter two types (and possibly two coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            block2 = self.client.GetBlockValue(parts[2])
            if block == None or block2 == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to bcb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                ticker = 0
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            try:
                                if (i + j + k) % 2 == 0:
                                    ticker = 1
                                else:
                                    ticker = 0
                                if ticker == 0:
                                    world[i, j, k] = block
                                else:
                                    world[i, j, k] = block2
                            except AssertionError:
                                self.client.sendServerMessage("Out of bounds bcb error.")
                                return
                            if ticker == 0:
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
                                self.client.sendBlock(i, j, k, block2)
                            else:
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                            yield

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your bcb just completed.")
                    pass

            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandBhcb(self, parts, fromloc, overriderank):
        "/bhcb blockname blockname2 [x y z x2 y2 z2] - Builder\nSets all blocks in this area to blocks, checkered hollow."
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter two block types")
        else:
            block = self.client.GetBlockValue(parts[1])
            block2 = self.client.GetBlockValue(parts[2])
            if block == None or block2 == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
                # TODO: Fix the formula
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to blb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                ticker = 0
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
                                try:
                                    if (i + j + k) % 2 == 0:
                                        ticker = 1
                                    else:
                                        ticker = 0
                                    if ticker == 0:
                                        world[i, j, k] = block
                                    else:
                                        world[i, j, k] = block2
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bhcb error.")
                                    return
                                if ticker == 0:
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
                                    self.client.sendBlock(i, j, k, block2)
                                else:
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                    self.client.sendBlock(i, j, k, block)
                                yield

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your bhcb just completed.")
                    pass

            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandFBlb(self, parts, fromloc, overriderank):
        "/bfb blockname [x y z x2 y2 z2] - Builder\nSets all blocks in this area to block, wireframe."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
                # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
                # TODO: Fix the formula
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to bfb (Limit is %s)" % limit)
                    return
                # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world

            def generate_changes():
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            if (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or (
                            i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or (
                            i == x and k == z2) or (j == y and k == z2) or (i == x2 and k == z) or (
                            j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                                try:
                                    world[i, j, k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bfb error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield

                # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())

            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your bfb just completed.")
                    pass

            do_step()
