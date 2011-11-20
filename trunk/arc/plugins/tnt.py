# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import random

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class DynamitePlugin(ProtocolPlugin):

    commands = {
        "tnt": "commandDynamite",
        "dynamite": "commandDynamite",
    }

    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.build_dynamite = False
        self.explosion_radius = 4
        self.delay = 2

    def newWorld(self, world):
        "Hook to reset dynamiting abilities in new worlds if not op."
        if not self.client.isOp():
            self.build_dynamite = False

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        tobuild = []
        world = self.client.world
        # Randomise the variables
        fanout = random.randint(2, 6)
        unbreakables = [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD), chr(BLOCK_TNT)]
        strongblocks = [chr(BLOCK_ROCK), chr(BLOCK_STONE), chr(BLOCK_OBSIDIAN), chr(BLOCK_WATER), chr(BLOCK_STILLWATER), chr(BLOCK_LAVA), chr(BLOCK_STILLLAVA), chr(BLOCK_BRICK), chr(BLOCK_GOLDORE), chr(BLOCK_IRONORE), chr(BLOCK_COAL), chr(BLOCK_SPONGE)]
        if self.build_dynamite and block == BLOCK_TNT:
            # Calculate block change radius
            for i in range(-fanout, fanout+1):
                for j in range(-fanout, fanout+1):
                    for k in range(-fanout, fanout+1):
                        value = (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691
                        if value < fanout:
                            try:
                                if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                    return
                                check_offset = world.blockstore.get_offset(x+i, y+j, z+k)
                                blocktype = world.blockstore.raw_blocks[check_offset]
                                if blocktype not in unbreakables + strongblocks:
                                    if not world.has_mine(x+i, y+j, z+k):
                                        tobuild.append((i, j, k))
                                if value < fanout - 1:
                                    if blocktype not in unbreakables:
                                        if not world.has_mine(x+i, y+j, z+k):
                                            tobuild.append((i, j, k))
                            except AssertionError: # OOB
                                pass
            def explode(block, save):
                # OK, send the build changes
                for dx, dy, dz in tobuild:
                    try:
                        if save: world[mx+dx, my+dy, mz+dz] = chr(block)
                        self.client.sendBlock(x+dx, y+dy, z+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                    except AssertionError: # OOB
                        pass
            # Explode in 2 seconds
            reactor.callLater(self.delay, explode, BLOCK_STILLLAVA, False)
            # Explode2 in 3 seconds
            reactor.callLater(self.delay+1, explode, BLOCK_AIR, True)

    @config("category", "build")
    @config("rank", "op")
    @on_off_command
    def commandDynamite(self, onoff, fromloc, overriderank):
        "/tnt on|off - Op\nAliases: dynamite\nExplodes a radius around the TNT."
        if onoff == "on":
            self.build_dynamite = True
            self.client.sendServerMessage("You have activated TNT; place a TNT block!")
        else:
            self.build_dynamite = False
            self.client.sendServerMessage("You have deactivated TNT.")