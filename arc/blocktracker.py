# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

# This blocktracker was written by Clay Sweetser, AKA Varriount (clay.sweetser@gmail.com)

from os import getcwd
from twisted.enterprise import adbapi
from threading import Thread

class Tracker(Thread):
    """ Provides facilities for block tracking and storage. """
    def __init__(self, world, buffersize = 500, directory = getcwd()):
        """ Set up database pool, buffers, and other preperations """
        Thread.__init__(self)
        self.database = adbapi.ConnectionPool('sqlite3', directory+'\\'+world+'.db', cp_min=1, cp_max=1, check_same_thread=False)
        self.databuffer = list()
        self.buffersize = buffersize
        try:
            self.exists = self.database.runQuery("SELECT name FROM sqlite_master WHERE name='history'")
            if len(self.exists) == 0:
                self.d = self.database.runOperation('CREATE TABLE history (block_offset INTEGER, matbefore INTEGER,\
                matafter INTEGER, name VARCHAR(50), date DATE)')
        except:
            i = 1
        finally:
            self.run = True
        #TODO - Pragma statements

    def add(self, data):
        """ Adds data to the tracker.
        NOTE the format for a single data entry is this -s
        (matbefore,matafter,name,date) """
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
        print offset
        print type(offset)
        edits = self.database.runQuery("SELECT * FROM history WHERE block_offset = (?)",[offset])
        return edits

    def getplayeredits(self, username):
        """ Gets the blocks, along with materials, that a player has edited """
        self._flush()
        playeredits = self.database.runQuery("SELECT * FROM history AS history WHERE name LIKE (?)", [username])
        return playeredits