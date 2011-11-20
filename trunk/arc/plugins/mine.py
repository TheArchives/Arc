# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class MinePlugin(ProtocolPlugin):

    commands = {
        "mine": "commandMine",
        "clearmines": "commandClearMines",
    }

    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.build_mines = False

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        if fromloc != "user":
            # People shouldn't be blbing mines
            return
        if self.client.world.has_mine(x, y, z):
            self.client.sendServerMessage("You defused a mine!")
            self.client.world.delete_mine(x, y, z)
        if self.build_mines and block == BLOCK_BLACK:
            self.build_mines = False
            self.client.world.add_mine(x, y, z)
            self.client.sendServerMessage("Your mine is now active!")

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        mx = rx
        mz = rz
        my = ry - 2
        tobuild = []
        world = self.client.world
        fanout = 3
        try:
            if world.has_mine(mx, my, mz) or world.has_mine(mx, my-1, mz):
                if world.has_mine(mx, my-1, mz):
                    world.delete_mine(mx, my-1, mz)
                    my = ry - 3
                if world.has_mine(mx, my, mz):
                    my = ry - 2
                    world.delete_mine(mx, my, mz)
        except AssertionError: # Out of bounds
            pass
        else:
            for i in range(-fanout, fanout+1):
                for j in range(-fanout, fanout+1):
                    for k in range(-fanout, fanout+1):
                        if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < fanout:
                            if not self.client.AllowedToBuild(mx+i, my+j, mz+k):
                                return
                            check_offset = world.blockstore.get_offset(mx+i, my+j, mz+k)
                            blocktype = world.blockstore.raw_blocks[check_offset]
                            if blocktype not in [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD)]:
                                if not world.has_mine(mx+i, my+j, mz+k):
                                    tobuild.append((i, j, k))
            def explode(block, save):
                # Send the explosion
                for dx, dy, dz in tobuild:
                    try:
                        if save: world[mx+dx, my+dy, mz+dz] = chr(block)
                        self.client.sendBlock(mx+dx, my+dy, mz+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (mx+dx, my+dy, mz+dz, block)))
                    except AssertionError: # Out of bounds
                        pass
            # Explode in 0.5 seconds
            self.client.sendServerMessage("*CLICK*")
            reactor.callLater(0.5, explode, BLOCK_STILLLAVA, False)
            # Explode2 in 1 seconds
            reactor.callLater(1, explode, BLOCK_AIR, True)

    def newWorld(self, world):
        "Hook to reset mine abilities in new worlds if not op."
        if not self.client.isOp():
            self.build_mines = False

    @config("category", "build")
    @config("rank", "op")
    @on_off_command
    def commandMine(self, onoff, fromloc, overriderank):
        "/mine - Op\nMakes the next black block you place a mine. Toggle."
        self.build_mines = True
        self.client.sendServerMessage("You are now placing mine blocks; Place a black block!")

    @config("category", "build")
    @config("rank", "worldowner")
    def commandClearMines(self, parts, fromloc, overriderank):
        "/clearmines - World Owner\nClears all mines in this world."
        self.client.world.clear_mines()
        self.client.sendServerMessage("All mines in this world have been cleared.")