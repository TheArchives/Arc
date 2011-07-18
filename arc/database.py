# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

class DBLayer(object):
    """ The database layer for communications between the server and the MySQL database. """
    def __init__(self, factory, buffersize=500):
        """ Set up database pool, buffers, and other preperations """
        self.factory = factory
        self.database = adbapi.ConnectionPool('MySQLdb', self.factory.mysql["host"], self.factory.mysql["user"], self.factory.mysql["pass"], self.factory.mysql["db"], self.factory.mysql["port"], charse="utf-8", cp_min=1, cp_max=1, check_same_thread=False)
        self.databuffer = list()
        self.buffersize = buffersize
        self.run = True
        #TODO - Pragma statements

    def add(self, data):
        """ Adds data to the tracker.
        NOTE the format for a single data entry is this -
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
        cursor.executemany("insert or replace into history values (?,?,?,?,?)", dbbuffer)
        return None