# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os, shutil
from ConfigParser import RawConfigParser as ConfigParser

class PlayerData():
    def __init__(self, client):
        "Initialises the class with the client's protocol object."
        self.logger = client.factory.logger # Get ourselves a logger
        # We're going to take a few things from the client, so we'll save it.
        self.client = client
        # Create a RawConfigParser instance and data dict
        self.dataReader = ConfigParser()
        self.data = {}
        # Obviously, we need to load the data right away.
        success = self.loadData()
        if not success:
            self.loadDataFallback() # If it failed, fall back.

    @property
    def username(self):
        return self.client.username

    def loadData(self):
        "Loads the player's data file"
        if os.path.isfile("data/players/%s.ini" % self.username): # Check if the file exists ( Much more efficient than x in os.listdir() )
            try:
                self.dataReader.read("data/players/%s.ini" % self.username) # Have ConfigParser read it
            except Exception as a: # If we can't read it, say that
                self.logger.error("Unable to read player data for %s!" % self.username)
                self.logger.error("Error: %s" % a)
                return False # Return false to show it failed
            else:
                self.logger.debug("Parsing data/players/%s.ini" % self.username)
        else: # If we have no file, copy it from the template
            self.logger.debug("No player data file for %s found." % self.username)
            self.logger.info("Creating data file data/players/%s.ini using template data/DEFAULT_TEMPLATE_PLAYER.ini" % self.username)
            shutil.copy("data/DEFAULT_TEMPLATE_PLAYER.ini", "data/players/%s.ini" % self.username)
            try:
                self.dataReader.read("data/players/%s.ini" % self.username) # Have ConfigParser read it
            except Exception as a: # If we can't read it, say that
                self.logger.error("Unable to read player data for %s!" % self.username)
                self.logger.error("Error: %s" % a)
                return False
        try:
            sections = self.dataReader.options("sections")
        except Exception as a:
            self.logger.error("Unable to read section header for /data/players/%s.ini!" % self.username)
            self.logger.error("Error: %s" % a)
            self.loadDataFallback()
            return False
        try:
            for element in sections:
                data = self.dataReader.items(element) # This gives us name, value pairs for the secion
                self.data[element] = {}
                for part in data:
                    name, value = part
                    self.data[element][name] = value
            self.logger.debug("Player data dictionary:")
            self.logger.debug(str(self.data))
        except Exception as a:
            self.logger.error("Unable to read player data for %s!" % self.username)
            self.logger.error("Error: %s" % a)
            return False
        self.logger.info("Parsed data file for %s." % self.username)
        return True

    def loadDataFallback(self):
        "Called when loading data fails. Prevents data saving and loads the default data values."
        self.factory.logger.warn("Settings will not be saved.")

    def saveData(self):
        "Saves the player's data file"
        pass # Derpishly, this does nothing yet. Derp derp.

class ClanData():
    pass