# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, math, random, traceback

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class InteractionPlugin(ProtocolPlugin):
    "Commands for player interactions."

    commands = {
        "say": "commandSay",
        "msg": "commandSay",
        "me": "commandMe",
        "away": "commandAway",
        "afk": "commandAway",
        "brb": "commandAway",
        "back": "commandBack",
        "slap": "commandSlap",
        "punch": "commandPunch",
        "roll": "commandRoll",
        "kill": "commandKill",

        "count": "commandCount",
        "countdown": "commandCount",

        "s": "commandSendMessage",
        "sendmessage": "commandSendMessage",
        "inbox": "commandCheckMessages",
        "c": "commandClear",
        "clear": "commandClear",
        "clearinbox": "commandClear",
    }

    def gotClient(self):
        self.num = 0
        self.hasCountdown = False
        self.gone = False

    def checkCount(self):
        if self.num == 0:
            self.client.sendPlainWorldMessage("&2[COUNTDOWN] GO!")
            self.hasCountdown = False
        else:
            self.num -= 1
            self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" % self.num)
            reactor.callLater(1, self.checkCount)

    @config("category", "player")
    def commandBack(self, parts, fromloc, overriderank):
        "/back - Guest\nPrints out message of you coming back."

    @config("category", "player")
    def commandAway(self, parts, fromloc, overriderank):
        "/away reason - Guest\nAliases: afk, brb\nPrints out message of you going away. Toggle."
        if self.gone:
            self.client.factory.sendMessageToAll("is now %sback." % (COLOUR_DARKGREEN), "action", self.client)
            self.gone = False
        else:
            self.client.factory.sendMessageToAll("has gone AFK. %s" % (("(%s)" % " ".join(parts[1:])) if len(parts) > 1 else ""), "action", self.client)
            self.gone = True

    @config("category", "player")
    def commandMe(self, parts, fromloc, overriderank):
        "/me action - Guest\nPrints 'username action'"
        if len(parts) == 1:
            self.client.sendServerMessage("Please type an action.")
        else:
            if self.client.isSilenced():
                self.client.sendServerMessage("You are Silenced and lost your tongue.")
            else:
                self.client.factory.sendMessageToAll(" ".join(parts[1:]), "action", self.client)

    @config("rank", "mod")
    def commandSay(self, parts, fromloc, overriderank):
        "/say message - Mod\nAliases: msg\nPrints out message in the server color."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.sendMessageToAll(COLOUR_YELLOW+" ".join(parts[1:]), "server", self.client)

    @config("category", "player")
    def commandSlap(self, parts, fromloc, overriderank):
        "/slap username [with object] - Guest\nSlap username [with object]."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter the name for the slappee.")
        else:
            stage = 0
            name = ""
            object = ""
            for i in range(1, len(parts)):
                if parts[i] == "with":
                    stage = 1
                    continue
                    if stage == 0 :
                        name += parts[i]
                        if (i+1 != len(parts) ) :
                            if (parts[i+1] != "with"):
                                name += " "
                    else:
                        object += parts[i]
                        if (i != len(parts)-1):
                            object += " "
                else:
                    self.client.factory.sendMessageToAll("slaps %s with %s!" % (name, (object if stage == 1 else "a giant smelly trout")), "action", self.client)

    @config("category", "player")
    def commandPunch(self, parts, fromloc, overriderank):
        "/punch username [bodypart to punch] - Punch username [in a bodypart]."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter the name for the punchee.")
        else:
            stage = 0
            name = ""
            object = ""
            for i in range(1, len(parts)):
                if parts[i] == "by":
                    stage = 1
                    continue
                    if stage == 0 :
                        name += parts[i]
                        if (i+1 != len(parts)):
                            if (parts[i+1] != "by"):
                                name += " "
                    else:
                        object += parts[i]
                        if (i != len(parts)-1):
                            object += " "
                else:
                    self.client.factory.sendMessageToAll("punches %s in the %s!" % (name, (object if stage == 1 else "face")), "action", self.client)

    @config("rank", "mod")
    @username_command
    @config("disabled_cmdblocks", True)
    def commandKill(self, user, fromloc, overriderank, params=[]):
        "/kill username [reason] - Mod\nKills the user for reason (optional)."
        killer = self.client.username
        user.teleportTo(user.world.spawn[0], user.world.spawn[1], user.world.spawn[2], user.world.spawn[3])
        if killer == user.username:
            user.sendServerMessage("You have died.")
            self.client.factory.sendMessageToAll("%s%s has died." % (COLOUR_DARKRED, self.client.username), "server", self.client)
        else:
            user.sendServerMessage("You have been killed by %s." % self.client.username)
            self.client.factory.sendMessageToAll("%s%s has been killed by %s." % (COLOUR_DARKRED, user.username, self.client.username), "server", self.client)
            if params:
                self.client.factory.sendMessageToAll("%sReason: %s" % (COLOUR_DARKRED, " ".join(params)), "server", self.client)

    def commandRoll(self, parts, fromloc, overriderank):
        "/roll max - Guest\nRolls a random number from 1 to max. Announces to world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter a number as the maximum roll.")
        else:
            try:
                roll = roll = int(math.floor((random.random() * (int(parts[1])-1)+1)))
            except ValueError:
                self.client.sendServerMessage("Please enter an integer as the maximum roll.")
            else:
                self.client.sendWorldMessage("%s rolled a %s" % (self.client.username, roll))

    @config("rank", "builder")
    def commandCount(self, parts, fromloc, overriderank):
        "/count [number] - Builder\nAliases: countdown\nCounts down from 3 or from number given"
        if self.hasCountdown:
            self.client.sendServerMessage("You can only have one count at a time!")
            return
        if len(parts) > 1:
            try:
                self.num = int(parts[1])
            except ValueError:
                self.client.sendServerMessage("Number must be an integer!")
                return
        else:
            self.num = 3
        self.hasCountdown = True
        self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" % self.num)
        reactor.callLater(1, self.checkCount)

    def commandSendMessage(self,parts, fromloc, overriderank):
        "/s username message - Guest\nAliases: sendmessage\nSends an message to the users Inbox."
        if len(parts) < 3:
            self.client.sendServerMessage("You must provide a username and a message.")
        else:
            try:
                from_user = self.client.username
                to_user = parts[1]
                if to_user in messages:
                    messages[to_user]+= "\n" + from_user + ": " + mess
                else:
                    messages[to_user] = from_user + ": " + mess
                file = open('config/data/inbox.dat', 'w')
                cPickle.dump(messages, file)
                file.close()
                self.client.factory.usernames[to_user].MessageAlert()
                self.client.sendServerMessage("A message has been sent to %s." % to_user)
            except:
                self.client.sendServerMessage("Error sending message.")

    def commandCheckMessages(self, parts, fromloc, overriderank):
        "/inbox [mode] - Guest\nChecks your inbox of messages.\nModes: NEW, ALL"
        file = open('config/data/inbox.dat', 'r')
        messages = cPickle.load(file)
        file.close()
        if self.client.username.lower() in messages:
            self.client._sendMessage(COLOUR_DARKPURPLE, messages[self.client.username.lower()])
            self.client.sendServerMessage("NOTE: Might want to do /c now.")
        else:
            self.client.sendServerMessage("You do not have any messages.")

