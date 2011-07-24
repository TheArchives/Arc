# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import time

from twisted.internet import reactor
from arc.includes.mcbans_api import McBans

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class McBansPlugin(ProtocolPlugin):

    commands = {
        "mcbans": "commandMCBans"
    }

    def gotClient(self):
        self.reason = ""

    @config("category", "build")
    def commandMCBans(self, parts, fromloc, overriderank):
        "/mcbans [command] - Guest\nUsed to interact with the MCBans API."
        if self.client.factory.serverPluginExists("McBansServerPlugin"):
            handler = self.client.factory.serverPlugins["McBansServerPlugin"].handler
            if self.client.factory.serverPlugins["McBansServerPlugin"].has_api:
                if len(parts) < 2:
                    self.client.sendServerMessage("--- MCBans API help ---")
                    self.client.sendServerMessage("Commands list")
                    self.client.sendServerMessage("/mcbans help [command/topic]")
                    self.client.sendServerMessage("/mcbans lookup [type] [player]")
                    self.client.sendServerMessage("/mcbans unban [player]")
                    self.client.sendServerMessage("/mcbans ban [player] [type]")
                    self.client.sendServerMessage("/mcbans reason [reason]")
                    self.client.sendServerMessage("/mcbans confirm [key]")
                else:
                    selection = parts[1].lower()
                    if selection == "help":
                        if len(parts) < 3:
                            self.client.sendServerMessage("--- MCBans API help ---")
                            self.client.sendSplitServerMessage("MCBans is a global ban system using a http API.")
                            self.client.sendSplitServerMessage("There are three MCBans commands available.")
                            self.client.sendSplitServerMessage("Admin commands in %sred%s." % (COLOUR_RED, COLOUR_YELLOW))
                            self.client.sendServerMessage("* lookup: Looks up a player's info")
                            self.client.sendServerMessage("* %sban%s: Bans a player on MCBans" % (COLOUR_RED, COLOUR_YELLOW))
                            self.client.sendServerMessage("* %sunban%s: Reverses a ban on MCBans" % (COLOUR_RED, COLOUR_YELLOW))
                            self.client.sendServerMessage("* %sreason%s: Set the ban reason for your next ban" % (COLOUR_RED, COLOUR_YELLOW))
                            self.client.sendSplitServerMessage("Do /mcbans help command for more info.")
                        else:
                            command = parts[2].lower()
                            if command == "lookup":
                                self.client.sendSplitServerMessage("USAGE: /mcbans lookup [type] [player]")
                                self.client.sendSplitServerMessage("This command is used to look up player info.")
                                self.client.sendSplitServerMessage("Type may be one of the following..")
                                self.client.sendSplitServerMessage("all: Displays all information")
                                self.client.sendSplitServerMessage("global: Displays global bans")
                                self.client.sendSplitServerMessage("local: Displays local bans")
                                self.client.sendSplitServerMessage("minimal: Displays reputation and ban count")
                            elif command == "ban":
                                self.client.sendSplitServerMessage("USAGE: /mcbans ban [player] [type] (duration) (measure)")
                                self.client.sendSplitServerMessage("This command is used to make a ban on MCBans.")
                                self.client.sendSplitServerMessage("Type may be one of the following..")
                                self.client.sendSplitServerMessage("global: A global ban.")
                                self.client.sendSplitServerMessage("- Only use this if you have conclusive proof!")
                                self.client.sendSplitServerMessage("- This includes screenshots and /checkblock.")
                                self.client.sendSplitServerMessage("temp: A temporary ban.")
                                self.client.sendSplitServerMessage("- Duration is a number.")
                                self.client.sendSplitServerMessage("- Measure can be 'm', 'h' or 'd'.")
                                self.client.sendSplitServerMessage("Local bans are handled by /ban.")
                            elif command == "unban":
                                self.client.sendSplitServerMessage("USAGE: /mcbans ban [player]")
                                self.client.sendSplitServerMessage("Unbans a player from the server's MCBans entries")
                            elif command == "reason":
                                self.client.sendSplitServerMessage("USAGE: /mcbans reason [reason]")
                                self.client.sendSplitServerMessage("Use this to set a ban reason for your next ban.")
                                self.client.sendSplitServerMessage("Reasons are manditory.")
                            elif command == "help":
                                self.client.sendSplitServerMessage("USAGE: /mcbans help (topic)")
                                self.client.sendSplitServerMessage("You're reading it, stupid.")
                            elif command == "confirm":
                                self.client.sendSplitServerMessage("USAGE: /mcbans confirm [key]")
                                self.client.sendSplitServerMessage("Used to confirm your mcbans.com account.")
                            else:
                                self.client.sendSplitServerMessage("'%s' is not a help topic." % command)
                                self.client.sendSplitServerMessage("Try /mcbans help on its own.")
                    elif selection == "ban":
                        if self.client.isAdmin():
                            if len(parts) > 2:
                                player = parts[2].lower()
                                type = parts[3].lower()
                                if type == "global":
                                    if not self.reason is "":
                                        if player in self.client.factory.usernames.keys():
                                            client = self.client.factory.usernames[player]
                                            try:
                                                value = handler.globalBan(player, client.transport.getPeer().host, self.reason, self.client.username)
                                            except Exception as a:
                                                self.client.sendServerMessage("Unable to ban %s globally." % player)
                                                self.client.sendServerMessage("Error: %s" % a)
                                            else:
                                                if value["result"] == u'y':
                                                    self.client.sendServerMessage("Player %s has been globally banned." % player)
                                                    self.client.sendServerMessage("Reason: %s" % self.reason)
                                                    client.sendError("[MCBans] Global ban: %s" % reason)
                                                    self.reason = ""
                                                else:
                                                    self.client.sendServerMessage("Unable to ban %s globally." % player)
                                                    self.client.sendServerMessage("Please check MCBans for more info.")
                                        else:
                                            self.client.sendServerMessage("Player is offline, unable to globally ban.")
                                    else:
                                        self.client.sendServerMessage("No reason set - try /mcbans help reason")
                                elif type == "temp":
                                    if not self.reason is "":
                                        if len(parts) > 5:
                                            duration = parts[4].lower()
                                            measure = str(parts[5].lower())
                                            if not (measure == "m" or measure == "h" or measure == "d"):
                                                self.client.sendServerMessage("Measure must be m, h or d!")
                                                self.client.sendServerMessage("See /mcbans help ban")
                                            else:
                                                try:
                                                    int(duration)
                                                except Exception:
                                                    self.client.sendServerMessage("Duration must be a number!")
                                                    self.client.sendServerMessage("See /mcbans help ban")
                                                else:
                                                    if player in self.client.factory.clients.keys():
                                                        ip = self.client.factory.clients[player].transport.getPeer().host
                                                        client = self.client.factory.clients[player]
                                                    else:
                                                        ip = "Offline"
                                                        client = None
                                                    try:
                                                        value = handler.tempBan(player, ip, self.reason, self.client.username, duration, measure=measure)
                                                    except Exception as a:
                                                        self.client.sendServerMessage("Unable to ban %s temporarily." % player)
                                                        self.client.sendServerMessage("Error: %s" % a)
                                                    else:
                                                        if value["result"] == u'y':
                                                            self.client.sendServerMessage("Player %s has been temporarily banned." % player)
                                                            self.client.sendServerMessage("Reason: %s" % self.reason)
                                                            if not client is None:
                                                                client.sendError("[MCBans] Temporary ban: %s" % reason)
                                                            self.reason = ""
                                                        else:
                                                            self.client.sendServerMessage("Unable to ban %s temporarily." % player)
                                                            self.client.sendServerMessage("Please check MCBans for more info.")
                                        else:
                                            self.client.sendServerMessage("Syntax: /mcbans ban [player] [type] (duration) (measure)")
                                    else:
                                        self.client.sendServerMessage("No reason set - try /mcbans help reason")
                                elif type == "local":
                                    self.client.sendServerMessage("Local bans are handled by /ban.")
                                else:
                                    self.client.sendServerMessage("Ban type %s not recognized." % type)
                                    self.client.sendServerMessage("See /mcbans help ban")
                            else:
                                self.client.sendServerMessage("Syntax: /mcbans ban [player] [type] (duration) (measure)")
                        else:
                            self.client.sendServerMessage("/mcbans ban is an admin-only command!")
                    elif selection == "unban":
                        if self.client.isAdmin():
                            if len(parts) > 2:
                                player = parts[2].lower()
                                try:
                                    value = handler.unban(player, self.client.username)
                                except Exception as a:
                                    self.client.sendServerMessage("Unable to unban %s." % player)
                                    self.client.sendServerMessage("Error: %s" % a)
                                else:
                                    if value["result"] == u'y':
                                        self.client.sendServerMessage("Player %s has been unbanned." % player)
                                    else:
                                        self.client.sendServerMessage("Unable to unban %s." % player)
                                        self.client.sendServerMessage("Please check MCBans for more info.")
                            else:
                                self.client.sendServerMessage("Syntax: /mcbans unban [player]")
                        else:
                            self.client.sendServerMessage("/mcbans unban is an admin-only command!")
                    elif selection == "reason":
                        if self.client.isAdmin():
                            if len(parts) > 2:
                                reason = parts[2]
                                self.reason = reason
                                self.client.sendServerMessage("Set reason: %s" % reason)
                            else:
                                self.reason = ""
                                self.client.sendServerMessage("Unset reason.")
                        else:
                            self.client.sendServerMessage("/mcbans reason is an admin-only command!")
                    elif selection == "lookup":
                        if len(parts) is 4:
                            type = parts[2].lower()
                            player = parts[3].lower()
                            try:
                                data = handler.lookup(player, self.client.username)
                            except Exception as a:
                                self.client.sendServerMessage("Unable to look up %s!" % player)
                                self.client.sendServerMessage("Error: %s" % a)
                            else:
                                if type == "all": # all/global/local/minimal
                                    self.client.sendServerMessage("Information on %s" % player)
                                    self.client.sendServerMessage("Reputation: %.2f/10" % data["reputation"])
                                    self.client.sendServerMessage("Total bans: %s" % data["total"])
                                    if len(data["local"]) > 0:
                                        self.client.sendServerMessage("--- LOCAL BANS ---")
                                        for element in data["local"]:
                                            server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                            reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                            self.client.sendServerMessage("%s: %s" % (server, reason))
                                    else:
                                        self.client.sendServerMessage("No local bans.")
                                    if len(data["global"]) > 0:
                                        self.client.sendServerMessage("--- GLOBAL BANS ---")
                                        for element in data["global"]:
                                            server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                            reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                            self.client.sendServerMessage("%s: %s" % (server, reason))
                                    else:
                                        self.client.sendServerMessage("No global bans.")
                                elif type == "global":
                                    self.client.sendServerMessage("Information on %s" % player)
                                    if len(data["global"]) > 0:
                                        self.client.sendServerMessage("--- GLOBAL BANS ---")
                                        for element in data["global"]:
                                            server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                            reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                            self.client.sendServerMessage("%s: %s" % (server, reason))
                                    else:
                                        self.client.sendServerMessage("No global bans.")
                                elif type == "local":
                                    self.client.sendServerMessage("Information on %s" % player)
                                    if len(data["local"]) > 0:
                                        self.client.sendServerMessage("--- LOCAL BANS ---")
                                        for element in data["local"]:
                                            server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                            reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                            self.client.sendServerMessage("%s: %s" % (server, reason))
                                    else:
                                        self.client.sendServerMessage("No local bans.")
                                elif type == "minimal":
                                    self.client.sendServerMessage("Information on %s" % player)
                                    self.client.sendServerMessage("Reputation: %.2f/10" % data["reputation"])
                                    self.client.sendServerMessage("Total bans: %s" % data["total"])
                                else:
                                    self.client.sendServerMessage("Type %s not reconized." % type)
                                    self.client.sendServerMessage("See /mcbans help lookup")
                        else:
                            self.client.sendServerMessage("Syntax: /mcbans lookup [type] [player]")
                    elif selection == "confirm":
                        if len(parts) > 2:
                            key = parts[2]
                            data = handler.confirm(self.client.username, key)
                            if data["result"] == u'y':
                                self.client.sendServerMessage("Account confirmed. Welcome to MCBans!")
                            else:
                                self.client.sendServerMessage("Unable to confirm account!")
                                self.client.sendServerMessage("Check your confirmation key.")
                        else:
                            self.client.sendServerMessage("Syntax: /mcbans confirm [key]")
                    else:
                        self.client.sendSplitServerMessage("'%s' is not an MCBans command." % parts[1])
                        self.client.sendSplitServerMessage("Try /mcbans help on its own.")
            else:
                self.client.sendSplitServerMessage("No MCBans API key found! \
            This command has therefore been disabled.")
        else:
            self.client.sendSplitServerMessage("The MCBans server plugin is not loaded. \
            This command has therefore been disabled.")