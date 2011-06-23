# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os, shutil, sys
from ConfigParser import RawConfigParser as ConfigParser

debug = (True if "--debug" in sys.argv else False)

class PlayerData(object):
    def __init__(self, client):
        "Initialises the class with the client's username."
        if isinstance(client, object):
            self.logger = client.factory.logger # Get ourselves a logger
            self.offline = False
        else: # Offline
            self.logger = ColouredLogger(debug)
            self.offline = True
        # We're going to take a few things from the client, so we'll save it.
        self.client = client
        # What is our username?
        self.username = (self.client.username if not self.offline else self.client)
        # Create a RawConfigParser instance and data dict
        self.dataReader = ConfigParser()
        self.data = {}
        # Obviously, we need to load the data right away.
        success = True
        if not self.offline:
            success = self.loadData()
        if (not success) or self.offline:
            self.loadDataFallback() # If it failed, fall back.
        else:
            self.saving = True

    def __str__(self):
        if not offline:
            return self.client.username # Or the client object?
        else:
            return self.client

    # Enables use of context manager (e.g: with PlayerData(username) as pd:) so it works offline too

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.flush()

    def loadData(self):
        "Loads the player's data file"
        if os.path.isfile("data/players/%s.ini" % self.username): # Check if the file exists ( Much more efficient than x in os.listdir() )
            try:
                self.dataReader.read("data/players/%s.ini" % self.username) # Have ConfigParser read it
            except Exception as e: # If we can't read it, say that
                self.logger.error("Unable to read player data for %s!" % self.username)
                self.logger.error("Error: %s" % e)
                return False # Return false to show it failed
            else:
                self.logger.debug("Parsing data/players/%s.ini" % self.username)
        else: # If we have no file, copy it from the template
            self.logger.debug("No player data file for %s found." % self.username)
            self.logger.info("Creating data file data/players/%s.ini using template data/DEFAULT_TEMPLATE_PLAYER.ini" % self.username)
            shutil.copy("data/DEFAULT_TEMPLATE_PLAYER.ini", "data/players/%s.ini" % self.username)
            try:
                self.dataReader.read("data/players/%s.ini" % self.username) # Have ConfigParser read it
            except Exception as e: # If we can't read it, say that
                self.logger.error("Unable to read player data for %s!" % self.username)
                self.logger.error("Error: %s" % e)
                return False
        sections = self.dataReader.sections()
        try:
            for element in sections:
                data = self.dataReader.items(element) # This gives us name, value pairs for the secion
                self.data[element] = {}
                for part in data:
                    name, value = part
                    self.data[element][name] = value
            self.logger.debug("Player data dictionary:")
            self.logger.debug(str(self.data))
        except Exception as e:
            self.logger.error("Unable to read player data for %s!" % self.username)
            self.logger.error("Error: %s" % e)
            return False
        self.logger.info("Parsed data file for %s." % self.username)
        return True

    def loadDataFallback(self):
        "Called when loading data fails. Prevents data saving and loads the default data values."
        self.factory.logger.warn("Settings will not be saved. Default data being used.")
        self.dataReader.read("data/DEFAULT_TEMPLATE_PLAYER.ini")
        sections = self.dataReader.sections()
        try:
            for element in sections:
                data = self.dataReader.items(element) # This gives us named items for the secion
                self.data[element] = {}
                for part in data:
                    name, value = part # This gives us name, value pairs from the named items in the section
                    self.data[element][name] = value
            self.logger.debug("Player data dictionary:")
            self.logger.debug(str(self.data))
        except Exception as e:
            self.logger.error("Unable to read default player data for %s!" % self.username)
            self.logger.error("Error: %s" % e)
            return False
        self.logger.info("Parsed default data file for %s." % self.username)
        self.saving = False
        return True

    def saveData(self, username=None):
        "Saves the player's data file, possibly cloning it to another player"
        if self.saving:
            if username is None:
                username = self.username
            self.logger.debug("Saving data/players/%s.ini..." % username)
            try:
                fp = open("data/players/%s.ini" % username, "w")
            except Exception as e:
                self.logger.error("Unable to open data/players/%s.ini for writing!" % username)
                self.logger.error("Error: %s" % e)
            else:
                for section in self.data.keys():
                    if not self.dataReader.has_section(section):
                        self.dataReader.add_section(section)
                    for element in section.items():
                        self.dataReader.set(section, element[0], str(element[1]))
                try:
                    self.dataReader.write(fp)
                    fp.flush()
                    fp.close()
                except Exception as e:
                    self.logger.error("Unable to write to data/players/%s.ini!" % username)
                    self.logger.error("Error: %s" % e)
                else:
                    self.logger.debug("Saved data/players/%s.ini successfully." % username)
        else:
            self.logger.warn("Unable to write player data for %s as it was unreadable." % username)
            self.logger.warn("Check the log for when they joined for more information.")

    # Convenience functions
    # These are here so that plugin authors can get and set data to the internal
    # data dict without interfering with it.

    def get(self, section, name, default=None):
        try:
            ret = self.data[section][name]
        except:
            if default is not None:
                self.data[section][name] = default
                ret = default
            else:
                ret = ""
        return ret

    def string(self, section, name, default=None):
        try:
            ret = self.data[section][name]
        except:
            if default is not None:
                self.data[section][name] = default
                ret = default
            else:
                ret = ""
        return ret

    def int(self, section, name, default=None):
        try:
            ret = self.data[section][name]
        except:
            if default is not None:
                self.data[section][name] = default
                ret = default
            else:
                ret = 0
        return ret

    def bool(self, section, name, default=None):
        try:
            ret = self.data[section][name]
        except:
            if default is not None:
                self.data[section][name] = default
                ret = default
            else:
                ret = False
        return ret

    def set(self, section, name, value):
        try:
            self.data[section][name] = value
        except Exception as e:
            self.logger.error("Error setting %s in section %s to %s!" % (name, section, str(value)))
            self.logger.error("Error: %s" % e)
            return False
        else:
            return True

    def flush(self):
        "Saves the current data structure."
        self.saveData()

    def reload(self):
        "Discards the current data structure and reparses it."
        del self.data
        self.loadData()

    # Properties (self.blah)
    # These are here so that plugin authors can get at the class' data variables
    # properly.

    @property
    def username(self):
        "Associated client's username"
        if not self.offline:
            return self.client.username
        else:
            return self.client

    @property
    def canSave(self):
        "Check to see if we can save or not"
        return self.saving

    @property
    def isOffline(self):
        "Check to see if we are in offline mode (no protocol object available)"
        return self.offline

class ClanData(object):
    pass