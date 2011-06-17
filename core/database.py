import apsw, logging, traceback
from collections import deque
from threading import Thread

class Connection(Thread):
    "Creates a connenction to the database for storage."

    def __init__(self, world):
        self.logger = logging.getLogger("%s - BlockTracker" % world)
        self.run = True
        self.count = 0
        self.path = world.basename+"/storage.db"
        self.memcon = apsw.Connection(":memory:")
        self.memcursor = self.memcon.cursor()
        self.memlist = deque()
        self.worldlist = deque()
        self.worldcon = apsw.Connection("{0}".format(self.path))
        self.worldcursor = self.worldcon.cursor()
        self.worldcursor.execute("pragma journal_mode=wal")
        try:
            self.memcursor.execute("CREATE TABLE blocks (id INTEGER PRIMARY KEY, name VARCHAR(50), date DATE, before INTEGER, after INTEGER)")
            self.worldcursor.execute("CREATE TABLE blocks (id INTEGER PRIMARY KEY, name VARCHAR(50), date DATE, before INTEGER, after INTEGER)")
        except:
            pass

    def opentable(self):
        self.memcursor = None
        self.worldcursor = None
        self.memcon.backup("blocks", self.worldcon, "blocks").step()
        self.memcursor = self.memcon.cursor()
        self.worldcursor = self.worldcon.cursor()

    def close(self):
        self.memwrite()
        self.worldwrite()
        self.memcursor = None
        self.worldcursor = None
        self.run = False

    def writetable(self, blockoffset, name, date, before, after):
        if self.run:
            self.memlist.append((blockoffset, name, date, before, after))
            self.worldlist.append((blockoffset, name, date, before, after))
            if len(self.memlist) > 200:
                self.memwrite()
                self.count = self.count+1
                if self.count > 5:
                    self.worldwrite()

    def memwrite(self):
        if self.run:
            self.memcursor.executemany("INSERT OR REPLACE INTO blocks VALUES (?, ?, ?, ?, ?)", self.worldlist)
            self.memlist.clear()

    def worldwrite(self):
        if self.run:
            self.worldcursor.executemany("INSERT OR REPLACE INTO blocks VALUES (?, ?, ?, ?, ?)", self.worldlist)
            self.worldlist.clear()
            self.count = 0

    def readtable(self, entry, column):
        returncolumn = "id, name, date, before, after"
        if len(self.memlist) > 0:
            self.memwrite()
        if isinstance(entry, (int, str)):
            string = "SELECT * FROM blocks AS blocks WHERE {0} = ?".format(column)
            self.memcursor.execute(string, [entry])
            memall = self.memcursor.fetchall()
            if len(memall) == 1:
                memall = memall[0]
            return(memall)
        elif isinstance(entry, (tuple, list)):
            string = 'SELECT * from blocks AS blocks WHERE {0} IN ({1})'.format(column, ('?, '*len(entry))[:-1])
            self.memcursor.execute(string, entry)
            memall = self.memcursor.fetchall()
            return(memall)
        else:
            self.logger.error(traceback.format_exc())
            self.logger.error("ERROR - Please make sure your input is correct, dumping information...")
            self.logger.error("Entry: %s | Column: %s | Return Column: %s | String: %s" (entry, column, returncolumn, string))
            self.logger.error("Please restart the world to restart the block tracker.")