#    def commandCheckMessages_DOESNOTWORK(self, parts, fromloc, overriderank):
#        "/inbox [mode] - Guest\nChecks your inbox of messages.\nModes: NEW, ALL"
#        if len(parts) > 0:
#            if parts[1].lower() in ["new", "all"]:
#                selection = parts[1].lower()
#            else:
#                self.client.sendServerMessage("Mode %s not recongized. Using 'all' instead." % parts[1].lower())
#                selection = "all"
#        else:
#            selection = "all"
#        entries = self.client.factory.serverPlugins["OfflineMessageServerPlugin"].getMessages(self.client.username, "to")
#        if entries == False:
#            self.client.sendServerMessage("You do not have any messages in your inbox.")
#            return
#        else:
#            for entry in entries:
#                id, from_user, to_user, message, date, status = entry
#                if status == STATUS_UNREAD and selection in ["new", "all"]:
#                    meetCriteria = True
#                elif status == STATUS_READ and selection == "all":
#                    meetCriteria = True
#                else:
#                    meetCriteria = False
#                if meetCriteria:
#                    self.client.sendServerMessage("Message sent by %s at %s: (ID: %s)" % (from_user, date, id))
#                    self.client.sendSplitServerMessage(message)
#                    self.client.sendServerMessage("------------------")

    def commandClear(self,parts, fromloc, overriderank):
        "/c - Guest\nAliases: clear, clearinbox\nClears your Inbox of messages."
        target = self.client.username
        if len(parts) == 2:
            target = parts[1]
        elif self.client.username.lower() not in self.client.factory.messages:
            self.client.sendServerMessage("You have no messages to clear.")
            return False
        self.client.factory.messages.pop(target)
        file = open('config/data/inbox.dat', 'w')
        cPickle.dump(messages, file)
        file.close()
        self.client.sendServerMessage("All your messages have been deleted.")