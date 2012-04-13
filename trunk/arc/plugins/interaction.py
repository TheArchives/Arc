# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, math, random, traceback

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

class InteractionPlugin(object):
    "Commands for player interactions."
    name = "InteractionPlugin"
    commands = {
        "say": "commandSay",
        "me": "commandMe",
        "away": "commandAway",
        "slap": "commandSlap",
        "punch": "commandPunch",
        "roll": "commandRoll",
        "kill": "commandKill",
        "count": "commandCount",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "consoleLoaded": "gotConsole",
    }

    def gotClient(self, data):
        data["client"].num = 0
        data["client"].hasCountdown = False
        data["client"].gone = False

    def gotConsole(self):
        self.factory.console.num = 0
        self.factory.console.hasCountdown = False
        self.factory.console.gone = False

    def checkCount(self, client):
        if client.num == 0:
            client.sendPlainWorldMessage("&2[COUNTDOWN] GO!")
            client.hasCountdown = False
        else:
            client.num -= 1
            client.sendPlainWorldMessage("&2[COUNTDOWN] %s" % self.num)
            reactor.callLater(1, self.checkCount, client)

    @config("category", "player")
    @config("aliases", ["afk", "brb"])
    @config("usage", "reason")
    def commandAway(self, data):
        "Prints out message of you going away. Toggle."
        if data["client"].gone:
            self.factory.sendMessageToAll("is now %sback." % COLOUR_DARKGREEN, "action", data["client"], user=data["client"].username, fromloc=data["fromloc"])
            data["client"].gone = False
        else:
            self.factory.sendMessageToAll("has gone AFK. %s" % 
                    (("(%s)" % " ".join(data["parts"][1:])) if len(data["parts"]) > 1 else ""), "action", data["client"], user=data["client"].username, fromloc=data["fromloc"])
            data["client"].gone = True

    @config("category", "player")
    def commandMe(self, data):
        "Prints 'username action'"
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please type an action.")
            return
        if data["client"].isSilenced():
            data["client"].sendServerMessage("You are Silenced and lost your tongue.")
        else:
            self.factory.sendMessageToAll(" ".join(data["parts"][1:]), "action", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("rank", "mod")
    @config("aliases", ["msg"])
    @config("usage", "message")
    def commandSay(self, data):
        "Prints out message in the server color."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please type a message.")
        else:
            self.factory.sendMessageToAll(COLOUR_YELLOW + " ".join(data["parts"][1:]), "server", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("category", "player")
    @config("usage", "username [with object")
    def commandSlap(self, data):
        "Slaps a user [with object]."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please enter the name for the slappee.")
            return
        stage = 0
        name = ""
        object = ""
        for i in range(1, len(data["parts"])):
            if data["parts"][i] == "with":
                stage = 1
                continue
            if stage == 0:
                name += data["parts"][i]
                if (i + 1 != len(data["parts"]) ):
                    if (data["parts"][i + 1] != "with"):
                        name += " "
                else:
                    object += data["parts"][i]
                    if (i != len(data["parts"]) - 1):
                        object += " "
            else:
                self.factory.sendMessageToAll("slaps %s with %s!" % 
                    (name, (object if stage == 1 else "a giant smelly trout")), "action", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("category", "player")
    @config("usage", "user [bodypart to punch]")
    def commandPunch(self, data):
        "Punchcs a user [in a bodypart]."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please enter the name for the punchee.")
        stage = 0
        name = ""
        object = ""
        for i in range(1, len(data["parts"])):
            if data["parts"][i] == "by":
                stage = 1
                continue
            if stage == 0:
                name += data["parts"][i]
                if (i + 1 != len(data["parts"])):
                    if (data["parts"][i + 1] != "by"):
                        name += " "
                else:
                    object += data["parts"][i]
                    if (i != len(data["parts"]) - 1):
                        object += " "
            else:
                self.factory.sendMessageToAll("punches %s in the %s!" %
                    (name, (object if stage == 1 else "face")), "action", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("rank", "mod")
    @config("usage", "user [reason]")
    @config("disable-on", ["cmdblock"])
    def commandKill(self, data):
        "Kills the user [with a reason]."
        killer = data["client"].username
        if user not in self.factory.usernames:
            data["client"].sendServerMessage("That user is not online.")
            return
        else:
            user = self.factory.usernames[data["parts"][1]]
        user.teleportTo(user.world.spawn[0], user.world.spawn[1], user.world.spawn[2], user.world.spawn[3])
        if killer == user.username:
            user.sendServerMessage("You have died.")
            self.factory.sendMessageToAll("%s%s has died." % (COLOUR_DARKRED, data["client"].username), "server",
                data["client"], user=data["client"].username, fromloc=data["fromloc"])
        else:
            user.sendServerMessage("You have been killed by %s." % data["client"].username)
            self.factory.sendMessageToAll("%s%s has been killed by %s." % 
                (COLOUR_DARKRED, user.username, data["client"].username), "server", data["client"], user=data["client"].username, fromloc=data["fromloc"])
            if len(data["parts"]) > 2:
                self.factory.sendMessageToAll("%sReason: %s" % (COLOUR_DARKRED, " ".join(data["parts"][2:])), "server", data["client"], user=data["client"].username, fromloc=data["fromloc"])

    @config("usage", "max")
    def commandRoll(self, data):
        "Rolls a random number from 1 to max. Announces to world."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please enter a number as the maximum roll.")
            return
        try:
            roll = int(math.floor((random.random() * (int(data["parts"][1]) - 1) + 1)))
        except ValueError:
            data["client"].sendServerMessage("Please enter an integer as the maximum roll.")
        else:
            data["client"].sendWorldMessage("%s rolled a %s" % (data["client"].username, roll))

    @config("rank", "builder")
    @config("usage", "[number]")
    @config("aliases", ["countdown"])
    def commandCount(self, data):
        "Counts down from 3 or from number given"
        if data["client"].hasCountdown:
            data["client"].sendServerMessage("You can only have one count at a time.")
            return
        if len(data["parts"]) > 1:
            try:
                data["client"].num = int(data["parts"][1])
            except ValueError:
                data["client"].sendServerMessage("Number must be an integer!")
                return
        else:
            data["client"].num = 3
        data["client"].hasCountdown = True
        data["client"].sendPlainWorldMessage("&2[COUNTDOWN] %s" % data["client"].num)
        reactor.callLater(1, self.checkCount, data["client"])

serverPlugin = InteractionPlugin