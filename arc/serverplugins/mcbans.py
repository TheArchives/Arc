# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.includes.mcbans_api import McBans
import ConfigParser

from arc.constants import *

class McBansServerPlugin():

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.logger.debug("[&1MCBans&f] Reading in API Key..")
        config = ConfigParser.RawConfigParser()
        try:
            config.read("config/plugins/mcbans.conf")
            api_key = config.get("mcbans", "apikey")
        except Exception as a:
            self.logger.error("[&1MCBans&f] &4Unable to find API key in config/plugins/mcbans.conf!")
            self.logger.error("[&1MCBans&f] &4%s" % a)
            self.has_api = False
        else:
            self.logger.debug("[&1MCBans&f] Found API key: &1%s&f" % api_key)
            self.logger.info("[&1MCBans&f] MCBans enabled!")
            self.handler = McBans(api_key)
            self.has_api = True
        try:
            self.threshold = config.getint("mcbans", "ban_threshold")
        except Exception as a:
            self.logger.error("[&1MCBans&f] Unable to get the ban threshold, ignoring global ban reputations!")
            self.logger.error("[&1MCBans&f] %s" % a)
            self.threshold = 0
        else:
            self.logger.info("[&1MCBans&f] Ban threshold is %s/10" % self.threshold) 
        self.exceptions = config.options("exceptions")
        del config
        
    def onlineLookup(self, data):
        if self.has_api:
            client = data["client"]
            data = self.handler.lookup(client.username)
            if int(data["total"]) > 0:
                self.logger.warn("User %s has &4%s&f bans on record at MCBans and a reputation of %s/10." % (client.username, data["total"], data["reputation"]))
                client.sendServerMessage("[%sMCBans%s] You have %s%s%s bans on MCBans and a reputation of %s/10" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_RED, data["total"], COLOUR_YELLOW, data["reputation"]))
            else:
                self.logger.info("User %s has &ano&f bans on record at MCBans and a reputation of %s/10." % (client.username, data["reputation"]))
                client.sendServerMessage("[%sMCBans%s] You have %sno%s bans on MCBans!" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_YELLOW))
            if int(data["reputation"]) < self.threshold:
                if client.username not in self.exceptions:
                    self.logger.info("[%sMCBans%s] Kicking %s because their reputation of %s/10 is below the threshold!" % (client.username, data["reputation"]))
                    client.sendError("Your MCBans reputation of %s/10 is too low!" % data["reputation"])
                else:
                    self.logger.info("[%sMCBans%s] %s has a reputation of %s/10 which is below the threshold, but is on the exceptions list." % (client.username, data["reputation"]))
                
        
    name = "McBansServerPlugin"
    
    hooks = {
        "onNewPlayer": onlineLookup
    }

serverPlugin = McBansServerPlugin