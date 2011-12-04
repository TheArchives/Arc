# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class LavaPlugin(ProtocolPlugin):

    hooks = {
        "poschange": "posChanged",
    }

    def gotClient(self):
        self.died = False

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        if hasattr(self.client.world.blockstore, "raw_blocks"):
            try:
                check_offset = self.client.world.blockstore.get_offset(rx, ry, rz)
                try:
                    block = self.client.world.blockstore.raw_blocks[check_offset]
                except IndexError:
                    return
                check_offset = self.client.world.blockstore.get_offset(rx, ry-1, rz)
                blockbelow = self.client.world.blockstore.raw_blocks[check_offset]
            except (KeyError, AssertionError):
                pass
            else:
                if block == chr(BLOCK_LAVA) or blockbelow == chr(BLOCK_LAVA):
                    # Ok, so they touched lava. Warp them to the spawn, timer to stop spam.
                    if not self.died:
                        self.died = True
                        self.client.teleportTo(self.client.world.spawn[0], self.client.world.spawn[1], self.client.world.spawn[2], self.client.world.spawn[3])
                        self.client.factory.sendMessageToAll("%s%s has died from lava." % (COLOUR_DARKRED, self.client.username), "server", self.client)
                        reactor.callLater(1, self.gotClient)