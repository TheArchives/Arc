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
        "checkblock": "checkBlock",
        "checkplayer": "checkPlayer"
    }

    hooks = {
        "blockchange": "blockChanged"
    }

    def gotClient(self):
        self.isChecking = False

    def sendCallbackPlayer(self, data):
        if len(data) > 10:
            done = []
            for i in range(10):
                done.append(data.pop())
            done.reverse()
        else:
            done = data
        name = done[0][3].encode("ascii", "ignore")
        self.client.sendServerMessage("Listing last %s edits for %s..." % (len(done), name))
        for element in done:
            offset, before, after, player, date = element
            date = time.strftime("%d/%m %H:%M:%S", time.gmtime(date))
            coords = self.client.world.get_coords(offset)
            self.client.sendServerMessage("[%s] (%s, %s, %s) %s -> %s" % (date, coords[0], coords[1], coords[2], before, after))
            
    def sendCallbackBlock(self, data):
        if len(data) > 10:
            done = []
            for i in range(10):
                done.append(data.pop())
            done.reverse()
        else:
            done = data
        self.client.sendServerMessage("Listing last %s edits..." % len(done))
        for element in done:
            offset, before, after, player, date = element
            date = time.strftime("%d/%m %H:%M:%S", time.gmtime(date))
            coords = self.client.world.get_coords(offset)
            self.client.sendServerMessage("[%s] (%s, %s, %s) %s: %s -> %s" % (date, coords[0], coords[1], coords[2], player.encode("ascii", "ignore"), before, after))        
    
    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if not self.isChecking:
            before_block = self.client.world.blockstore.__getitem__((x, y, z))
            if before_block == u'':
                before_block = 0
            else:
                before_block = ord(before_block)
            self.client.world.blocktracker.add((self.client.world.get_offset(x, y, z), before_block, block, self.client.username, time.mktime(time.localtime())))
            return block
        else:
            edits = self.client.world.blocktracker.getblockedits([self.client.world.get_offset(x, y, z)])
            edits.addCallback(self.sendCallbackBlock)
            self.isChecking = False
            block = self.client.world.blockstore.__getitem__((x, y, z))
            if block == u'':
                block = 0
            else:
                block = ord(block)
            return block

    @config("category", "build")
    def checkBlock(self, parts, fromloc, overriderank):
        "/checkblock: Checks the next edited block for past edits."
        if not self.isChecking:
            self.client.sendServerMessage("Checking for edits: Place or remove a block!")
            self.isChecking = True
        else:
            self.client.sendServerMessage("Already checking for edits: Place or remove a block!")
            
    @config("category", "build")
    def checkPlayer(self, parts, fromloc, overriderank):
        "/checkplayer playername: Checks a player's edits on this world."
        if len(parts) > 1:
            edits = self.client.world.blocktracker.getplayeredits(parts[1])
            edits.addCallback(self.sendCallbackPlayer)
        else:
            self.client.sendServerMessage("Syntax: /checkplayer playername")