# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cmath, cPickle, time

from arc.constants import *
from arc.decorators import *
from arc.globals import *
from arc.plugins import ProtocolPlugin

class PlayerUtilPlugin(ProtocolPlugin):
    commands = {
        "rank": "commandRank",
        "setrank": "commandRank",
        "promote": "commandRank",
        "derank": "commandDeRank",
        "demote": "commandDeRank",
        "spec": "commandSpec",
        "unspec": "commandDeSpec",
        "despec": "commandDeSpec",
        "specced": "commandSpecced",
        "writer": "commandOldRanks",
        "builder": "commandOldRanks",
        "op": "commandOldRanks",
        "helper": "commandOldRanks",
        "mod": "commandOldRanks",
        "admin": "commandOldRanks",
        "director": "commandOldRanks",
        "dewriter": "commandOldDeRanks",
        "debuilder": "commandOldDeRanks",
        "deop": "commandOldDeRanks",
        "dehelper": "commandOldDeRanks",
        "demod": "commandOldDeRanks",
        "deadmin": "commandOldDeRanks",
        "dedirector": "commandOldDeRanks",

        "respawn": "commandRespawn",

        "fetch": "commandFetch",
        "bring": "commandFetch",
        "invite": "commandInvite",

        "fly": "commandFly",

        "coord": "commandCoord",
        "goto": "commandCoord",
        "tp": "commandTeleport",
        "teleport": "commandTeleport",

        "tpp": "commandTeleProtect",

        "who": "commandWho",
        "whois": "commandWho",
        "players": "commandWho",
        "pinfo": "commandWho",
        "locate": "commandLocate",
        "find": "commandLocate",
        "lastseen": "commandLastseen",

        "mute": "commandMute",
        "unmute": "commandUnmute",
        "muted": "commandMuted",

        "clearchat": "commandClearChat",
        }

    hooks = {
        "chatmsg": "message",
        "poschange": "posChanged",
        "newworld": "newWorld",
        "recvmessage": "messageReceived",
        }

    colors = ["&4", "&c", "&e", "&a", "&2", "&3", "&b", "&d", "&5"]

    def loadRank(self):
        file = open('config/data/titles.dat', 'r')
        rank_dic = cPickle.load(file)
        file.close()
        return rank_dic

    def dumpRank(self, bank_dic):
        file = open('config/data/titles.dat', 'w')
        cPickle.dump(bank_dic, file)
        file.close()

    def gotClient(self):
        self.client.var_fetchrequest = False
        self.client.var_fetchdata = ()
        self.flying = False
        self.last_flying_block = None
        self.num = int(0)
        self.muted = set()

    def message(self, message):
        if self.client.var_fetchrequest:
            self.client.var_fetchrequest = False
            if message in ["y", "yes"]:
                sender, world, rx, ry, rz = self.client.var_fetchdata
                if self.client.world == world:
                    self.client.teleportTo(rx, ry, rz)
                else:
                    self.client.changeToWorld(world.id, position=(rx, ry, rz))
                self.client.sendServerMessage("You have accepted the fetch request.")
                sender.sendServerMessage("%s has accepted your fetch request." % self.client.username)
            elif message in ["n", "no"]:
                sender = self.client.var_fetchdata[0]
                self.client.sendServerMessage("You did not accept the fetch request.")
                sender.sendServerMessage("%s did not accept your request." % self.client.username)
            else:
                sender = self.client.var_fetchdata[0]
                self.client.sendServerMessage("You have ignored the fetch request.")
                sender.sendServerMessage("%s has ignored your request." % self.client.username)
                return
            return True

    def messageReceived(self, colour, username, text, action):
        "Stop viewing a message if we've muted them."
        if username.lower() in self.muted:
            return False

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        # Are we fake-flying them?
        if self.flying:
            fly_block_loc = ((x >> 5), ((y - 48) >> 5) - 1, (z >> 5))
            if not self.last_flying_block:
                # OK, send the first flying blocks
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
            else:
                # Have we moved at all?
                if fly_block_loc != self.last_flying_block:
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2],
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2],
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2],
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2],
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1,
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1,
                        BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1],
                        self.last_flying_block[2] - 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1],
                        self.last_flying_block[2] + 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1],
                        self.last_flying_block[2] - 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1],
                        self.last_flying_block[2] + 1, BLOCK_AIR)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
            self.last_flying_block = fly_block_loc
        else:
            if self.last_flying_block:
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2],
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2],
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2],
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2],
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1,
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1,
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] - 1,
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] + 1,
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] - 1,
                    BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] + 1,
                    BLOCK_AIR)
                self.last_flying_block = None

    def newWorld(self, world):
        "Hook to reset flying abilities in new worlds if not op."
        if self.client.isSpectator():
            self.flying = False

    def setCsBlock(self, x, y, z, type):
        if y > -1 and x > -1 and z > -1:
            if y < self.client.world.y and x < self.client.world.x and z < self.client.world.z:
                if ord(self.client.world.blockstore.raw_blocks[self.client.world.blockstore.get_offset(x, y, z)]) is 0:
                    self.client.sendPacked(TYPE_BLOCKSET, x, y, z, type)

    def sendgo(self):
        self.client.sendPlainWorldMessage("&7GET SET: &aGO!")
        self.num = 0

    def sendcount(self, count):
        if int(self.num) - int(count) == 1:
            self.client.sendPlainWorldMessage("&7GET READY: &e1")
        elif not int(self.num) - int(count) == 0:
            self.client.sendPlainWorldMessage("&7COUNTDOWN: &c%s" % (int(self.num) - int(count)))

    @config("category", "player")
    @config("rank", "mod")
    def commandSpecced(self, user, fromloc, overriderank):
        "/specced - Mod\nShows who is Specced."
        if len(self.client.factory.spectators):
            self.client.sendServerList(["Specced:"] + list(self.client.factory.spectators))
        else:
            self.client.sendServerList(["Specced: No one."])

    @config("category", "player")
    @config("rank", "op")
    @config("disabled_cmdblocks", True)
    def commandRank(self, parts, fromloc, overriderank):
        "/rank username rankname - Op\nAliases: setrank, promote\nMakes username the rank of rankname."
        if len(parts) < 3:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "op")
    @config("disabled_cmdblocks", True)
    def commandDeRank(self, parts, fromloc, overriderank):
        "/derank username rankname - Op\nAliases: demote\nMakes username lose the rank of rankname."
        if len(parts) < 3:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "op")
    @config("disabled_cmdblocks", True)
    def commandOldRanks(self, parts, fromloc, overriderank):
        "/rankname username [world] - Op\nAliases: writer, builder, op, helper, mod, admin, director\nThis is here for Myne users."
        if len(parts) < 2:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            if parts[0] == "/writer":
                parts[0] = "/builder"
            parts[0] = parts[0].strip("/")
            parts = ["/rank", parts[1], parts[0]] + ([parts[2]] if len(parts) == 3 else [])
            self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "op")
    @config("disabled_cmdblocks", True)
    def commandOldDeRanks(self, parts, fromloc, overriderank):
        "/derankname username [world] - Op\nAliases: dewriter, debuilder, deop, dehelper, demod, deadmin, dedirector\nThis is here for Myne users."
        if len(parts) < 2:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            if parts[0] == "/dewriter":
                parts[0] = "/debuilder"
            parts[0] = parts[0].replace("/de", "")
            parts = ["/derank", parts[1], parts[0]] + ([parts[2]] if len(parts) == 3 else [])
            self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "mod")
    @only_username_command
    @config("disabled_cmdblocks", True)
    def commandSpec(self, username, fromloc, overriderank):
        "/spec username - Mod\nMakes the user as a spec."
        self.client.sendServerMessage(Spec(self, username, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "mod")
    @only_username_command
    @config("disabled_cmdblocks", True)
    def commandDeSpec(self, username, fromloc, overriderank):
        "/unspec username - Mod\nAliases: despec\nRemoves the user as a spec."
        self.client.sendServerMessage(DeSpec(self, username, fromloc, overriderank))

    @config("category", "player")
    @config("rank", "op")
    @username_command
    def commandRespawn(self, user, fromloc, overriderank):
        "/respawn username - Mod\nRespawns the user."
        if not self.client.isMod() and (user.world.id != self.client.world.id):
            self.client.sendServerMessage("The user is not in your world.")
        else:
            user.respawn()
            user.sendServerMessage("You have been respawned by %s." % self.client.username)
            self.client.sendServerMessage("%s respawned." % user.username)

    @config("category", "player")
    @username_command
    def commandInvite(self, user, fromloc, overriderank):
        "/invite username - Guest\Invites a user to be where you are."
        # Shift the locations right to make them into block coords
        rx = self.client.x >> 5
        ry = self.client.y >> 5
        rz = self.client.z >> 5
        user.var_prefetchdata = (self.client, self.client.world)
        user.sendServerMessage("%s would like to fetch you%s." % (
        self.client.username, (("to %s" % self.client.world.id) if self.client.world.id == user.world.id else "")))
        user.sendServerMessage("Do you wish to accept? [y]es [n]o")
        user.var_fetchrequest = True
        user.var_fetchdata = (self.client, self.client.world, rx, ry, rz)
        self.client.sendServerMessage("The fetch request has been sent.")

    @config("category", "player")
    @config("rank", "op")
    @username_command
    def commandFetch(self, user, fromloc, overriderank):
        "/fetch username - Op\nAliases: bring\nTeleports a user to be where you are."
        # Shift the locations right to make them into block coords
        rx = self.client.x >> 5
        ry = self.client.y >> 5
        rz = self.client.z >> 5
        if user.world == self.client.world:
            user.teleportTo(rx, ry, rz)
        else:
            if self.client.isMod():
                user.changeToWorld(self.client.world.id, position=(rx, ry, rz))
            else:
                self.client.sendServerMessage("%s cannot be fetched from '%s'" % (self.client.username, user.world.id))
                return
        user.sendServerMessage("You have been fetched by %s" % self.client.username)

    @config("category", "player")
    @on_off_command
    def commandFly(self, onoff, fromloc, overriderank):
        "/fly on|off - Guest\nEnables or disables bad server-side flying"
        if onoff == "on":
            self.flying = True
            self.client.sendServerMessage("You are now flying.")
        else:
            self.flying = False
            self.client.sendServerMessage("You are no longer flying.")

    @config("category", "player")
    @on_off_command
    def commandTeleProtect(self, onoff, fromloc, overriderank):
        "/tpp on|off - Guest\nEnables or disables teleport protection\n(Stops non-staff from teleporting to you.)"
        if onoff == "on":
            self.client.settings["tpprotect"] = True
            self.client.data.set("misc", "tpprotect", "true")
            self.client.sendServerMessage("Teleport protection is now on.")
        else:
            self.client.settings["tpprotect"] = False
            self.client.data.set("misc", "tpprotect", "false")
            self.client.sendServerMessage("Teleport protection is now off.")

    @config("category", "world")
    def commandCoord(self, parts, fromloc, overriderank):
        "/goto x y z [h p] - Guest\nTeleports you to coords. NOTE: y is up."
        try:
            x = int(parts[1])
            y = int(parts[2])
            z = int(parts[3])
            try:
                try:
                    h = int(parts[4])
                    self.client.teleportTo(x, y, z, h)
                except:
                    p = int(parts[5])
                    self.client.teleportTo(x, y, z, h, p)
            except:
                self.client.teleportTo(x, y, z)
        except (IndexError, ValueError):
            self.client.sendServerMessage("Usage: /goto x y z [h p]")
            self.client.sendServerMessage("MCLawl users: /l worldname")

    @config("category", "player")
    @username_command
    def commandTeleport(self, user, fromloc, overriderank):
        "/tp username - Guest\nAliases: teleport\nTeleports you to the users location."
        try:
            x = user.x >> 5
            y = user.y >> 5
            z = user.z >> 5
        except AttributeError:
            self.client.sendServerMessage("That user seems to have went offline before the teleportation can finish.")
            return
        if (user.settings["tpprotect"] == True) and not self.client.isMod():
            self.client.sendServerMessage(
                "%s has teleport protection enabled - you cannot teleport to him/her." % user.username)
            return
        if user.world == self.client.world:
            self.client.teleportTo(x, y, z)
        else:
            if self.client.canEnter(user.world):
                self.client.changeToWorld(user.world.id, position=(x, y, z))
            else:
                self.client.sendServerMessage("Sorry, that world is private.")

    @only_username_command
    def commandLastseen(self, username, fromloc, overriderank):
        "/lastseen username - Guest\nTells you when 'username' was last seen."
        if username not in self.client.factory.lastseen:
            self.client.sendServerMessage("There are no records of %s." % username)
        else:
            t = time.time() - self.client.factory.lastseen[username]
            days = t // 86400
            hours = (t % 86400) // 3600
            mins = (t % 3600) // 60
            desc = "%id, %ih, %im" % (days, hours, mins)
            self.client.sendServerMessage("%s was last seen %s ago." % (username, desc))

    @username_command
    def commandLocate(self, user, fromloc, overriderank):
        "/locate username - Guest\nAliases: find\nTells you what world a user is in."
        self.client.sendServerMessage("%s is in %s" % (user.username, user.world.id))

    @config("category", "player")
    def commandWho(self, parts, fromloc, overriderank):
        "/who [username] - Guest\nAliases: pinfo, players, users, whois\nOnline users, or user lookup."
        if len(parts) < 2:
            self.client.sendServerMessage("Do '/who username' for more info.")
            self.client.sendServerMessage("Players: ")
            for key in self.client.factory.worlds:
                if len(self.client.factory.worlds[key].clients) > 0:
                    theList = [(key + ": ")]
                    for c in self.client.factory.worlds[key].clients:
                        user = str(c.username)
                        if self.client.factory.isSpectator(user):
                            user = COLOUR_BLACK + user
                        elif self.client.factory.isOwner(user):
                            user = COLOUR_GREEN + user
                        elif self.client.factory.isDirector(user):
                            user = COLOUR_DARKRED + user
                        elif self.client.factory.isAdmin(user):
                            user = COLOUR_RED + user
                        elif self.client.factory.isMod(user):
                            user = COLOUR_DARKBLUE + user
                        elif self.client.factory.isHelper(user):
                            user = COLOUR_DARKGREY + user
                        elif user in INFO_VIPLIST:
                            user = COLOUR_YELLOW + user
                        elif user == self.client.world.status["owner"].lower():
                            user = COLOUR_DARKYELLOW + user
                        elif user in self.client.world.ops:
                            user = COLOUR_DARKCYAN + user
                        elif user in self.client.world.builders:
                            user = COLOUR_CYAN + user
                        else:
                            user = COLOUR_WHITE + user
                        theList.append(user)
                    self.client.sendServerList(theList, plain=True)
        else:
            def loadBank():
                file = open('config/data/balances.dat', 'r')
                bank_dic = cPickle.load(file)
                file.close()
                return bank_dic

            def loadRank():
                file = open('config/data/titles.dat', 'r')
                rank_dic = cPickle.load(file)
                file.close()
                return rank_dic

            bank = loadBank()
            rank = loadRank()
            user = parts[1].lower()
            try:
                title = self.client.factory.usernames[user].title
            except:
                title = ""
            if parts[1].lower() in self.client.factory.usernames:
                # Parts is an array, always, so we get the first item.
                username = self.client.factory.usernames[parts[1].lower()]
                if self.client.isAdmin() or username.username.lower() == self.client.username.lower():
                    self.client.sendNormalMessage(
                        self.client.factory.usernames[user].userColour() + ("%s" % (title)) + parts[
                                                                                              1] + COLOUR_YELLOW + " " + username.world.id + " | " + str(
                            username.transport.getPeer().host))
                else:
                    self.client.sendNormalMessage(
                        self.client.factory.usernames[user].userColour() + ("%s" % (title)) + parts[
                                                                                              1] + COLOUR_YELLOW + " " + username.world.id)
                if hasattr(username, "gone"):
                    if username.gone == 1:
                        self.client.sendNormalMessage(COLOUR_DARKPURPLE + "is currently Away")
                if user in bank:
                    self.client.sendServerMessage("Balance: M%d" % (bank[user]))
            else:
                # Parts is an array, always, so we get the first item.
                username = parts[1].lower()
                self.client.sendNormalMessage(
                    self.client.userColour() + ("%s" % (title)) + parts[1] + COLOUR_DARKRED + " Offline")
                try:
                    t = time.time() - self.client.factory.lastseen[username]
                except:
                    return
                days = t // 86400
                hours = (t % 86400) // 3600
                mins = (t % 3600) // 60
                desc = "%id, %ih, %im" % (days, hours, mins)
                if username in self.client.factory.lastseen:
                    self.client.sendServerMessage("On %s ago" % desc)
                if user in bank:
                    self.client.sendServerMessage("Balance: M%s" % bank[user])

    @config("category", "player")
    @only_username_command
    @config("disabled_cmdblocks", True)
    def commandMute(self, username, fromloc, overriderank):
        "/mute username - Guest\nStops you hearing messages from 'username'."
        self.muted.add(username)
        self.client.sendServerMessage("%s muted." % username)

    @config("category", "player")
    @only_username_command
    def commandUnmute(self, username, fromloc, overriderank):
        "/unmute username - Guest\nLets you hear messages from this user again"
        if username in self.muted:
            self.muted.remove(username)
            self.client.sendServerMessage("%s unmuted." % username)
        else:
            self.client.sendServerMessage("%s wasn't muted to start with" % username)

    @config("category", "player")
    def commandMuted(self, username, fromloc, overriderank):
        "/muted - Guest\nLists people you have muted."
        if self.muted:
            self.client.sendServerList(["Muted:"] + list(self.muted))
        else:
            self.client.sendServerMessage("You haven't muted anyone.")

    @config("category", "player")
    def commandClearChat(self, parts, fromloc, overriderank):
        "/clearchat - Guest\nClears the chat screen."
        for i in range(2):
            for i in range(10):
                self.client.sendServerMessage("")