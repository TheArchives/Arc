# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle

from arc.constants import *
from arc.decorators import *

class ModUtilPlugin(object):
    commands = {
        "u": "commandUrgent",

        "banish": "commandBanish",
        "worldban": "commandWorldBan",
        "unworldban": "commandUnWorldban",
        "worldbanned": "commandWorldBanned",

        "ban": "commandBan",
        "banb": "commandBanBoth",
        "ipban": "commandIpban",
        "ipreason": "commandIpreason",
        "kick": "commandKick",
        "banreason": "commandReason",
        "unban": "commandUnban",
        "unipban": "commandUnipban",
        "banned": "commandBanned",
        "freeze": "commandFreeze",
        "unfreeze": "commandUnFreeze",

        "hide": "commandHide",

        "overload": "commandOverload",
        "send": "commandSend",

        "spectate": "commandSpectate",

        "silence": "commandSilence",
        "desilence": "commandDesilence",
        "silenced": "commandSilenced",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "playerpos": "playerMoved",
        "poschange": "posChanged",
        }

    def gotClient(self, data):
        data["client"].hidden = False
        data["client"].spectating = False

    def playerMoved(self, data):
        "Stops transmission of user positions if hide is on."
        if data["client"].hidden: return False

    def posChanged(self, data):
        "Hook trigger for when the user moves"
        for uid in self.factory.clients:
            user = self.factory.clients[uid]
            if user.spectating == data["client"].id:
                if user.x != data["x"] and user.y != data["y"] and user.z != data["z"]:
                    user.teleportTo(data["x"] >> 5, data["y"] >> 5, data["z"] >> 5, data["h"], data["p"])

    @config("rank", "admin")
    @config("aliases", ["urgent"])
    @config("usage", "message")
    def commandUrgent(self, data):
        "Prints out message in the server color."
        if len(parts) == 1:
            data["client"].sendServerMessage("Please type a message.")
            return
        self.factory.sendMessageToAll("%s[URGENT] %s" % (COLOUR_DARKRED, " ".join(parts[1:])), "server", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("category", "player")
    @config("rank", "op")
    def commandWorldBanned(self, data):
        "Shows who is WorldBanned."
        if len(data["client"].world.worldbans.keys()):
            data["client"].sendServerList(["WorldBanned:"] + data["client"].world.worldbans.keys())
        else:
            data["client"].sendServerMessage("WorldBanned: No one.")

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["banish"])
    @config("disabled-on", ["cmdblock"])
    def commandBanish(self, data):
        "Banishes the user to the default world."
        if data["parts"] < 2:
            data["client"].sendServerMessage("Usage: /worldkick username")
            return
        user = self.factory.usernames[data["parts"][1]]
        if user.isWorldOwner() and not data["client"].isMod():
            if user.isMod():
                data["client"].sendServerMessage("You can't WorldKick a staff!")
            else:
                data["client"].sendServerMessage("You can't WorldKick the world owner!")
            return
        if user.world == data["client"].world:
            user.sendServerMessage("You were WorldKicked from '%s'." % user.world.id)
            user.changeToWorld("default")
            data["client"].sendServerMessage("User %s got WorldKicked." % user.username)
        else:
            data["client"].sendServerMessage("% is in another world!" % user.username)

    @config("category", "player")
    @config("rank", "op")
    @config("usage", "username")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandWorldBan(self, data):
        "WorldBan a user from this world."
        if data["parts"] < 2:
            data["client"].sendServerMessage("Usage: /worldkick username")
            return
        username = data["parts"][1]
        if data["client"].world.isWorldBanned(username):
            data["client"].sendServerMessage("%s is already WorldBanned." % username)
        elif username == data["client"].world.status["owner"].lower():
            data["client"].sendServerMessage("You can't WorldBan the world owner!")
        elif self.factory.isHelper(username):
            data["client"].sendServerMessage("You can't WorldBan a staff!")
        else:
            data["client"].world.add_worldban(username)
            if username in self.factory.usernames:
                if self.factory.usernames[username].world == data["client"].world:
                    self.factory.usernames[username].changeToWorld("default")
                    self.factory.usernames[username].sendServerMessage("You got WorldBanned!")
            data["client"].sendServerMessage("%s has been WorldBanned." % username)

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["deworldban"])
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandUnWorldban(self, data):
        "Removes the WorldBan on the user."
        if not data["client"].world.isWorldBanned(username):
            data["client"].sendServerMessage("%s is not WorldBanned." % username)
        else:
            data["client"].world.delete_worldban(username)
            data["client"].sendServerMessage("%s was UnWorldBanned." % username)

    @config("category", "player")
    @config("rank", "op")
    @config("aliases", ["cloak"])
    def commandHide(self, data):
        "Hides you so no other users can see you. Toggle."
        if not data["client"].hidden:
            data["client"].sendServerMessage("You have vanished.")
            data["client"].hidden = True
            # Send the "user has disconnected" command to people
            data["client"].queueTask(TASK_PLAYERLEAVE, [data["client"].id])
        else:
            data["client"].sendServerMessage("That was Magic!")
            data["client"].hidden = False
            # Imagine that! They've mysteriously appeared.
            data["client"].queueTask(TASK_NEWPLAYER,
                [data["client"].id, data["client"].username, data["client"].x, data["client"].y, data["client"].z, data["client"].h,
                 data["client"].p])

    @config("category", "player")
    @config("rank", "mod")
    def commandBanned(self, data):
        "Shows who is Banned."
        if len(self.factory.banned.keys()):
            data["client"].sendServerList(["Banned:"] + self.factory.banned.keys())
        else:
            data["client"].sendServerMessage("Banned: No one.")

    @config("category", "player")
    @config("rank", "helper")
    def commandSilenced(self, data):
        "Lists all Silenced players."
        if len(self.factory.silenced):
            data["client"].sendServerList(["Silenced:"] + list(self.factory.silenced))
        else:
            data["client"].sendServerMessage("Silenced: No one.")

    @config("category", "player")
    @config("rank", "helper")
    @config("usage", "username [reason]")
    @username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandKick(self, data):
        "Kicks the user off the server."
        username = user.username
        if data["parts"] > 1:
            user.sendError("Kicked by %s: %s" % (data["client"].username, " ".join(data["parts"][1:])))
        else:
            user.sendError("You got kicked by %s." % data["client"].username)
        data["client"].sendServerMessage("User %s kicked." % username)

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username reason")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandBanBoth(self, data):
        "Name and IP ban a user from this server."
        if len(data["parts"]) <= 2:
            data["client"].sendServerMessage("Please specify a username and a reason.")
            return
        # Grab statistics
        username = data["parts"][1].lower()
        if username not in self.factory.usernames:
            noIP = True
        else:
            noIP = False
            ip = self.factory.usernames[username].transport.getPeer().host
        # Region ban
        if self.factory.isBanned(username):
            data["client"].sendServerMessage("%s is already banned." % username)
        else:
            self.factory.addBan(username, " ".join(data["parts"][2:]), data["client"].username)
            data["client"].sendServerMessage("Player %s banned. Continuing to IPBan..." % username)
        # Region IPBan
        if not noIP:
            if self.factory.isIpBanned(ip):
                data["client"].sendServerMessage("%s is already IPBanned." % ip)
                return
            else:
                data["client"].sendServerMessage("%s has been IPBanned." % ip)
                self.factory.addIpBan(ip, " ".join(data["parts"][2:]))
        else:
            data["client"].sendServerMessage("User %s is not online, unable to IPBan." % username)
        # Follow-up action
        if username in self.factory.usernames:
            self.factory.usernames[username].sendError("You got IPbanned by %s: %s" % (data["client"].username, " ".join(data["parts"][2:])))

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username reason")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandBan(self, data):
        "Bans the player from this server."
        if len(data["parts"]) <= 2:
            data["client"].sendServerMessage("Please specify a username and a reason.")
            return
        username = data["parts"][1]
        if self.factory.isBanned(username):
            data["client"].sendServerMessage("%s is already banned." % username)
            return
        self.factory.addBan(username, " ".join(data["parts"][2:]), data["client"].username)
        if username in self.factory.usernames:
            self.factory.usernames[username].sendError("You got banned by %s: %s" % (data["client"].username, " ".join(data["parts"][2:])))
        data["client"].sendServerMessage("%s has been banned for %s." % (username, " ".join(data["parts"][2:])))

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username reason")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandIpban(self, data):
        "Ban a user's IP from this server."
        if data["parts"][1].lower() not in self.factory.usernames:
            data["client"].sendServerMessage("Sorry, that user is not online.")
            return
        username = data["parts"][1].lower()
        ip = self.factory.usernames[username].ip
        if self.factory.isIpBanned(ip):
            data["client"].sendServerMessage("%s is already IPBanned." % ip)
            return
        if len(data["parts"]) <= 2:
            data["client"].sendServerMessage("Please specify a username and a reason.")
            return
        data["client"].sendServerMessage("%s has been IPBanned." % ip)
        self.factory.addIpBan(ip, " ".join(data["parts"][2:]))
        self.factory.usernames[username].sendError("You got IPbanned by %s: %s" % (data["client"].username, " ".join(data["parts"][2:])))

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandUnban(self, data):
        "Removes the ban on the user."
        if not self.factory.isBanned(data["parts"][1]):
            data["client"].sendServerMessage("%s is not banned." % data["parts"][1])
        else:
            self.factory.removeBan(data["parts"][1])
            data["client"].sendServerMessage("%s has been unbanned." % data["parts"][1])

    @config("category", "player")
    @config("rank", "admin")
    @only_string_command("IP")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandUnipban(self, data):
        "Removes the ban on the IP."
        if not self.factory.isIpBanned(data["parts"][1]):
            data["client"].sendServerMessage("%s is not Banned." % data["parts"][1])
        else:
            self.factory.removeIpBan(data["parts"][1])
            data["client"].sendServerMessage("%s UnBanned." % data["parts"][1])

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandReason(self, data):
        "Gives the reason a user was Banned."
        if not self.factory.isBanned(data["parts"][1]):
            data["client"].sendServerMessage("%s is not Banned." % data["parts"][1])
        else:
            data["client"].sendServerMessage("Reason: %s" % self.factory.banReason(data["parts"][1]))

    @config("category", "player")
    @config("rank", "admin")
    @config("usage", "IP")
    @only_string_command("IP")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandIpreason(self, data):
        "Gives the reason an IP was Banned."
        if not self.factory.isIpBanned(data["parts"][1]):
            data["client"].sendServerMessage("%s is not Banned." % data["parts"][1])
        else:
            data["client"].sendServerMessage("Reason: %s" % self.factory.ipBanReason(data["parts"][1]))

    @config("category", "player")
    @config("rank", "mod")
    @config("aliases", ["defreeze", "unstop"])
    @config("usage", "username")
    @username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandUnFreeze(self, data):
        "Unfreezes the user."
        if not data["user"].frozen:
            data["client"].sendServerMessage("User is not frozen.")
            return
        data["user"].frozen = False
        data["user"].sendNormalMessage("&4You have been unfrozen by %s!" % data["client"].username)

    @config("category", "player")
    @config("rank", "mod")
    @config("aliases", ["stop"])
    @config("usage", "username")
    @username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandFreeze(self, data):
        "Freezes the user."
        if data["user"].frozen:
            data["client"].sendServerMessage("User is already frozen.")
            return
        data["user"].frozen = True
        data["user"].sendNormalMessage("&4You have been frozen by %s!" % data["client"].username)

    @config("category", "player")
    @config("rank", "admin")
    @config("usage", "username")
    @username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandOverload(self, data):
        "Sends the users client a massive fake world."
        data["user"].sendOverload()
        data["client"].sendServerMessage("Overload sent to %s." % data["user"].username)

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username world")
    @username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandSend(self, data):
        "Sends the users client to another world."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Pleasey specify the username and the world.")
            return
        world_id = parts[2]
        if not self.factory.world_exists(world_id):
            data["client"].sendServerMessage("That world does not exist.")
            return
        username = data["parts"][1]
        if username not in self.factory.usernames:
            data["client"].sendServerMessage("User %s is not online." % username)
            return
        user = self.factory.usernames[username]
        if user.isMod() and not data["client"].isMod():
            data["client"].sendServerMessage("You cannot send staff!")
            return
        user.changeToWorld(world_id)
        user.sendServerMessage("You were sent to %s by %s." % (world_id, data["client"].username))
        data["client"].sendServerMessage("User %s was sent to world %s." % (username, world_id))

    @config("category", "player")
    @config("rank", "mod")
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandSilence(self, data):
        "Disallows the user to talk."
        if self.factory.isMod(data["parts"][1]):
            data["client"].sendServerMessage("You cannot silence staff!")
            return
        self.factory.silenced.add(data["parts"][1])
        data["client"].sendServerMessage("%s is now silenced." % data["parts"][1])

    @config("category", "player")
    @config("rank", "mod")
    @config("aliases", ["unsilence"])
    @config("usage", "username")
    @only_username_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandDesilence(self, data):
        "Allows a silenced user to talk again."
        if self.factory.isSilenced(data["parts"][1]):
            self.factory.silenced.remove(data["parts"][1])
            data["client"].sendServerMessage("%s is no longer silenced." % data["parts"][1].lower())
        else:
            data["client"].sendServerMessage("User specified is not silenced.")

    @config("rank", "op")
    @config("category", "player")
    @config("aliases", ["follow", "watch"])
    @config("usage", "user")
    @username_command
    def commandSpectate(self, data):
        "Follows specified user around."
        nospec_check = True
        try:
            getattr(data["client"], "spectating")
        except AttributeError:
            nospec_check = False
        if not nospec_check or data["client"].spectating != data["user"].id:
            data["client"].sendServerMessage("You are now spectating %s" % data["user"].username)
            data["client"].spectating = data["user"].id
        else:
            data["client"].sendServerMessage("You are no longer spectating %s" % data["user"].username)
            data["client"].spectating = False

serverPlugin = ModUtilPlugin