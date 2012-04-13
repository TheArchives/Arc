# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cmath, cPickle, time

from arc.constants import *
from arc.decorators import *
from arc.globals import *

class PlayerUtilPlugin(object):
    commands = {
        "rank": "commandRank",
        "derank": "commandDeRank",
        "spec": "commandSpec",
        "unspec": "commandDeSpec",
        "specced": "commandSpecced",
        "rankname": "commandOldRanks",
        "derankname": "commandOldDeRanks",

        "respawn": "commandRespawn",

        "fetch": "commandFetch",
        "invite": "commandInvite",

        "coord": "commandCoord",
        "tp": "commandTeleport",

        "tpp": "commandTeleProtect",

        "who": "commandWho",
        "locate": "commandLocate",
        "lastseen": "commandLastseen",

        "mute": "commandMute",
        "unmute": "commandUnmute",
        "muted": "commandMuted",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "consoleLoaded": "gotConsole",
        "messageSent": "messageSent",
        "recvmessage": "messageReceived",
        }

    colors = ["&4", "&c", "&e", "&a", "&2", "&3", "&b", "&d", "&5"]

    def gotClient(self, data):
        data["client"].var_fetchrequest = False
        data["client"].var_fetchdata = ()
        data["client"].num = int(0)
        data["client"].muted = set()

    def gotConsole(self):
        self.factory.console.var_fetchrequest = False
        self.factory.console.var_fetchdata = ()
        self.factory.console.num = int(0)
        self.factory.console.muted = set()

    def messageSent(self, data):
        if data["client"].var_fetchrequest:
            data["client"].var_fetchrequest = False
            if message in ["y", "yes"]:
                sender, world, rx, ry, rz = data["client"].var_fetchdata
                if data["client"].world == world:
                    data["client"].teleportTo(rx, ry, rz)
                else:
                    data["client"].changeToWorld(world.id, position=(rx, ry, rz))
                data["client"].sendServerMessage("You have accepted the fetch request.")
                sender.sendServerMessage("%s has accepted your fetch request." % data["client"].username)
            elif message in ["n", "no"]:
                sender = data["client"].var_fetchdata[0]
                data["client"].sendServerMessage("You did not accept the fetch request.")
                sender.sendServerMessage("%s did not accept your request." % data["client"].username)
            else:
                sender = data["client"].var_fetchdata[0]
                data["client"].sendServerMessage("You have ignored the fetch request.")
                sender.sendServerMessage("%s has ignored your request." % data["client"].username)
                return
            return True

    def messageReceived(self, data):
        "Stop viewing a message if we've muted them."
        if data["username"].lower() in data["client"].muted:
            return False

    @config("category", "player")
    @config("rank", "mod")
    def commandSpecced(self, data):
        "/specced - Mod\nShows who is Specced."
        if len(self.factory.spectators):
            data["client"].sendServerList(["Specced:"] + list(self.factory.spectators))
        else:
            data["client"].sendServerList(["Specced: No one."])

    @config("category", "player")
    @config("rank", "op")
    @config("usage", "username rank [world]")
    @config("aliases", ["setrank", "promote"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandRank(self, data):
        "Makes username the rank of rankname."
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("You must specify a rank and username.")
            return
        username = data["parts"][1].lower()
        rank = data["parts"][2].lower()
        if rank not in ["builder", "op", "worldowner", "helper", "mod", "admin", "director"]:
            data["client"].sendServerMessage("Unknown rank '%s'" % rank)
            return
        if rank in ["builder", "op", "worldowner"]:
            # World check
            if len(data["parts"]) > 3:
                try:
                    world = self.factory.worlds[data["parts"][3]]
                except KeyError:
                    data["client"].sendServerMessage("Unknown world %s." % data["parts"][3])
            else:
                if data["fromloc"] == "user":
                    world = data["client"].world
                else:
                    data["client"].sendServerMessage("You must provide a world.")
        # Do the ranks
        if rank == "builder":
            if data["fromloc"] == "user":
                if not (data["client"].username.lower() in world.ops or data["client"].isWorldOwner()):
                    data["client"].sendServerMessage("Only Op+ may /rank builders.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() in world.ops) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Op+ may /rank builders.")
                        return
            world.builders.add(username)
        elif rank == "op":
            if data["fromloc"] == "user":
                if not data["client"].isWorldOwner():
                    data["client"].sendServerMessage("Only WorldOwner+ may /rank ops.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() == world.status["owner"]) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only WorldOwner+ may /rank ops.")
                        return
            world.ops.add(username)
        elif rank == "worldowner":
            if data["fromloc"] == "user":
                if not data["client"].isWorldOwner():
                    data["client"].sendServerMessage("Only WorldOwner+ may /rank world owners.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() == world.status["owner"]) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only WorldOwner+ may /rank world owners.")
                        return
            self.client.world.status["owner"] = (username)
        elif rank == "helper":
            if data["fromloc"] == "user":
                if not data["client"].isMod():
                    data["client"].sendServerMessage("Only Mod+ may /rank helpers.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Mod+ may /rank helpers.")
                        return
            self.factory.helpers.add(username)
        elif rank == "mod":
            if data["fromloc"] == "user":
                if not data["client"].isDirector():
                    data["client"].sendServerMessage("Only Director+ may /rank mods.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isDirector(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Director+ may /rank mods.")
                        return
            self.factory.mods.add(username)
        elif rank == "admin":
            if data["fromloc"] == "user":
                if not data["client"].isDirector():
                    data["client"].sendServerMessage("Only Director+ may /rank admins.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isDirector(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Director+ may /rank admins.")
                        return
            self.factory.admins.add(username)
        elif rank == "director":
            if data["fromloc"] == "user":
                if not data["client"].isOwner():
                    data["client"].sendServerMessage("Only Owner+ may /rank directors.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isOwner(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Owner+ may /rank directors.")
                        return
            self.factory.directors.add(username)
        # Final cleanup
        if username in self.factory.usernames:
            if rank in ["builder", "op", "worldowner"]:
                if self.factory.usernames[username].world == world:
                    self.factory.usernames[username].sendRankUpdate()
            else:
                self.factory.usernames[username].sendRankUpdate()
            self.factory.usernames[username].sendServerMessage("You are now %s %s%s." % (("an" if (rank.startswith(tuple("aeiou"))) else "a", rank, (" here" if rank in ["builder", "op", "worldowner"] else ""))))
        data["client"].sendServerMessage("%s is now %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " in world %s" % world.id if rank in ["builder", "op", "worldowner"] else ""))

    @config("category", "player")
    @config("rank", "op")
    @config("usage", "username rank [world]")
    @config("aliases", ["demote"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandDeRank(self, data):
        "Makes username lose the rank of rankname."
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("You must specify a rank and username.")
            return
        username = data["parts"][1].lower()
        rank = data["parts"][2].lower()
        if rank not in ["builder", "op", "worldowner", "helper", "mod", "admin", "director"]:
            data["client"].sendServerMessage("Unknown rank '%s'" % rank)
            return
        if rank in ["builder", "op", "worldowner"]:
            # World check
            if len(data["parts"]) > 3:
                try:
                    world = self.factory.worlds[data["parts"][3]]
                except KeyError:
                    data["client"].sendServerMessage("World %s does not exist, or is not booted." % data["parts"][3])
            else:
                if data["fromloc"] == "user":
                    world = data["client"].world
                else:
                    data["client"].sendServerMessage("You must provide a world.")
        # Do the ranks
        if rank == "builder":
            if data["fromloc"] == "user":
                if not (data["client"].username.lower() in world.ops or data["client"].isWorldOwner()):
                    data["client"].sendServerMessage("Only Op+ may /derank builders.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() in world.ops) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Op+ may /derank builders.")
                        return
            if username not in world.builders:
                data["client"].sendServerMessage("%s is not a builder." % username)
            else:
                world.builders.remove(username)
        elif rank == "op":
            if data["fromloc"] == "user":
                if not data["client"].isWorldOwner():
                    data["client"].sendServerMessage("Only WorldOwner+ may /derank ops.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() == world.status["owner"]) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only WorldOwner+ may /derank ops.")
                        return
            if username not in world.ops:
                data["client"].sendServerMessage("%s is not an op." % username)
            else:
                world.ops.remove(username)
        elif rank == "worldowner":
            if data["fromloc"] == "user":
                if not data["client"].isWorldOwner():
                    data["client"].sendServerMessage("Only WorldOwner+ may /derank world owners.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not ((data["client"].username.lower() == world.status["owner"]) or self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only WorldOwner+ may /derank world owners.")
                        return
            if username != world.status["owner"]:
                data["client"].sendServerMessage("%s is not the world owner." % username)
            else:
                world.status["owner"] = ""
        elif rank == "helper":
            if data["fromloc"] == "user":
                if not data["client"].isMod():
                    data["client"].sendServerMessage("Only Mod+ may /derank helpers.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isMod(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Mod+ may /derank helpers.")
                        return
            if username not in self.factory.helpers:
                data["client"].sendServerMessage("%s is not a helper." % username)
            else:
                self.factory.helpers.remove(username)
        elif rank == "mod":
            if data["fromloc"] == "user":
                if not data["client"].isDirector():
                    data["client"].sendServerMessage("Only Director+ may /derank mods.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isDirector(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Director+ may /derank mods.")
                        return
            if username not in self.factory.mods:
                data["client"].sendServerMessage("%s is not a mod." % username)
            else:
                self.factory.mods.remove(username)
        elif rank == "admin":
            if data["fromloc"] == "user":
                if not data["client"].isDirector():
                    data["client"].sendServerMessage("Only Director+ may /derank admins.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isDirector(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Director+ may /derank admins.")
                        return
            if username not in self.factory.admins:
                data["client"].sendServerMessage("%s is not an admin." % username)
            else:
                self.factory.admins.remove(username)
        elif rank == "director":
            if data["fromloc"] == "user":
                if not data["client"].isOwner():
                    data["client"].sendServerMessage("Only Owner+ may /derank directors.")
                    return
            else:
                if data["fromloc"] != "console":
                    if not (self.factory.isOwner(data["client"].username.lower())):
                        data["client"].sendServerMessage("Only Owner+ may /derank directors.")
                        return
            if username not in self.factory.directors:
                data["client"].sendServerMessage("%s is not a director." % username)
            else:
                self.factory.directors.remove(username)
        # Final cleanup
        if username in self.factory.usernames:
            if rank in ["builder", "op", "worldowner"]:
                if self.factory.usernames[username].world == world:
                    self.factory.usernames[username].sendRankUpdate()
            else:
                self.factory.usernames[username].sendRankUpdate()
            self.factory.usernames[username].sendServerMessage("You are no longer %s %s%s." % (("an" if (rank.startswith(tuple("aeiou"))) else "a", rank, (" here" if rank in ["builder", "op", "worldowner"] else ""))))
        data["client"].sendServerMessage("%s is now %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " in world %s" % world.id if rank in ["builder", "op", "worldowner"] else ""))

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["builder", "op", "helper", "mod", "admin", "director"])
    @config("usage", "username [world]")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandOldRanks(self, data):
        "Ranks the user to the rank specified in the command name."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must specify a username.")
            return
        if data["parts"][0] == "/writer":
            data["parts"][0] = "/builder"
        data["parts"][0].strip("/")
        parts = ["/rank", data["parts"][1], data["parts"][0]] + ([data["parts"][2]] if len(data["parts"]) == 3 else [])
        self.factory.runCommand("rank", parts, data["fromloc"], data["overriderank"], data["client"])

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["debuilder", "deop", "dehelper", "demod", "deadmin", "dedirector"])
    @config("usage", "username [world]")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandOldDeRanks(self, data):
        "Deranks the user from the rank specified in the command name."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must specify a rank and username.")
            return
        if data["parts"][0] == "/dewriter":
            data["parts"][0] = "/debuilder"
        data["parts"][0].replace("/de", "")
        parts = ["/derank", data["parts"][1], data["parts"][0]] + ([data["parts"][2]] if len(data["parts"]) == 3 else [])
        self.factory.runCommand("derank", parts, data["fromloc"], data["overriderank"], data["client"])

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandSpec(self, data):
        "Makes the user as a spec."
        if self.factory.isMod(data["parts"][1].lower()):
            data["client"].sendServerMessage("You cannot make staff a spec!")
            return
        self.factory.spectators.add(data["parts"][1].lower())
        if data["parts"][1].lower() in self.factory.usernames:
            self.factory.usernames[data["parts"][1].lower()].sendRankUpdate()
        data["client"].sendServerMessage("%s is now a spec." % data["parts"][1].lower())

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username")
    @config("aliases", ["despec"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandDeSpec(self, data):
        "Removes the user from the spec list."
        if data["parts"][1].lower() not in self.factory.spectators:
            data["client"].sendServerMessage("User %s is not specced." % data["parts"][1].lower())
            return
        self.factory.spectators.remove(data["parts"][1].lower())
        if data["parts"][1].lower() in self.factory.usernames:
            self.factory.usernames[data["parts"][1].lower()].sendRankUpdate()
        data["client"].sendServerMessage("%s is no longer a spec." % data["parts"][1].lower())

    @config("category", "player")
    @config("rank", "op")
    @config("usage", "username")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandRespawn(self, data):
        "/respawn username - Mod\nRespawns the user."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Usage: /respawn username")
            return
        user = self.factory.usernames[parts[1]]
        if not data["client"].isMod() and (user.world.id != data["client"].world.id):
            data["client"].sendServerMessage("The user is not in your world.")
            return
        user.respawn()
        user.sendServerMessage("You have been respawned by %s." % data["client"].username)
        data["client"].sendServerMessage("%s has been respawned." % user.username)

    @config("category", "player")
    @config("usage", "username")
    def commandInvite(self, data):
        "Invites a user to be where you are."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Usage: /invite username")
            return
        user = self.factory.usernames[data["parts"][1]]
        # Shift the locations right to make them into block coords
        rx, ry, rz = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5
        user.var_prefetchdata = (self.client, data["client"].world)
        user.sendServerMessage("%s would like to fetch you%s." % (data["client"].username, (("to %s" % data["client"].world.id) if data["client"].world.id == user.world.id else "")))
        user.sendServerMessage("Do you wish to accept? [y]es [n]o")
        user.var_fetchrequest = True
        user.var_fetchdata = (self.client, data["client"].world, rx, ry, rz)
        data["client"].sendServerMessage("The fetch request has been sent.")

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["bring"])
    @config("usage", ["username"])
    @config("disabled-on", ["irc", "irc-query", "console"])
    def commandFetch(self, data):
        "Teleports a user to be where you are."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Usage: /fetch username")
            return
        user = self.factory.usernames[parts[1]]
        # Shift the locations right to make them into block coords
        rx, ry, rz = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5
        if user.world == data["client"].world:
            user.teleportTo(rx, ry, rz)
        else:
            if data["client"].isMod():
                user.changeToWorld(data["client"].world.id, position=(rx, ry, rz))
            else:
                data["client"].sendServerMessage("%s cannot be fetched from '%s'" % (data["client"].username, user.world.id))
                return
        user.sendServerMessage("You have been fetched by %s." % data["client"].username)

    @config("category", "player")
    @config("usage", "on|off")
    @on_off_command
    @config("disabled-on", ["irc", "irc-query", "console"])
    def commandTeleProtect(self, data):
        "Enables or disables teleport protection\n(Stops non-staff from teleporting to you.)"
        if data["onoff"] == "on":
            data["client"].settings["tpprotect"] = True
            data["client"].data.set("misc", "tpprotect", "true")
            data["client"].sendServerMessage("Teleport protection is now on.")
        else:
            data["client"].settings["tpprotect"] = False
            data["client"].data.set("misc", "tpprotect", "false")
            data["client"].sendServerMessage("Teleport protection is now off.")

    @config("category", "world")
    @config("usage", "x y z [h p]")
    @config("disabled-on", ["irc", "irc-query", "console"])
    def commandCoord(self, data):
        "Teleports you to coords. NOTE: y is up."
        try:
            x, y, z = [int(i) for i in data["parts"][1:3]]
            try:
                if len(data["parts"]) > 5: h = int(data["parts"][4])
                elif len(data["parts"]) > 6: p = int(data["parts"][5])
            except:
                data["client"].teleportTo(x, y, z)
            else:
                if len(data["parts"]) > 6:
                    data["client"].teleportTo(x, y, z, h, p)
                else:
                    data["client"].teleportTo(x, y, z, h)
        except (IndexError, ValueError):
            data["client"].sendServerMessage("Usage: /goto x y z [h p]")
            data["client"].sendServerMessage("MCLawl users: /l worldname")

    @config("category", "player")
    @config("aliases", ["teleport"])
    @config("usage", "username")
    @username_command
    @config("disabled-on", ["irc", "irc-query", "console"])
    def commandTeleport(self, data):
        "Teleports you to the users location."
        try:
            x, y, z = data["user"].x >> 5, data["user"].y >> 5, data["user"].z >> 5
        except AttributeError:
            data["client"].sendServerMessage("That user seems to have went offline before the teleportation can finish.")
            return
        if (data["user"].settings["tpprotect"] == True) and not data["client"].isMod():
            data["client"].sendServerMessage("%s has teleport protection enabled - you cannot teleport to him/her." % data["user"].username)
            return
        if data["user"].world == data["client"].world:
            data["client"].teleportTo(x, y, z)
        else:
            if data["client"].canEnter(data["user"].world):
                data["client"].changeToWorld(data["user"].world.id, position=(x, y, z))
            else:
                data["client"].sendServerMessage("Sorry, that world is private.")

    @config("usage", "username")
    @only_username_command
    def commandLastseen(self, data):
        "Tells you when 'username' was last seen."
        if data["parts"][1] not in self.factory.lastseen:
            data["client"].sendServerMessage("There are no records of %s." % data["parts"][1])
        else:
            t = time.time() - self.factory.lastseen[data["parts"][1]]
            days, hours, mins = t // 86400, (t % 86400) // 3600, (t % 3600) // 60
            desc = "%id, %ih, %im" % (days, hours, mins)
            data["client"].sendServerMessage("%s was last seen %s ago." % (data["parts"][1], desc))

    @config("aliases", ["find"])
    @config("usage", "username")
    @username_command
    def commandLocate(self, data):
        "Tells you what world a user is in."
        data["client"].sendServerMessage("%s is in %s" % (data["user"].username, data["user"].world.id))

    @config("category", "player")
    @config("usage", "[username]")
    @config("aliases", ["pinfo", "players", "users", "whois"])
    def commandWho(self, data):
        "Shows online users, or user lookup."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Do '/who username' for more info.")
            data["client"].sendServerMessage("Players: ")
            for key in self.factory.worlds:
                if len(self.factory.worlds[key].clients) > 0:
                    theList = [(key + ": ")]
                    for c in self.factory.worlds[key].clients:
                        user = str(c.username)
                        if self.factory.isSpectator(user): user = COLOUR_BLACK + user
                        elif self.factory.isOwner(user): user = COLOUR_GREEN + user
                        elif self.factory.isDirector(user): user = COLOUR_DARKRED + user
                        elif self.factory.isAdmin(user): user = COLOUR_RED + user
                        elif self.factory.isMod(user): user = COLOUR_DARKBLUE + user
                        elif self.factory.isHelper(user): user = COLOUR_DARKGREY + user
                        elif user in INFO_VIPLIST: user = COLOUR_YELLOW + user
                        elif user == data["client"].world.status["owner"].lower(): user = COLOUR_DARKYELLOW + user
                        elif user in data["client"].world.ops: user = COLOUR_DARKCYAN + user
                        elif user in data["client"].world.builders: user = COLOUR_CYAN + user
                        else: user = COLOUR_WHITE + user
                        theList.append(user)
                    data["client"].sendServerList(theList, plain=True)
        else:
            if data["parts"][1].lower() in self.factory.usernames:
                # Parts is an array, always, so we get the first item.
                user = self.factory.usernames[data["parts"][1]].lower()
                data["client"].sendNormalMessage("%s%s%s %s%s" % (user.userColour(), user.username, COLOUR_YELLOW, user.world.id, ((" | %s" % str(user.ip)) if (data["client"].isAdmin() or user == data["client"]) else "")))
            else:
                # Parts is an array, always, so we get the first item.
                username = data["parts"][1].lower()
                data["client"].sendNormalMessage("%s%s%s Offline" % (data["client"].userColour(), data["parts"][1], COLOUR_DARKRED))
                if username not in self.factory.lastseen:
                    return
                t = time.time() - self.factory.lastseen[username]
                days, hours, mins = t // 86400, (t % 86400) // 3600, (t % 3600) // 60
                desc = "%id, %ih, %im" % (days, hours, mins)
                data["client"].sendServerMessage("Online %s ago" % desc)

    @config("category", "player")
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMute(self, data):
        "/mute username - Guest\nStops you hearing messages from 'username'."
        data["client"].muted.add(data["parts"][1])
        data["client"].sendServerMessage("%s has been muted." % data["parts"][1])

    @config("category", "player")
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandUnmute(self, data):
        "Lets you hear messages from this user again"
        if data["parts"][1] in self.muted:
            self.muted.remove(data["parts"][1])
            data["client"].sendServerMessage("%s has been unmuted." % data["parts"][1])
        else:
            data["client"].sendServerMessage("%s was not muted." % data["parts"][1])

    @config("category", "player")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMuted(self, data):
        "/muted - Guest\nLists people you have muted."
        if data["client"].muted:
            data["client"].sendServerList(["Muted:"] + list(data["client"].muted))
        else:
            data["client"].sendServerMessage("You haven't muted anyone.")

serverPlugin = PlayerUtilPlugin