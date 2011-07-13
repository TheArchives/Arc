# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.includes.mcbans_api import McBans
from ConfigParser import RawConfigParser

from arc.constants import *

class McBansServerPlugin():

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.logger.debug("[&1MCBans&f] Reading in API Key..")
        config = ConfigParser()
        try:
            config.read("config/plugins/mcbans.conf")
            api_key = config.get("mcbans", "apikey")
        except Exception as a:
            self.logger.error("[&1MCBans&f] &4Unable to find API key in config/plugins/mcbans.conf!")
            self.logger.error("[&1MCBans&f] &4%s" % a)
            self.has_api = False
        else:
            self.logger.debug("[&1MCBans&f] Found API key: &1%s&f" % api_key)
            self.has_api = True
        del config
        del ConfigParser
        self.handler = McBans(api_key)
        
    def onlineLookup(self, data):
        if self.has_api:
            client = data["client"]
            data = self.handler.lookup(client.username)
            if int(data["total"]) > 0:
                self.logger.warn("User %s has &4%s&f bans on record at MCBans and a reputation of %s/10." % (client.username, data["total"], data["reputation"]))
                client.sendServerMessage("[%sMCBans%s] You have %s%s%s bans on MCBans!" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_RED, data["total"], COLOUR_YELLOW))
            else:
                self.logger.info("User %s has &ano&f bans on record at MCBans and a reputation of %s/10." % (client.username, data["reputation"]))
                client.sendServerMessage("[%sMCBans%s] You have %sno%s bans on MCBans!" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_YELLOW))
        
    name = "McBansServerPlugin"
    
    hooks = {
        "onNewPlayer": onlineLookup
    }

serverPlugin = McBansServerPlugin