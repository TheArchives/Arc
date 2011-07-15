# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import time

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class BlockTracker(ProtocolPlugin):

    hooks = {
        "blockchange": "blockChanged"
    }
    
    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        self.client.world.blocktracker.add((self.client.world.get_offset(x, y, z), selected_block, block, self.client.username, time.mktime(time.localtime())))
        return block