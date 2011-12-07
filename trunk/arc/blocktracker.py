# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

# This blocktracker was written by Clay Sweetser, AKA Varriount (clay.sweetser@gmail.com)

from os import getcwd, path
from threading import Thread

from twisted.enterprise import adbapi

class Tracker(Thread):
    """ Provides facilities for block tracking and storage. """
    def __init__(self, world, buffersize=500, directory=getcwd()):
        """ Set up database pool, buffers, and other preperations """
        Thread.__init__(self)
        self.deamon = True
        self.database = adbapi.ConnectionPool('sqlite3', path.join(directory, world+'.db'), check_same_thread=False)
        self.databuffer = list()
        self.buffersize = buffersize
        def c(r):
            if isinstance(r, Exception) or len(r) == 0: # Contradictationay conditions :P
                self.database.runOperation('CREATE TABLE history (block_offset INTEGER, matbefore INTEGER, matafter INTEGER, name VARCHAR(50), date DATE)')
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