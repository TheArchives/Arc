# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import hashlib, socket

from arc.decorators import *
from arc.constants import *
from arc.globals import *
from arc.plugins import ProtocolPlugin

class helpPlugin(ProtocolPlugin):

    commands = {
        "help": "commandHelp",
        "?": "commandHelp",
        "cmdlist": "commandCmdlist",
        "commands": "commandCmdlist",
        "about": "commandAbout",
        "info": "commandAbout",
        "credits": "commandCredits",
        "motd": "commandMOTD",
        "greeting": "commandMOTD",
        "rules": "commandRules",

        "staff": "commandStaff",
        "helpers": "commandHelpers",
        "directors": "commandDirectors",
        "admins": "commandAdmins",
        "mods": "commandMods",

        "dcurl": "commandDCURL",
        "womurl": "commandDCURL",
    }

    @config("category", "info")
    def commandHelp(self, parts, fromloc, overriderank):
        "/help [document/command] - Guest\nHelp for this server and commands."
        if len(parts) > 1:
            try:
                func = self.client.commands[parts[1].lower()]
            except KeyError:
                if parts[1].lower() == "chats":
                    self.client.sendServerMessage("Help; Chats")
                    self.client.sendServerMessage("Whispers: @username Whispers")
                    self.client.sendServerMessage("WorldChat: !message")
                    if self.client.isMod():
                        self.client.sendServerMessage("StaffChat: #message")
                elif parts[1].lower() == "physic":
                    self.client.sendServerMessage("Help; Physics Engine")
                    self.client.sendServerMessage("Turn physics on to use Physics (max of 5 worlds)")
                    self.client.sendServerMessage("If fwater is on then your water won't move.")
                    self.client.sendServerMessage("Orange blocks make Lavafalls, darkblue blocks make Waterfalls.")
                    self.client.sendServerMessage("Spouts need fwater to be on in order to work.")
                    self.client.sendServerMessage("Sand will fall, grass will grow, sponges will absorb.")
                    self.client.sendServerMessage("Use unflood to move all water, lava, and spouts from the world.")
                elif parts[1].lower() == "ranks":
                    self.client.sendNormalMessage(COLOUR_YELLOW+"Help: Server Ranks - "+COLOUR_DARKGREEN+
                                                 "Owner/Console [9] "+COLOUR_GREEN+"Director [8] "+COLOUR_RED+"Admin [7] "+COLOUR_BLUE+"Mod [6] "
                                                 +COLOUR_DARKBLUE+"Helper [5] "+COLOUR_DARKYELLOW+"World Owner [4] "+COLOUR_DARKCYAN+"Op [3] "+COLOUR_CYAN+"Builder [2] "
                                                 +COLOUR_WHITE+"Guest [1] "+COLOUR_BLACK+"Spec/Banned [0]")
                elif parts[1].lower() == "cc":
                    self.client.sendServerMessage("Help; Color Codes")
                    self.client.sendNormalMessage("&a%a &b%b &c%c &d%d &e%e &f%f")
                    self.client.sendNormalMessage("&0%0 &1%1 &2%2 &3%3 &4%4 &5%5 &6%6 &7%7 &8%8 &9%9")
                elif parts[1].lower() == "guide":
                    self.client.sendServerMessage("Help; The Guide")
                    self.client.sendServerMessage("/command required [optional]")
                    self.client.sendServerMessage("command - the command you're using (like /help)")
                    self.client.sendServerMessage("required - this stuff is required after the command")
                    self.client.sendServerMessage("optional - this stuff isn't needed, like blb coords")
                    self.client.sendServerMessage("Example: /help [document/command]")
                    self.client.sendServerMessage("You can do /help only or optionally input more.")
                else:
                    self.client.sendServerMessage("Unknown command '%s'" % parts[1])
            else:
                if func.__doc__:
                    for line in func.__doc__.split("\n"):
                        self.client.sendServerMessage(line)
                else:
                    self.client.sendServerMessage("There's no help for that command.")
        else:
            self.client.sendServerMessage("The Central Help Hub")
            self.client.sendServerMessage("Documents: /help [cc|chats|guide|physic|ranks]")
            self.client.sendServerMessage("Commands: /cmdlist - Lookup: /help command")
            self.client.sendServerMessage("About: /about - Credits: /credits")
            self.client.sendServerMessage("MOTD: /motd - Rules: /rules")

    @config("category", "info")
    def commandCmdlist(self, parts, fromloc, overriderank):
        "/cmdlist category - Guest\nThe command list of your rank, categories."
        if len(parts) > 1:
            if parts[1].lower() not in ["all", "build", "world", "player", "info", "other"]:
                self.client.sendServerMessage("Unknown cmdlist '%s'" % parts[1])
            else:
                self.ListCommands(parts[1].lower())
        else:
            self.client.sendServerMessage("Command List - Use: /cmdlist category")
            self.client.sendServerMessage("Categories: all build world player info other")

    def ListCommands(self, list):
        self.client.sendServerMessage("%s Commands:" % list.title())
        commands = []
        for name, command in self.client.commands.items():
            try:
                config = getattr(command, "config")
            except AttributeError:
                config = recursive_default()
            if config["disabled"]:
                continue
            if not list == "other":
                if not list == "all":
                    if not config["category"]:
                        continue
                if config["rank"] == "owner" and not self.client.isOwner():
                    continue
                if config["rank"] == "director" and not self.client.isDirector():
                    continue
                if config["rank"] == "admin" and not self.client.isAdmin():
                    continue
                if config["rank"] == "mod" and not self.client.isMod():
                    continue
                if config["rank"] == "helper" and not self.client.isHelper():
                    continue
                if config["rank"] == "worldowner" and not self.client.isWorldOwner():
                    continue
                if config["rank"] == "op" and not self.client.isOp():
                    continue
                if config["rank"] == "builder" and not self.client.isBuilder():
                    continue
            else:
                if config["category"]:
                    continue
                if config["rank"] == "owner" and not self.client.isOwner():
                    continue
                if config["rank"] == "director" and not self.client.isDirector():
                    continue
                if config["rank"] == "admin" and not self.client.isAdmin():
                    continue
                if config["rank"] == "mod" and not self.client.isMod():
                    continue
                if config["rank"] == "helper" and not self.client.isHelper():
                    continue
                if config["rank"] == "worldowner" and not self.client.isWorldOwner():
                    continue
                if config["rank"] == "op" and not self.client.isOp():
                    continue
                if config["rank"] == "builder" and not self.client.isBuilder():
                    continue
            commands.append(name)
        if commands:
            self.client.sendServerList(sorted(commands))
        else:
            self.client.sendServerMessage("None.")

    @config("category", "info")
    def commandAbout(self, parts, fromloc, overriderank):
        "/about - Guest\nAliases: info\nAbout the server and software."
        self.client.sendSplitServerMessage("About The Server, powered by Arc %s | Credits: /credits" % VERSION)
        self.client.sendSplitServerMessage("Name: %s; Owners: %s" % (self.client.factory.server_name, ", ".join(self.client.factory.owners)))
        self.client.sendSplitServerMessage(self.client.factory.server_message)
        self.client.sendServerMessage("URL: %s" % self.client.factory.info_url)
        if self.client.factory.use_irc:
            self.client.sendServerMessage("IRC: "+self.client.factory.irc_config.get("irc", "server")+" "+self.client.factory.irc_channel)

    @config("category", "info")
    def commandCredits(self, parts, fromloc, overriderank):
        "/credits - Guest\nCredits for the creators, devs and testers."
        self.client.sendServerMessage("Arc Credits")
        list = Credits()
        for each in list:
            self.client.sendSplitServerMessage(each)

    @config("category", "info")
    def commandMOTD(self, parts, fromloc, overriderank):
        "/motd - Guest\nAliases: greeting\nShows the greeting."
        self.client.sendServerMessage("MOTD for "+self.client.factory.server_name+":")
        try:
            r = open('config/greeting.txt', 'r')
        except:
            r = open('config/greeting.example.txt', 'r')
        for line in r:
            self.client.sendNormalMessage(line)

    @config("category", "info")
    def commandRules(self, parts, fromloc, overriderank):
        "/rules - Guest\nShows the server rules."
        self.client.sendServerMessage("Rules for "+self.client.factory.server_name+":")
        try:
            r = open('config/rules.txt', 'r')
        except:
            r = open('config/rules.example.txt', 'r')
        for line in r:
            self.client.sendNormalMessage(line)

    @config("category", "info")
    def commandStaff(self, parts, fromloc, overriderank):
        "/staff - Guest\nLists all server staff."
        self.client.sendServerMessage("The Server Staff")
        list = Staff(self)
        for each in list:
            self.client.sendServerList(each)

    @config("category", "info")
    def commandHelpers(self, parts, fromloc, overriderank):
        "/helpers - Guest\nLists all Helpers."
        if len(self.client.factory.helpers):
            self.client.sendServerList(["Helpers:"] + list(self.client.factory.helpers))
        else:
            self.client.sendServerList(["Helpers:"] + list("N/A"))

    @config("category", "info")
    def commandDirectors(self, parts, fromloc, overriderank):
        "/directors - Guest\nLists all Directors."
        if len(self.client.factory.directors):
            self.client.sendServerList(["Directors:"] + list(self.client.factory.directors))
        else:
            self.client.sendServerList(["Directors:"] + list("N/A"))

    @config("category", "info")
    def commandAdmins(self, parts, fromloc, overriderank):
        "/admins - Guest\nLists all Admins."
        if len(self.client.factory.admins):
            self.client.sendServerList(["Admins:"] + list(self.client.factory.admins))
        else:
            self.client.sendServerList(["Admins:"] + list("N/A"))

    @config("category", "info")
    def commandMods(self, parts, fromloc, overriderank):
        "/mods - Guest\nLists all Mods."
        if len(self.client.factory.mods):
            self.client.sendServerList(["Mods:"] + list(self.client.factory.mods))
        else:
            self.client.sendServerList(["Mods:"] + list("N/A"))

    @config("category", "info")
    def commandDCURL(self, parts, fromloc, overriderank):
        "/dcurl - Guest\nAliases: womurl\nGives your Direct Connect URL for WoM Client 1.6.3+"
        # TODO: I think there is a twisted alt for this -tyteen
        ip = socket.gethostbyname(socket.gethostname())
        if ip == "127.0.0.1": # TODO: Also check LAN IP
            output = commands.getoutput("/sbin/ifconfig")
            ip = parseaddress(output)
        mppass = hashlib.md5(self.client.factory.salt + self.client.username).hexdigest()[-32:].strip("0")
        self.client.sendServerMessage("Direct Connect URL:")
        self.client.sendServerMessage("mc://%s:%s/%s/" % (ip, self.client.factory.config.getint("network", "port"), self.client.username))
        self.client.sendServerMessage("%s" % (mppass))