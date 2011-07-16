# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import time

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class BlockTrackerPlugin(ProtocolPlugin):

    commands = {
        "checkblock": "commandCheckBlock"
    }

    hooks = {
        "blockchange": "blockChanged"
    }

    def gotClient(self):
        self.isChecking = False

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if not self.isChecking:
            self.client.world.blocktracker.add((self.client.world.get_offset(x, y, z), selected_block, block, self.client.username, time.mktime(time.localtime())))
            return block
        else:
            edits = self.client.world.blocktracker.getblockedits(self.client.world.get_offset(x, y, z))
            self.client.logger.debug("Edits: %s" % edits)
            if edits == None:
                self.client.sendServerMessage("No edits stored for that block.")
            self.isChecking = False
            return selected_block

    @config("category", "build")
    def checkBlock(self, parts, fromloc, overriderank):
        "/checkblock: Checks the next edited block for past edits."
        if not self.isChecking:
            self.client.sendServerMessage("Checking for edits: Place or remove a block!")
            self.isChecking = True
        else:
            self.client.sendServerMessage("Already checking for edits: Place or remove a block!")