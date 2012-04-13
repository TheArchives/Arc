# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import time
from os import getcwd, path
from threading import Thread

from twisted.enterprise import adbapi

from arc.constants import *
from arc.decorators import *

class BlockTrackerPlugin(object):
    name = "BlockTrackerPlugin"
    commands = {
        "checkblock": "commandCheckBlock",
        "checkplayer": "commandCheckPlayer",
        "restoreplayer": "commandRestorePlayer",
        "cb": "commandCheckBlock",
        "cp": "commandCheckPlayer",
        "rp": "commandRestorePlayer",
        "undo": "commandRestorePlayer",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "blockdetect": "blockDetected",
        "onBlockChange": "blockChanged",
        "worldInstanceLoaded": "worldInstanceLoaded",
        "worldInstanceStopped": "worldInstanceStopped",
    }

    def gotClient(self, data):
        data["client"].isChecking = False

    def worldInstanceLoaded(self, data):
        data["world"].blocktracker = Tracker("blocks", directory=data["world"].basename)

    def worldInstanceStopped(self, data):
        try:
            data["world"].blocktracker.close()
            del self.blocktracker
        except AttributeError:
            pass

    def sendCallbackRestorePlayer(self, data, num, client):
        j = len(data)
        done = []
        if num == -1:
            for i in range(j):
                done.append(data.pop())
            i = len(done)
        elif j > num:
            for i in range(num):
                done.append(data.pop())
            done.reverse()
            i = len(done)
        else:
            done = data
            i = len(data)
        try:
            name = done[0][3].encode("ascii", "ignore")
        except Exception:
            client.sendServerMessage("No edits could be found for that player!")
        else:
            client.sendServerMessage("Reverting %s edits for %s (out of %s)..." % (i, name, j))
            changeset = {}
            for element in done:
                offset, before, after, player, date = element
                x, y, z = world.get_coords(offset)
                changeset[(x, y, z)] = chr(before)
            client.sendServerMessage("Reverted %s edits." % i)

    def sendCallbackPlayer(self, data, client):
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
            client.sendServerMessage("No edits could be found for that player!")
        else:
            client.sendServerMessage("Listing last %s edits for %s (out of %s)..." % (len(done), name, len(data)))
            for element in done:
                offset, before, after, player, date = element
                date = time.strftime("%d/%m %H:%M:%S", time.gmtime(date))
                coords = self.client.world.get_coords(offset)
                client.sendServerMessage("[%s] (%s, %s, %s) %s -> %s" % 
                    (date, coords[0], coords[1], coords[2], before, after))

    def sendCallbackBlock(self, data, client):
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
            client.sendServerMessage("No edits could be found for that block!")
        else:
            client.sendServerMessage("Listing last %s edits (out of %s)..." % (len(done), len(data)))
            for element in done:
                offset, before, after, player, date = element
                date = time.strftime("%d/%m %H:%M:%S", time.gmtime(date))
                coords = client.world.get_coords(offset)
                client.sendServerMessage("[%s] (%s, %s, %s) %s: %s -> %s" % 
                    (date, coords[0], coords[1], coords[2], player.encode("ascii", "ignore"), before, after))

    def blockDetected(self, data):
        "Hook trigger for block changes."
        if not data["client"].isChecking: # Only add this block entry if we are not checking a block
            before_block = data["client"].world.blockstore[x, y, z]
            if before_block == u'':
                before_block = 0
            elif isinstance(before_block, Deferred):
                # Nope, wait a bit
                reactor.callLater(0.1, self.blockDetected, data)
            else:
                before_block = ord(before_block)
            data["client"].world.blocktracker.add((
                    data["client"].world.get_offset(x, y, z), before_block, block, data["client"].username.lower(),
                    time.mktime(time.localtime())))

    def blockChanged(self, data):
        if data["client"].isChecking: # Reverts the change if we are in checking mode
            data["client"].world.blocktracker.getblockedits(self.client.world.get_offset(x, y, z)).addCallback(self.sendCallbackBlock)
            data["client"].isChecking = False
            block = self.client.world.blockstore[data["x"], data["y"], data["z"]]
            if block == u'':
                block = 0
            else:
                block = ord(block)
            return block

    @config("category", "build")
    @config("usage", "[world x y z]")
    def commandCheckBlock(self, data):
        "Checks the next edited block for past edits."
        if data["fromloc"] == "user":
            if not data["client"].isChecking:
                data["client"].sendServerMessage("Checking for edits: Place or remove a block!")
                data["client"].isChecking = True
            else:
                data["client"].sendServerMessage("Already checking for edits: Place or remove a block!")
        else:
            if len(data["parts"]) != 6:
                data["client"].sendServerMessage("You must provide a coord-triplet and a booted world to use the command.")
                return
            if data["parts"][1] not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is not booted.")
                return
            data["client"].world.blocktracker.getblockedits(data["client"].world.get_offset(data["parts"][2], data["parts"][3], data["parts"][4])).addCallback(self.sendCallbackBlock, client=data["client"])
            data["client"].sendServerMessage("Getting information, please wait...")

    @config("category", "build")
    @config("usage", "playername [world]")
    def commandCheckPlayer(self, data):
        "Checks a player's edits on this world, or a world specified."
        if len(data["parts"]) > 2:
            if len(data["parts"]) == 3:
                if data["parts"][2] not in self.factory.keys():
                    data["client"].sendServerMessage("That world is not booted.")
                    return
                self.factory.worlds[data["parts"][2]].blocktracker.getplayeredits(data["parts"][1]).addCallback(self.sendCallbackPlayer, client=data["client"])
            else:
                if fromloc == "user":
                    data["client"].world.blocktracker.getplayeredits(data["parts"][1]).addCallback(self.sendCallbackPlayer, client=data["client"])
                else:
                    data["client"].sendServerMessage("Syntax: /checkplayer playername world")
        else:
            data["client"].sendServerMessage("Syntax: /checkplayer playername [world]")

    @config("category", "build")
    @config("usage", "number|all [username world]")
    def commandRestorePlayer(self, data):
        "Reverse n edits on the current world (or a world specified) by yourself.\nFor Mod+, you can also specify a username."
        if len(data["parts"]) < 2:
            self.client.sendServerMessage("Syntax: /undo number|all [username world]")
            return
        if data["parts"][1] == "all":
            num = -1
        else:
            try:
                data["client"].blocktracker_num = int(data["parts"][1])
            except:
                data["client"].sendServerMessage("n must be a number or \"all\"!")
                return
            if num < 0:
                data["client"].sendServerMessage("n must be greater than 0!")
                return
        if len(data["parts"]) >= 3:
            if not data["client"].isMod():
                data["client"].sendServerMessage("You cannot undo other's block changes!")
                return
            else:
                if fromloc == "user":
                    username = data["parts"][2].lower()
                else:
                    data["client"].sendServerMessage("Syntax: /undo number|all [username world]") 
        else:
            username = data["client"].username.lower()
        if data["parts"] == 4:
            if data["parts"][3] not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is not booted.")
                return
            world = self.factory.worlds[data["parts"][3]]
        else:
            if data["fromloc"] == "user":
                world = data["client"].world
            else:
                data["client"].sendServerMessage("Syntax: /undo number|all [username world]") 
        world.blocktracker.getplayeredits(username).addCallback(self.sendCallbackRestorePlayer, client=data["client"], num=num)


