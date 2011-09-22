# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import datetime

from twisted.internet import reactor, task

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class GreiferDetectorPlugin(ProtocolPlugin):

    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.var_blockchcount = 0
        self.in_publicworld = False
        self.loop = task.LoopingCall(self.griefcheck)
        self.loop.start(self.client.factory.grief_time, now=False)

    def griefcheck(self):
        if self.var_blockchcount >= self.client.factory.grief_blocks:
            self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, (0, COLOUR_DARKGREEN, "Console", ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'Console ALERT', COLOUR_DARKRED, "Possible grief behavior was detected;")), False)))
            self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, (0, COLOUR_DARKGREEN, "Console", ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'Console ALERT', COLOUR_DARKRED, ("World: %s | User: %s" % (self.lastblock_worldname, self.client.username))))), False))
            self.client.logger.warning("%s was detected as a possible griefer in world %s." % (username, worldname))
            self.client.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")+" | #Console ALERT: Possible grief behavior was detected; World: "+self.lastblock_worldname+" | User: "+self.client.username+"\n")
            self.client.adlog.flush()
        self.var_blockchcount = 0

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        world = self.client.world
        if block is BLOCK_AIR and self.in_publicworld:
            if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)]) != 3: # Tunneling
                self.lastblock_worldname = world.id
                self.var_blockchcount += 1

    def newWorld(self, world):
        "Hook to reset griefer count in new worlds."
        if world.all_write and not world.private:
            self.in_publicworld = True
        else:
            self.in_publicworld = False
            self.var_blockchcount = 0
