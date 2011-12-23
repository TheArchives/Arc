# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import ConfigParser

from arc.includes.mcbans_api import McBans

from arc.constants import *
from arc.decorators import *

class McBansServerPlugin():
    name = "McBansServerPlugin"

    hooks = {
        "prePlayerConnect": "connected",
        "playerQuit": "disconnected",
        "playerBanned": "banned",
        "playerUnbanned": "unbanned",
        "heartbeatSent": "callback"
    }

    commands = {
        "mcbans": "commandMCBans"
    }

    def gotServer(self):
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
                self.logger.warn("[&1MCBans&f] Unable to get the ban threshold, ignoring global ban reputations!")
                self.logger.warn("[&1MCBans&f] %s" % a)
                self.threshold = 0
            else:
                self.logger.info("[&1MCBans&f] Ban threshold is %s/10" % self.threshold)
            try:
                self.exceptions = config.options("exceptions")
            except Exception as a:
                self.logger.warn("[&1MCBans&f] Unable to get the exceptions list! Ignoring exceptions.")
                self.logger.warn("[&1MCBans&f] %s" % a)
                self.exceptions = []
            else:
                self.logger.info("[&1MCBans&f] %s exceptions loaded." % len(self.exceptions))

    def connected(self, data):
        if self.has_api:
            client = data["client"]
            data = self.handler.connect(client.username, client.transport.getPeer().host)
            try:
                error = value["error"]
            except:
                status = data["banStatus"]
                if status == u'n':
                    self.logger.info(
                        "[&1MCBans&f] User %s has a reputation of %s/10." % (client.username, data["playerRep"]))
                    client.sendServerMessage("[%sMCBans%s] You have a reputation of %s%s/10." % (
                    COLOUR_BLUE, COLOUR_YELLOW, COLOUR_GREEN, data["playerRep"]))
                else:
                    self.logger.warn("[&1MCBans&f] User %s has a reputation of %s/10 with bans on record." % (
                    client.username, data["playerRep"]))
                    client.sendServerMessage("[%sMCBans%s] Your reputation is %s%s/10%s with recorded bans." % (
                    COLOUR_BLUE, COLOUR_YELLOW, COLOUR_RED, data["playerRep"], COLOUR_YELLOW))
                    if status == u'l':
                        if client.username not in self.exceptions:
                            self.logger.info(
                                "[&1MCBans&f] Kicking user %s as they are locally banned." % client.username)
                            client.sendError("[MCBans] You are locally banned.")
                        else:
                            self.logger.info(
                                "[&1MCBans&f] User %s has a local ban but is on the exclusion list." % client.username)
                    elif status == u's':
                        if client.username not in self.exceptions:
                            self.logger.info(
                                "[&1MCBans&f] Kicking user %s as they are banned in another server in the group." % client.username)
                            client.sendError("[MCBans] You banned on another server in this group.")
                        else:
                            self.logger.info(
                                "[&1MCBans&f] User %s is banned on another server in the group but is on the exclusion list." % client.username)
                    elif status == u't':
                        if client.username not in self.exceptions:
                            self.logger.info(
                                "[&1MCBans&f] Kicking user %s as they are temporarily banned." % client.username)
                            client.sendError("[MCBans] You are temporarily banned.")
                        else:
                            self.logger.info(
                                "[&1MCBans&f] User %s has a temporary ban but is on the exclusion list." % client.username)
                    elif status == u'i':
                        if client.username not in self.exceptions:
                            self.logger.info(
                                "[&1MCBans&f] Kicking user %s as they are banned on another IP." % client.username)
                            client.sendError("[MCBans] You are IP banned.")
                        else:
                            self.logger.info(
                                "[&1MCBans&f] User %s has a ban for another IP but is on the exclusion list." % client.username)
                if int(data["playerRep"]) < self.threshold:
                    if client.username not in self.exceptions:
                        self.logger.info(
                            "[&1MCBans&1] Kicking %s because their reputation of %s/10 is below the threshold!" % (
                            client.username, data["playerRep"]))
                        client.sendError("Your MCBans reputation of %s/10 is too low!" % data["playerRep"])
                    else:
                        self.logger.info(
                            "[%sMCBans%s] %s has a reputation of %s/10 which is below the threshold, but is on the exceptions list." % (
                            client.username, data["playerRep"]))
            else:
                self.factory.logger.error("MCBans error: %s" % str(error))
            finally:
                client.reason = ""

    def disconnected(self, data):
        if self.has_api:
            value = self.handler.disconnect(data["client"].username)
        try:
            error = value["error"]
        except:
            pass
        else:
            self.factory.logger.error("MCBans error: %s" % str(error))

    def banned(self, data):
        if self.has_api:
            value = self.handler.localBan(data["username"],
                self.factory.clients[data["username"]].getPeer().host if data[
                                                                         "username"] in self.factory.clients.keys() else "Offline"
                , data["reason"], data["admin"])
            try:
                error = value["error"]
            except:
                if value["result"] != u'y':
                    self.factory.logger.warn("Unable to add %s to the MCBans local ban list!")
            else:
                self.factory.logger.error("MCBans error: %s" % str(error))

    def unbanned(self, data):
        if self.has_api:
            value = self.handler.unban(data["username"], "Local")
            try:
                error = value["error"]
            except:
                if value["result"] != u'y':
                    self.factory.logger.warn("Unable to remove %s from the MCBans local ban list!")
            else:
                self.factory.logger.error("MCBans error: %s" % str(error))

    def callback(self):
        if self.has_api:
            version = "13.37"
            maxplayers = self.factory.max_clients
            playerlist = []
            for element in self.factory.usernames.keys():
                playerlist.append(element)
            done = ",".join(playerlist)
            value = self.handler.callBack(maxplayers, done, version)
            try:
                error = value["error"]
            except:
                pass
            else:
                self.factory.logger.error("MCBans error: %s" % str(error))

    @config("category", "build")
    def commandMCBans(self, data):
        "Used to interact with the MCBans API."
        if self.has_api:
            if len(data["parts"]) < 2:
                data["client"].sendServerMessage("--- MCBans API help ---")
                data["client"].sendServerMessage("Commands list")
                data["client"].sendServerMessage("/mcbans help [command/topic]")
                data["client"].sendServerMessage("/mcbans lookup [type] [player]")
                data["client"].sendServerMessage("/mcbans unban [player]")
                data["client"].sendServerMessage("/mcbans ban [player] [type]")
                data["client"].sendServerMessage("/mcbans reason [reason]")
                data["client"].sendServerMessage("/mcbans confirm [key]")
            else:
                selection = data["parts"][1].lower()
                if selection == "help":
                    if len(data["parts"]) < 3:
                        data["client"].sendServerMessage("--- MCBans API help ---")
                        data["client"].sendSplitServerMessage("MCBans is a global ban system using a http API.")
                        data["client"].sendSplitServerMessage("There are three MCBans commands available.")
                        data["client"].sendSplitServerMessage(
                            "Admin commands in %sred%s." % (COLOUR_RED, COLOUR_YELLOW))
                        data["client"].sendServerMessage("* lookup: Looks up a player's info")
                        data["client"].sendServerMessage(
                            "* %sban%s: Bans a player on MCBans" % (COLOUR_RED, COLOUR_YELLOW))
                        data["client"].sendServerMessage(
                            "* %sunban%s: Reverses a ban on MCBans" % (COLOUR_RED, COLOUR_YELLOW))
                        data["client"].sendServerMessage(
                            "* %sreason%s: Set the ban reason for your next ban" % (COLOUR_RED, COLOUR_YELLOW))
                        data["client"].sendSplitServerMessage("Do /mcbans help command for more info.")
                    else:
                        command = data["parts"][2].lower()
                        if command == "lookup":
                            data["client"].sendSplitServerMessage("USAGE: /mcbans lookup [type] [player]")
                            data["client"].sendSplitServerMessage("This command is used to look up player info.")
                            data["client"].sendSplitServerMessage("Type may be one of the following..")
                            data["client"].sendSplitServerMessage("all: Displays all information")
                            data["client"].sendSplitServerMessage("global: Displays global bans")
                            data["client"].sendSplitServerMessage("local: Displays local bans")
                            data["client"].sendSplitServerMessage("minimal: Displays reputation and ban count")
                        elif command == "ban":
                            data["client"].sendSplitServerMessage(
                                "USAGE: /mcbans ban [player] [type] (duration) (measure)")
                            data["client"].sendSplitServerMessage("This command is used to make a ban on MCBans.")
                            data["client"].sendSplitServerMessage("Type may be one of the following..")
                            data["client"].sendSplitServerMessage("global: A global ban.")
                            data["client"].sendSplitServerMessage("- Only use this if you have conclusive proof!")
                            data["client"].sendSplitServerMessage("- This includes screenshots and /checkblock.")
                            data["client"].sendSplitServerMessage("temp: A temporary ban.")
                            data["client"].sendSplitServerMessage("- Duration is a number.")
                            data["client"].sendSplitServerMessage("- Measure can be 'm', 'h' or 'd'.")
                            data["client"].sendSplitServerMessage("Local bans are handled by /ban.")
                        elif command == "unban":
                            data["client"].sendSplitServerMessage("USAGE: /mcbans ban [player]")
                            data["client"].sendSplitServerMessage("Unbans a player from the server's MCBans entries")
                        elif command == "reason":
                            data["client"].sendSplitServerMessage("USAGE: /mcbans reason [reason]")
                            data["client"].sendSplitServerMessage("Use this to set a ban reason for your next ban.")
                            data["client"].sendSplitServerMessage("Reasons are manditory.")
                        elif command == "help":
                            data["client"].sendSplitServerMessage("USAGE: /mcbans help (topic)")
                            data["client"].sendSplitServerMessage("You're reading it, stupid.")
                        elif command == "confirm":
                            data["client"].sendSplitServerMessage("USAGE: /mcbans confirm [key]")
                            data["client"].sendSplitServerMessage("Used to confirm your mcbans.com account.")
                        else:
                            data["client"].sendSplitServerMessage("'%s' is not a help topic." % command)
                            data["client"].sendSplitServerMessage("Try /mcbans help on its own.")
                elif selection == "ban":
                    if fromloc != "user":
                        self.sendServerMessage("This command cannot be used in a command block.")
                        return
                    if self.client.isAdmin():
                        if len(data["parts"]) > 2:
                            player = data["parts"][2].lower()
                            type = data["parts"][3].lower()
                            if type == "global":
                                if not data["client"].reason is "":
                                    if player in self.client.factory.usernames.keys():
                                        client = self.client.factory.usernames[player]
                                        try:
                                            value = self.handler.globalBan(player, client.transport.getPeer().host,
                                                data["client"].reason, self.client.username)
                                        except Exception as a:
                                            data["client"].sendServerMessage("Unable to ban %s globally." % player)
                                            data["client"].sendServerMessage("Error: %s" % a)
                                        else:
                                            if value["result"] == u'y':
                                                data["client"].sendServerMessage(
                                                    "Player %s has been globally banned." % player)
                                                data["client"].sendServerMessage("Reason: %s" % data["client"].reason)
                                                client.sendError("[MCBans] Global ban: %s" % data["client"].reason)
                                                data["client"].reason = ""
                                            else:
                                                data["client"].sendServerMessage("Unable to ban %s globally." % player)
                                                data["client"].sendServerMessage("Please check MCBans for more info.")
                                    else:
                                        data["client"].sendServerMessage("Player is offline, unable to globally ban.")
                                else:
                                    data["client"].sendServerMessage("No reason set - try /mcbans help reason")
                            elif type == "temp":
                                if not data["client"].reason is "":
                                    if len(data["parts"]) > 5:
                                        duration = data["parts"][4].lower()
                                        measure = str(data["parts"][5].lower())
                                        if not (measure == "m" or measure == "h" or measure == "d"):
                                            data["client"].sendServerMessage("Measure must be m, h or d!")
                                            data["client"].sendServerMessage("See /mcbans help ban")
                                        else:
                                            try:
                                                int(duration)
                                            except Exception:
                                                data["client"].sendServerMessage("Duration must be a number!")
                                                data["client"].sendServerMessage("See /mcbans help ban")
                                            else:
                                                if player in self.client.factory.clients.keys():
                                                    ip = self.client.factory.clients[
                                                         player].transport.getPeer().host
                                                    client = self.client.factory.clients[player]
                                                else:
                                                    ip = "Offline"
                                                    client = None
                                                try:
                                                    value = self.handler.tempBan(player, ip, data["client"].reason,
                                                        self.client.username, duration, measure=measure)
                                                except Exception as a:
                                                    data["client"].sendServerMessage(
                                                        "Unable to ban %s temporarily." % player)
                                                    data["client"].sendServerMessage("Error: %s" % a)
                                                else:
                                                    if value["result"] == u'y':
                                                        data["client"].sendServerMessage(
                                                            "Player %s has been temporarily banned." % player)
                                                        data["client"].sendServerMessage("Reason: %s" % data["client"].reason)
                                                        if not client is None:
                                                            client.sendError("[MCBans] Temporary ban: %s" % reason)
                                                        data["client"].reason = ""
                                                    else:
                                                        data["client"].sendServerMessage(
                                                            "Unable to ban %s temporarily." % player)
                                                        data["client"].sendServerMessage(
                                                            "Please check MCBans for more info.")
                                    else:
                                        data["client"].sendServerMessage(
                                            "Syntax: /mcbans ban [player] [type] (duration) (measure)")
                                else:
                                    data["client"].sendServerMessage("No reason set - try /mcbans help reason")
                            elif type == "local":
                                data["client"].sendServerMessage("Local bans are handled by /ban.")
                            else:
                                data["client"].sendServerMessage("Ban type %s not recognized." % type)
                                data["client"].sendServerMessage("See /mcbans help ban")
                        else:
                            data["client"].sendServerMessage(
                                "Syntax: /mcbans ban [player] [type] (duration) (measure)")
                    else:
                        data["client"].sendServerMessage("/mcbans ban is an admin-only command!")
                elif selection == "unban":
                    if self.client.isAdmin():
                        if len(data["parts"]) > 2:
                            player = data["parts"][2].lower()
                            try:
                                value = self.handler.unban(player, self.client.username)
                            except Exception as a:
                                data["client"].sendServerMessage("Unable to unban %s." % player)
                                data["client"].sendServerMessage("Error: %s" % a)
                            else:
                                if value["result"] == u'y':
                                    data["client"].sendServerMessage("Player %s has been unbanned." % player)
                                else:
                                    data["client"].sendServerMessage("Unable to unban %s." % player)
                                    data["client"].sendServerMessage("Please check MCBans for more info.")
                        else:
                            data["client"].sendServerMessage("Syntax: /mcbans unban [player]")
                    else:
                        data["client"].sendServerMessage("/mcbans unban is an admin-only command!")
                elif selection == "reason":
                    if self.client.isAdmin():
                        if len(data["parts"]) > 2:
                            reason = data["parts"][2]
                            data["client"].reason = reason
                            data["client"].sendServerMessage("Set reason: %s" % reason)
                        else:
                            data["client"].reason = ""
                            data["client"].sendServerMessage("Unset reason.")
                    else:
                        data["client"].sendServerMessage("/mcbans reason is an admin-only command!")
                elif selection == "lookup":
                    if len(data["parts"]) is 4:
                        type = data["parts"][2].lower()
                        player = data["parts"][3].lower()
                        try:
                            data = self.handler.lookup(player, self.client.username)
                        except Exception as a:
                            data["client"].sendServerMessage("Unable to look up %s!" % player)
                            data["client"].sendServerMessage("Error: %s" % a)
                        else:
                            if type == "all": # all/global/local/minimal
                                data["client"].sendServerMessage("Information on %s" % player)
                                data["client"].sendServerMessage("Reputation: %.2f/10" % data["reputation"])
                                data["client"].sendServerMessage("Total bans: %s" % data["total"])
                                if len(data["local"]) > 0:
                                    data["client"].sendServerMessage("--- LOCAL BANS ---")
                                    for element in data["local"]:
                                        server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                        reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                        data["client"].sendServerMessage("%s: %s" % (server, reason))
                                else:
                                    data["client"].sendServerMessage("No local bans.")
                                if len(data["global"]) > 0:
                                    data["client"].sendServerMessage("--- GLOBAL BANS ---")
                                    for element in data["global"]:
                                        server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                        reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                        data["client"].sendServerMessage("%s: %s" % (server, reason))
                                else:
                                    data["client"].sendServerMessage("No global bans.")
                            elif type == "global":
                                data["client"].sendServerMessage("Information on %s" % player)
                                if len(data["global"]) > 0:
                                    data["client"].sendServerMessage("--- GLOBAL BANS ---")
                                    for element in data["global"]:
                                        server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                        reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                        data["client"].sendServerMessage("%s: %s" % (server, reason))
                                else:
                                    data["client"].sendServerMessage("No global bans.")
                            elif type == "local":
                                data["client"].sendServerMessage("Information on %s" % player)
                                if len(data["local"]) > 0:
                                    data["client"].sendServerMessage("--- LOCAL BANS ---")
                                    for element in data["local"]:
                                        server = element.split(" .:. ")[0].encode("ascii", "ignore")
                                        reason = element.split(" .:. ")[1].encode("ascii", "ignore")
                                        data["client"].sendServerMessage("%s: %s" % (server, reason))
                                else:
                                    data["client"].sendServerMessage("No local bans.")
                            elif type == "minimal":
                                data["client"].sendServerMessage("Information on %s" % player)
                                data["client"].sendServerMessage("Reputation: %.2f/10" % data["reputation"])
                                data["client"].sendServerMessage("Total bans: %s" % data["total"])
                            else:
                                data["client"].sendServerMessage("Type %s not reconized." % type)
                                data["client"].sendServerMessage("See /mcbans help lookup")
                    else:
                        data["client"].sendServerMessage("Syntax: /mcbans lookup [type] [player]")
                elif selection == "confirm":
                    if fromloc != "user":
                        data["client"].sendServerMessage("This command cannot be used in a command block.")
                        return
                    if len(data["parts"]) > 2:
                        key = data["parts"][2]
                        data = self.handler.confirm(self.client.username, key)
                        if data["result"] == u'y':
                            data["client"].sendServerMessage("Account confirmed. Welcome to MCBans!")
                        else:
                            data["client"].sendServerMessage("Unable to confirm account!")
                            data["client"].sendServerMessage("Check your confirmation key.")
                    else:
                        data["client"].sendServerMessage("Syntax: /mcbans confirm [key]")
                else:
                    data["client"].sendSplitServerMessage("'%s' is not an MCBans command." % data["parts"][1])
                    data["client"].sendSplitServerMessage("Try /mcbans help on its own.")
        else:
            data["client"].sendSplitServerMessage("No MCBans API key found! This command has therefore been disabled.")

serverPlugin = McBansServerPlugin