class Tracker(Thread):
    """ Provides facilities for block tracking and storage. """

    def __init__(self, world, buffersize=500, directory=getcwd()):
        """ Set up database pool, buffers, and other preperations """
        Thread.__init__(self)
        self.deamon = True
        self.database = adbapi.ConnectionPool('sqlite3', path.join(directory, world + '.db'), check_same_thread=False)
        self.databuffer = []
        self.buffersize = buffersize

        def c(r):
            if isinstance(r, Exception) or len(r) == 0: # Contradictationay conditions :P
                self.database.runOperation(
                    'CREATE TABLE history (block_offset INTEGER, matbefore INTEGER, matafter INTEGER, name VARCHAR(50), date DATE)')
            self.run = True

        self.database.runQuery("SELECT name FROM sqlite_master WHERE name='history'").addBoth(c)

    def add(self, data):
        """ Adds data to the tracker.
        NOTE the format for a single data entry is this -s
        (matbefore, matafter, name, date) """
        self.databuffer.append(data)
        if len(self.databuffer) > self.buffersize:
            self._flush()

    def close(self):
        """ Flushes and closes the database """
        self._flush()
        self.database.close()

    def _flush(self):
        """ Flushes buffer to database """
        tempbuf = self.databuffer
        self.databuffer = []
        self.database.runInteraction(self._executemany, tempbuf)

    def _executemany(self, cursor, dbbuffer):
        """ Work around for the absence of an executemany in adbapi """
        cursor.executemany("INSERT OR REPLACE INTO history VALUES (?,?,?,?,?)", dbbuffer)
        return None

    def getblockedits(self, offset):
        """ Gets the players that have edited a specified block """
        self._flush()
        edits = self.database.runQuery("SELECT * FROM history WHERE block_offset = (?)", [offset])
        return edits

    def getplayeredits(self, username, filter="all", blocktype="all"):
        """ Gets the blocks, along with materials, that a player has edited """
        # Note: The advanced filtering doesn't work right now, but the old /checkplayer still works.
        # Need to find out why. -tyteen
        self._flush()
        if filter == "before":
            filter_query = "AND matbefore=(?)"
        elif filter == "after":
            filter_query = "AND matafter=(?)"
        elif blocktype != "all" and filter == "all":
            filter_query = "AND (matbefore=(?) OR matafter=(?))"
        else:
            filter_query = ""
        if blocktype != "all":
            block = blocktype
        else:
            block = ""
        theQuery = "SELECT * FROM history AS history WHERE name LIKE (?)" + filter_query
        if blocktype != "all":
            if filter == "all":
                playeredits = self.database.runQuery(theQuery, [username], [block], [block])
            else:
                playeredits = self.database.runQuery(theQuery, [username], [block])
                print filter, theQuery, username, block
        else:
            print theQuery, username, block
            playeredits = self.database.runQuery(theQuery, [username])
        return playeredits

serverPlugin = BlockTrackerPlugin