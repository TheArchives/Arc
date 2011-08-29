# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from os import getcwd, path

from twisted.enterprise import adbapi

# Stealing the tracker for now :P
# This will need to be rewritten soon to work with MySQL.

# Status ID variables
STATUS_UNREAD = 0
STATUS_READ = 1
STATUS_DELETED = 2

class InboxDatabase(object):
    """ Provides facilities for inbox accessing storage. """
    def __init__(self, buffersize=500, directory=getcwd()):
        """ Set up database pool, buffers, and other preperations """
        self.database = adbapi.ConnectionPool('sqlite3', path.join("config", "data", "inbox.db"), check_same_thread=False)
        try:
            self.d = self.database.runOperation("CREATE TABLE inbox (id INTEGER unsigned AUTO_INCREMENT,\
                from VARCHAR(255), to VARCHAR(255), message TEXT, date DATE, status INTEGER)")
        except:
            i = 1
        finally:
            self.run = True
        #TODO - Pragma statements

    def add(self, data):
        """ Adds data to the database.
        NOTE the format for a single data entry is this -
        (id, from, to, message, date, status) where id and status should not be entered"""
        self.database.runQuery("INSERT OR REPLACE INTO inbox (from, to, message, date, status) VALUES (?,?,?,?,0)", data)

    def close(self):
        """ Flushes and closes the database """
        self.database.close()

    def getmessages_to(self, player):
        """ Gets the player's message """
        self._flush()
        messages = self.database.runQuery("SELECT ALL FROM inbox WHERE to = (?)", player)
        return messages

    def getmessages_to(self, player):
        """ Gets the messages sent by the player """
        self._flush()
        messages = self.database.runQuery("SELECT ALL FROM inbox WHERE from = (?)", player)
        return messages

class OfflineMessageServerPlugin(object):
    """
    A plugin used for loading inbox messages.
    """

    name = "OfflineMessagePlugin"

    def gotServer(self):
        self.database = InboxDatabase()

    def getMessages(self, user, way):
        """
        Gets the current messages to see if there is a message for the user.
        Returns a list of entries.
        """
        if way not in ["from", "to"]:
            raise ValueError("Value of way must be from or to")
        else:
            if way == "to":
                result = self.database.getmessages_to(user)
            elif way == "from":
                result = self.database.getmessages_from(user)
            return result

    def checkMessages(self, user):
        """ Checks the messages database to see if user received a message. """
        if self.database.getmessages_to(user):
            return True
        else:
            return False

    def sendMessage(self, from_user, to_user, message):
        """ Sends a message to to_user. """
        if to_user in self.factory.usernames:
            self.factory.usernames[to_user].sendServerMessage("You have a new message waiting in your inbox.")
            self.factory.usernames[to_user].sendServerMessage("Use /inbox to check and see.")

    def numMessages(self, user, way):
        """ Returns the number of messages the player sent/has """
        if way not in ["from", "to"]:
            raise ValueError("Value of way must be from or to")
        else:
            if way == "to":
                result = self.database.rowcount(self.database.getmessages_to(user))
            elif way == "from":
                result = self.database.rowcount(self.database.getmessages_from(user))
            return result

#    def setStatus(self, mid, status):
#        """ Set the status of a message. """
#        if status in [STATUS_UNREAD, STATUS_READ, STATUS_DELETED]:


#    def MessageAlert(self):
#        if os.path.exists("config/data/inbox.dat"):
#            self.messages = self.factory.messages
#            for client in self.factory.clients.values():
#                if client.username in self.messages:
#                    client.sendServerMessage("You have a message waiting in your Inbox.")
#                    client.sendServerMessage("Use /inbox to check and see.")
#                    reactor.callLater(300, self.MessageAlert)

    hooks = {
        }

serverPlugin = OfflineMessageServerPlugin