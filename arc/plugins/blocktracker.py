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
        "checkblock": "commandCheckBlock",
        "checkplayer": "commandCheckPlayer",
        "restoreplayer": "commandRestorePlayer"
    }

    hooks = {
        "blockdetect": "blockDetected",
        "blockchange": "blockChanged"
    }

    def gotClient(self):
        self.isChecking = False
        self.num = 0

    def sendCallbackRestorePlayer(self, data):
        j = len(data)
        if j > self.num:
            done = []
            for i in range(self.num):
                done.append(data.pop())
            done.reverse()
            i = len(done)
        else:
            done = data
            i = len(data)
        world = self.client.world
        try:
            name = done[0][3].encode("ascii", "ignore")
        except Exception:
            self.client.sendServerMessage("No edits could be found for that player!")
        else:
            self.client.sendServerMessage("Reverting %s edits for %s (out of %s)..." % (i, name, j))
            for element in done:
                offset, before, after, player, date = element
                x, y, z = world.get_coords(offset)
                world[x, y, z] = chr(before)
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, before), world=world)
                self.client.sendBlock(x, y, z, before)
            self.client.sendServerMessage("Reverted %s edits." % i)
            self.num = 0

    def sendCallbackPlayer(self, data):
        if len(data) > 10:
            done = []
            for i in range(10):
                done.append(data.pop())
            done.reverse()
        else:
            done = data
        try:
            name = done[0][3].encode("ascii", "ignore")
        except Exception:
            self.client.sendServerMessage("No edits could be found for that player!")
        else:
            self.client.sendServerMessage("Listing last %s edits for %s (out of %s)..." % (len(done), name, len(data)))
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
        try:
            name = done[0][3].encode("ascii", "ignore")
        except Exception:
            self.client.sendServerMessage("No edits could be found for that block!")
        else:
            self.client.sendServerMessage("Listing last %s edits (out of %s)..." % (len(done), len(data)))
            for element in done:
                offset, before, after, player, date = element
                date = time.strftime("%d/%m %H:%M:%S", time.gmtime(date))
                coords = self.client.world.get_coords(offset)
                self.client.sendServerMessage("[%s] (%s, %s, %s) %s: %s -> %s" % (date, coords[0], coords[1], coords[2], player.encode("ascii", "ignore"), before, after))

    def blockDetected(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if not self.isChecking: # Only add this block entry if we are not checking a block
            before_block = self.client.world.blockstore.__getitem__((x, y, z))
            if before_block == u'':
                before_block = 0
            else:
                before_block = ord(before_block)
            self.client.world.blocktracker.add((self.client.world.get_offset(x, y, z), before_block, block, self.client.username, time.mktime(time.localtime())))

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        if self.isChecking:
            edits = self.client.world.blocktracker.getblockedits(self.client.world.get_offset(x, y, z))
            edits.addCallback(self.sendCallbackBlock)
            self.isChecking = False
            block = self.client.world.blockstore.__getitem__((x, y, z))
            if block == u'':
                block = 0
            else:
                block = ord(block)
            return block

    @config("category", "build")
    def commandCheckBlock(self, parts, fromloc, overriderank):
        "/checkblock - Guest\nChecks the next edited block for past edits"
        if not self.isChecking:
            self.client.sendServerMessage("Checking for edits: Place or remove a block!")
            self.isChecking = True
        else:
            self.client.sendServerMessage("Already checking for edits: Place or remove a block!")

    @config("category", "build")
    def commandCheckPlayer(self, parts, fromloc, overriderank):
        "/checkplayer playername [before|after|all] [blocktype] - Guest\nChecks a player's edits on this world.\nSpecify 'before' and 'after' with the block type to show edits\nabout that type of block only."
        if len(parts) >= 1:
            if len(parts) == 2:
                self.client.sendServerMessage("You need to specify the block type to view, or specify 'all'.")
                return
            if len(parts) == 3:
                if parts[2].lower() not in ["all", "before", "after"]:
                    self.client.sendServerMessage("Please specify 'before', 'after' or 'all'.")
                    return
                else:
                    filter = parts[2].lower()
                block = self.client.GetBlockValue(parts[3])
                if block == None:
                    return
            else:
                filter = "all"
                block = "all"
            edits = self.client.world.blocktracker.getplayeredits(parts[1], filter, block)
            edits.addCallback(self.sendCallbackPlayer)
        else:
            self.client.sendServerMessage("Syntax: /checkplayer playername [before|after] [blocktype]")

    @config("category", "build")
    @config("rank", "mod")
    def commandRestorePlayer(self, parts, fromloc, overriderank):
        "/restoreplayer username n - Mod\n: Reverse n edits on the current world by username."
        if len(parts) > 2:
            try:
                self.num = int(parts[2])
            except Exception:
                self.client.sendServerMessage("n must be a number!")
            else:
                if self.num > 0:
                    edits = self.client.world.blocktracker.getplayeredits(parts[1])
                    edits.addCallback(self.sendCallbackRestorePlayer)
                else:
                    self.client.sendServerMessage("n must be greater than 0!")
        else:
            self.client.sendServerMessage("Syntax: /restoreplayer playername number")