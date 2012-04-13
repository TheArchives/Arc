# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

class LavaPlugin(object):
    name = "LavaPlugin"
    hooks = {
        "onPlayerConnect": "gotClient",
        "posChange": "posChanged",
        }

    def gotClient(self, data):
        data["client"].died = False

    def posChanged(self, data):
        "Hook trigger for when the user moves"
        rx, ry, rz = data["x"] >> 5, data["y"] >> 5, data["z"] >> 5
        try:
            check_offset = data["client"].world.blockstore.get_offset(rx, ry, rz)
            try:
                block = data["client"].world.blockstore.raw_blocks[check_offset]
            except IndexError:
                return
        except (KeyError, AssertionError):
            pass
        else:
            if block == chr(BLOCK_LAVA):
                # Ok, so they touched lava. Warp them to the spawn, timer to stop spam.
                if not data["client"].died:
                    data["client"].died = True
                    data["client"].teleportTo(data["client"].world.spawn[0], data["client"].world.spawn[1],
                        data["client"].world.spawn[2], data["client"].world.spawn[3])
                    self.factory.sendMessageToAll("%s%s has died from lava." % (COLOUR_DARKRED, data["client"].username), "", data["client"], user=data["client"].username, fromloc=data["fromloc"])
                    reactor.callLater(1, self.playerConnected, {"client": data["client"]})

serverPlugin = LavaPlugin