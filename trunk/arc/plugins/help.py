# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import hashlib, socket

from arc.constants import *
from arc.decorators import *
from arc.globals import *

class HelpPlugin(object):
    commands = {
        "help": "commandHelp",
        "cmdlist": "commandCmdlist",
        "about": "commandAbout",
        "credits": "commandCredits",
        "motd": "commandMOTD",
        "rules": "commandRules",

        "staff": "commandStaff",
        "helpers": "commandHelpers",
        "directors": "commandDirectors",
        "admins": "commandAdmins",
        "mods": "commandMods",

        "dcurl": "commandDCURL",
    }

    @config("category", "info")
    @config("usage", "[document|command]")
    @config("aliases", ["?"])
    def commandHelp(self, data):
        "Help for this server and commands."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("The Central Help Hub")
            data["client"].sendServerMessage("Documents: /help [cc|chats|guide|physic|ranks]")
            data["client"].sendServerMessage("Commands: /cmdlist - Lookup: /help command")
            data["client"].sendServerMessage("About: /about - Credits: /credits")
            data["client"].sendServerMessage("MOTD: /motd - Rules: /rules")
            return
        command = data["parts"][1]
        if command.lower() == "chats":
            data["client"].sendServerMessage("Help; Chats")
            data["client"].sendServerMessage("Whispers: @username Whispers")
            data["client"].sendServerMessage("WorldChat: !message")
            if data["client"].isMod(): data["client"].sendServerMessage("StaffChat: #message")
        elif command.lower() == "physic":
            data["client"].sendServerMessage("Help; Physics Engine")
            data["client"].sendServerMessage(
                "Turn physics on to use Physics (max of %s worlds)" % self.factory.physics_limit)
            data["client"].sendServerMessage("If fwater is on then your water won't move.")
            data["client"].sendServerMessage("Orange blocks make Lavafalls, darkblue blocks make Waterfalls.")
            data["client"].sendServerMessage("Spouts need fwater to be on in order to work.")
            data["client"].sendServerMessage("Sand will fall, grass will grow, sponges will absorb.")
            data["client"].sendServerMessage("Use unflood to move all water, lava, and spouts from the world.")
        elif command.lower() == "ranks":
            data["client"].sendNormalMessage(COLOUR_YELLOW + "Help: Server Ranks - " + COLOUR_GREEN +
                                          "Owner/Console [9] " + COLOUR_DARKRED + "Director [8] " + COLOUR_RED + "Admin [7] " + COLOUR_DARKBLUE + "Mod [6] "
                                          + COLOUR_DARKGREY + "Helper [5] " + COLOUR_DARKYELLOW + "World Owner [4] " + COLOUR_DARKCYAN + "Op [3] " + COLOUR_CYAN + "Builder [2] "
                                          + COLOUR_WHITE + "Guest [1] " + COLOUR_YELLOW + "VIP (Guest) " + COLOUR_BLACK + "Spec/Banned [0]")
        elif command.lower() == "cc":
            data["client"].sendServerMessage("Help; Colour Codes")
            data["client"].sendNormalMessage("&a%a &b%b &c%c &d%d &e%e &f%f")
            data["client"].sendNormalMessage("&0%0 &1%1 &2%2 &3%3 &4%4 &5%5 &6%6 &7%7 &8%8 &9%9")
        elif command.lower() == "guide":
            data["client"].sendServerMessage("Help; The Guide")
            data["client"].sendServerMessage("/command required [optional]")
            data["client"].sendServerMessage("command - the command you're using (like /help)")
            data["client"].sendServerMessage("required - this stuff is required after the command")
            data["client"].sendServerMessage("optional - this stuff isn't needed, like blb coords")
            data["client"].sendServerMessage("Example: /help [document/command]")
            data["client"].sendServerMessage("You can do /help only or optionally input more.")
        elif command in (self.factory.commands.keys() + self.factory.aliases.keys()):
            # Check if they are querying the alias
            theCommand = command if command in self.factory.commands else self.factory.aliases[command]
            func = self.factory.commands[theCommand] 
            data["client"].sendServerMessage("/%s%s - %s" %
                (theCommand, (" "+func.config["usage"] if "usage" in func.config else ""), (func.config["rank"].capitalize() if func.config["rank"] != "" else "Guest")))
            aliases = find_keys(self.factory.aliases, theCommand)
            if aliases != []:
                data["client"].sendServerMessage("Aliases: %s" % ", ".join(aliases))
            if func.__doc__:
                for line in func.__doc__.split("\n"):
                    data["client"].sendServerMessage(line)
            else:
                data["client"].sendServerMessage("There's no help for that command.")
            return
        else:
            data["client"].sendServerMessage("Unknown command '%s'" % command)

    @config("category", "info")
    @config("aliases", ["commands"])
    def commandCmdlist(self, data):
        "Lists all commands available."
        data["client"].sendServerMessage("Commands:")
        commands = []
        cmdlist = sorted(self.factory.commands.keys())
        for command in cmdlist:
            try:
                config = getattr(self.factory.commands[command], "config")
            except AttributeError:
                config = recursive_default()
            if config["disabled"]:
                continue
            if data["fromloc"] in ["user", "cmdblock"]:
                if config["rank"] == "owner":
                    command = "%s%s" % (RANK_COLOURS["owner"], command)
                elif config["rank"] == "director":
                    command = "%s%s" % (RANK_COLOURS["director"], command)
                elif config["rank"] == "admin":
                    command = "%s%s" % (RANK_COLOURS["admin"], command)
                elif config["rank"] == "mod":
                    command = "%s%s" % (RANK_COLOURS["mod"], command)
                elif config["rank"] == "helper":
                    command = "%s%s" % (RANK_COLOURS["helper"], command)
                elif config["rank"] == "worldowner":
                    command = "%s%s" % (RANK_COLOURS["worldowner"], command)
                elif config["rank"] == "op":
                    command = "%s%s" % (RANK_COLOURS["op"], command)
                elif config["rank"] == "builder":
                    command = "%s%s" % (RANK_COLOURS["builder"], command)
                else:
                    command = "%s%s" % (RANK_COLOURS["guest"], command)
            commands.append(command)
        if commands:
            data["client"].sendSplitServerMessage("Commands: %s" % " ".join(commands))
        else:
            data["client"].sendServerMessage("None.")
        data["client"].sendServerMessage("%s command(s) total." % len(commands))

    @config("category", "info")
    @config("aliases", ["info"])
    def commandAbout(self, data):
        "Displays information about the server and software."
        data["client"].sendSplitServerMessage("About The Server, powered by Arc %s | Credits: /credits" % VERSION)
        data["client"].sendSplitServerMessage("Name: %s; Owners: %s" % 
                                            (self.factory.server_name, ", ".join(self.factory.owners)))
        data["client"].sendSplitServerMessage(self.factory.server_message)
        data["client"].sendServerMessage("URL: %s" % self.factory.info_url)
        if self.factory.use_irc:
            data["client"].sendServerMessage("IRC: %s %s" %
                                            (self.factory.irc_config.get("irc", "server"), self.factory.irc_channel))

    @config("category", "info")
    def commandCredits(self, data):
        "/credits - Guest\nCredits for the creators, devs and testers."
        data["client"].sendServerMessage("Arc Credits")
        for each in CREDITS_TEXT:
            data["client"].sendSplitServerMessage(each)

    @config("category", "info")
    @config("aliases", ["greeting"])
    def commandMOTD(self, data):
        "Shows the MOTD."
        data["client"].sendServerMessage("MOTD for %s:" % self.factory.server_name)
        try:
            r = open('config/greeting.txt', 'r')
        except:
            r = open('config/greeting.example.txt', 'r')
        for line in r:
            data["client"].sendNormalMessage(line)

    @config("category", "info")
    def commandRules(self, data):
        "Shows the server rules."
        data["client"].sendServerMessage("Rules for %s:" % self.factory.server_name)
        try:
            r = open('config/rules.txt', 'r')
        except:
            r = open('config/rules.example.txt', 'r')
        for line in r:
            data["client"].sendSplitServerMessage(line, plain=True)

    @config("category", "info")
    @config("usage", "[all]")
    def commandStaff(self, data):
        "Lists all online server staff.\nSpecify all to retrieve the full server staff list."
        if len(data["parts"]) > 1:
            if data["parts"][1] == "all":
                data["client"].sendServerMessage("The Server Staff")
                theList = []
                if len(self.factory.owners): # This doesn't make much sense but okay
                    data["client"].sendServerList(["Owners:"] + list(self.factory.owners))
                if len(self.factory.directors):
                    data["client"].sendServerList(["Directors:"] + list(self.factory.directors))
                if len(self.factory.admins):
                    data["client"].sendServerList(["Admins:"] + list(self.factory.admins))
                if len(self.factory.mods):
                    data["client"].sendServerList(["Mods:"] + list(self.factory.mods))
                if len(self.factory.helpers):
                    data["client"].sendServerList(["Helpers:"] + list(self.factory.helpers))
            else:
                data["client"].sendServerMessage("Usage: /staff [all]")
        else:
            data["client"].sendServerMessage("Online server staff (Do /staff all for full list):")
            owners = []
            directors = []
            admins = []
            mods = []
            helpers = []
            for user in self.factory.usernames:
                if self.factory.usernames[user].isOwner():
                    owners.append(self.factory.usernames[user].username)
                elif self.factory.usernames[user].isDirector():
                    directors.append(self.factory.usernames[user].username)
                elif self.factory.usernames[user].isAdmin():
                    admins.append(self.factory.usernames[user].username)
                elif self.factory.usernames[user].isMod():
                    mods.append(self.factory.usernames[user].username)
                elif self.factory.usernames[user].isHelper():
                    helpers.append(self.factory.usernames[user].username)
            if owners != []:
                data["client"].sendServerList(["Owners:"] + owners)
            if directors != []:
                data["client"].sendServerList(["Directors:"] + directors)
            if admins != []:
                data["client"].sendServerList(["Admins:"] + admins)
            if mods != []:
                data["client"].sendServerList(["Mods:"] + mods)
            if helpers != []:
                data["client"].sendServerList(["Helpers:"] + helpers)

    @config("category", "info")
    def commandHelpers(self, data):
        "Lists all Helpers."
        if len(self.factory.helpers):
            data["client"].sendServerList(["Helpers:"] + list(self.factory.helpers))
        else:
            data["client"].sendServerMessage("Helpers: N/A")

    @config("category", "info")
    def commandDirectors(self, data):
        "Lists all Directors."
        if len(self.factory.directors):
            data["client"].sendServerList(["Directors:"] + list(self.factory.directors))
        else:
            data["client"].sendServerMessage("Directors: N/A")

    @config("category", "info")
    def commandAdmins(self, data):
        "Lists all Admins."
        if len(self.factory.admins):
            data["client"].sendServerList(["Admins:"] + list(self.factory.admins))
        else:
            data["client"].sendServerMessage("Admins: N/A")

    @config("category", "info")
    def commandMods(self, data):
        "Lists all Mods."
        if len(self.factory.mods):
            data["client"].sendServerList(["Mods:"] + list(self.factory.mods))
        else:
            data["client"].sendServerMessage("Mods: N/A")

    @config("category", "info")
    @config("aliases", ["womurl"])
    @config("disabled-on", ["irc", "irc_query", "cmdblock", "console"])
    def commandDCURL(self, data):
        "Gives your Direct Connect URL for WoM Client 1.6.3+"
        # TODO: fix this broken code -tyteen
        ip = socket.gethostbyname(socket.gethostname())
        if ip == "127.0.0.1": # TODO: Also check LAN IP
            output = commands.getoutput("/sbin/ifconfig")
            ip = parseaddress(output)
        mppass = hashlib.md5(self.factory.salt + data["client"].username).hexdigest()[-32:].strip("0")
        data["client"].sendServerMessage("Direct Connect URL for %s:" % data["client"].username)
        data["client"].sendServerMessage("mc://%s:%s/%s/" % (ip, self.factory.server_port, data["client"].username))
        data["client"].sendServerMessage("%s" % (mppass))
        data["client"].sendServerMessage("Security advice: Never share this URL with anybody.")

serverPlugin = HelpPlugin