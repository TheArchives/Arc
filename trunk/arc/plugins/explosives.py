# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import random

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

UNBREAKABLE = [chr(b) for b in [BLOCK_SOLID, BLOCK_IRON, BLOCK_GOLD, BLOCK_TNT]]
STRONG = [chr(b) for b in [BLOCK_ROCK, BLOCK_STONE, BLOCK_OBSIDIAN, BLOCK_WATER, BLOCK_STILLWATER,
          BLOCK_LAVA, BLOCK_STILLLAVA, BLOCK_BRICK, BLOCK_GOLDORE, BLOCK_IRONORE,
          BLOCK_COAL, BLOCK_SPONGE]]

class ExplosivesPlugin(object):
    name = "ExplosivesPlugin"
    commands = {
        "mine": "commandMine",
        "clearmines": "commandClearMines",
        "tnt": "commandDynamite",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "blockChange": "blockChanged",
        "posChange": "posChanged",
        "newworld": "newWorld",
        }

    # Constants
    explosion_radius = 4
    delay = 2
    fanout = 3

    def gotClient(self, data):
        data["client"].build_mines = False
        data["client"].build_dynamite = False

    def blockChanged(self, data):
        tobuild = []
        world = data["client"].world
        x, y, z, block = data["x"], data["y"], data["z"], data["block"]
        if data["fromloc"] != "user":
            # People shouldn't be blbing mines and TNTs
            return
        if data["client"].world.has_mine(x, y, z):
            data["client"].sendServerMessage("You defused a mine!")
            data["client"].world.delete_mine(x, y, z)
        if self.build_mines and block == BLOCK_BLACK:
            self.build_mines = False
            data["client"].world.add_mine(x, y, z)
            data["client"].sendServerMessage("Your mine is now active!")
        # Randomise the variables
        fanout = random.randint(2, 6)
        if self.build_dynamite and block == BLOCK_TNT:
            # Calculate block change radius
            for i in range(-fanout, fanout + 1):
                for j in range(-fanout, fanout + 1):
                    for k in range(-fanout, fanout + 1):
                        value = (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691
                        if value < fanout:
                            try:
                                if not data["client"].allowedToBuild(x + i, y + j, z + k):
                                    return
                                check_offset = world.blockstore.get_offset(x + i, y + j, z + k)
                                blocktype = world.blockstore.raw_blocks[check_offset]
                                if blocktype not in UNBREAKABLE + STRONG:
                                    if not world.has_mine(x + i, y + j, z + k):
                                        tobuild.append((i, j, k))
                                if value < fanout - 1:
                                    if blocktype not in UNBREAKABLE:
                                        if not world.has_mine(x + i, y + j, z + k):
                                            tobuild.append((i, j, k))
                            except AssertionError: # OOB
                                pass

            def explode(block, save):
                # OK, send the build changes
                for dx, dy, dz in tobuild:
                    try:
                        if save: world[x + dx, y + dy, z + dz] = chr(block)
                        data["client"].sendBlock(x + dx, y + dy, z + dz, block)
                        self.factory.queue.put((data["client"], TASK_BLOCKSET, (x + dx, y + dy, z + dz, block)))
                    except AssertionError: # OOB
                        pass

            # Explode in 2 seconds
            reactor.callLater(self.delay, explode, BLOCK_STILLLAVA, False)
            # Explode2 in 3 seconds
            reactor.callLater(self.delay + 1, explode, BLOCK_AIR, True)

    def posChanged(self, data):
        "Hook trigger for when the user moves."
        rx, ry, rz = data["x"] >> 5, data["y"] >> 5, data["z"] >> 5
        mx, my, mz = rx, ry - 2, rz
        tobuild = []
        world = data["client"].world
        hasMine = False
        try:
            if world.has_mine(mx, my, mz) or world.has_mine(mx, my - 1, mz):
                hasMine = True
                if world.has_mine(mx, my - 1, mz):
                    world.delete_mine(mx, my - 1, mz)
                    my = ry - 3
                if world.has_mine(mx, my, mz):
                    my = ry - 2
                    world.delete_mine(mx, my, mz)
        except AssertionError: # Out of bounds
            pass
        else:
            if hasMine:
                for i in range(-self.fanout, self.fanout + 1):
                    for j in range(-self.fanout, self.fanout + 1):
                        for k in range(-self.fanout, self.fanout + 1):
                            if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < self.fanout:
                                if not data["client"].allowedToBuild(mx + i, my + j, mz + k):
                                    return
                                check_offset = world.blockstore.get_offset(mx + i, my + j, mz + k)
                                blocktype = world.blockstore.raw_blocks[check_offset]
                                if blocktype not in [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD)]:
                                    if not world.has_mine(mx + i, my + j, mz + k):
                                        tobuild.append((i, j, k))

                def explode(block, save):
                    # Send the explosion
                    for dx, dy, dz in tobuild:
                        try:
                            if save: world[mx + dx, my + dy, mz + dz] = chr(block)
                            data["client"].sendBlock(mx + dx, my + dy, mz + dz, block)
                            self.factory.queue.put((data["client"], TASK_BLOCKSET, (mx + dx, my + dy, mz + dz, block)))
                        except AssertionError: # Out of bounds
                            pass

                # Explode in 0.5 seconds
                data["client"].sendServerMessage("*CLICK*")
                reactor.callLater(0.5, explode, BLOCK_STILLLAVA, False)
                # Explode2 in 1 seconds
                reactor.callLater(1, explode, BLOCK_AIR, True)

    def newWorld(self, world):
        "Hook to reset mine abilities in new worlds if not op."
        if not data["client"].isOp():
            data["client"].build_mines = False
            data["client"].build_dynamite = False

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "on|off")
    @config("disabled-on", ["console", "irc", "irc_query", "cmdblock"])
    def commandMine(self, data):
        "Makes the next black block you place a mine. Toggle."
        if data["parts"][1] == "on":
            data["client"].build_mines = True
            data["client"].sendServerMessage("You are now placing mine blocks; Place a black block!")
        elif data["parts"][1] == "off":
            data["client"].build_mines = False
            data["client"].sendServerMessage("You have deactivated mines-building mode.")
        else:
            data["client"].sendServerMessage("Please specify 'on' or 'off'.")

    @config("category", "build")
    @config("rank", "worldowner")
    @config("usage", "world")
    def commandClearMines(self, data):
        "Clears all mines in the specified world, or the current world."
        if data["fromloc"] != "user" and len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must specify a world.")
            return
        if len(data["parts"]) > 2:
            w = data["parts"][2]
            if world not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is not booted.")
                return
            else:
                world = self.factory.worlds[w]
        else:
            world = data["client"].world # Fail-proof
        world.clear_mines()
        data["client"].sendServerMessage("All mines in this world have been cleared.")

    @config("category", "build")
    @config("rank", "op")
    @config("aliases", "dynamite")
    @config("usage", "on|off")
    @config("disabled-on", ["console", "irc", "irc_query", "cmdblock"])
    def commandDynamite(self, data):
        "Explodes a radius around the TNT."
        if data["parts"][1] == "on":
            data["client"].build_dynamite = True
            data["client"].sendServerMessage("You have activated TNT; place a TNT block!")
        elif data["parts"][1] == "off":
            data["client"].build_dynamite = False
            data["client"].sendServerMessage("You have deactivated TNT.")
        else:
            data["client"].sendServerMessage("Please specify 'on' or 'off'.")

serverPlugin = ExplosivesPlugin