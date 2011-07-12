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
        self.handler = McBans("3c6167438cf0183a78ddf27760ec44d84580c27c")
        
    def onlineLookup(self, data):
        client = data["client"]
        data = self.handler.lookup(client.username)
        if int(data["total"]) > 0:
            self.logger.warn("User %s has %s bans on record at MCBans!" % (client.username, data["total"]))
            client.sendServerMessage("[%sMCBans%s] You have %s%s%s bans on MCBans!" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_RED, data["total"], COLOUR_YELLOW))
        else:
            self.logger.info("User %s has no bans on record at MCBans!" % client.username)
            client.sendServerMessage("[%sMCBans%s] You have %sno%s bans on MCBans!" % (COLOUR_BLUE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_YELLOW))
        # print "Total bans: %s\n" % readable["total"]
        # if int(readable["total"]) > 0:
            # print "-- Global bans --"
            # if len(readable["global"]) > 0:
                # for element in readable["global"]:
                    # data = element.split(" .:. ")
                    # print data[0] + ": " + data[1]
            # else:
                # print "No bans"
            # print ""
            # print "-- Local bans --"
            # if len(readable["local"]) > 0:
                # for element in readable["local"]:
                    # data = element.split(" .:. ")
                    # print data[0] + ": " + data[1]
            # else:
                # print "No bans"
            # print ""
        # print "Reputation: %s/10" % readable["reputation"]
        
    name = "McBansServerPlugin"
    
    hooks = {
        "onNewPlayer": onlineLookup
    }

serverPlugin = McBansServerPlugin