# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, threading, time, traceback

from twisted.internet.task import LoopingCall
from arc.constants import *
from arc.globals import *
from arc.logger import ColouredLogger

class StdinPlugin(threading.Thread):
    def __init__(self, factory):
        threading.Thread.__init__(self)
        self.factory = factory
        self.logger = self.factory.logger
        self.stop = False

    def run(self):
        try:
            try:
                while not self.stop:
                    try:
                        line = sys.stdin.readline()
                    except:
                        return
                    message = line
                    if len(line) > 1:
                        for character in message:
                            if not character.lower() in PRINTABLE:
                                message = message.replace("&0", "&0")
                                message = message.replace("&1", "&1")
                                message = message.replace("&2", "&2")
                                message = message.replace("&3", "&3")
                                message = message.replace("&4", "&4")
                                message = message.replace("&5", "&5")
                                message = message.replace("&6", "&6")
                                message = message.replace("&7", "&7")
                                message = message.replace("&8", "&8")
                                message = message.replace("&9", "&9")
                                message = message.replace("&a", "&a")
                                message = message.replace("&b", "&b")
                                message = message.replace("&c", "&c")
                                message = message.replace("&d", "&d")
                                message = message.replace("&e", "&e")
                                message = message.replace("&f", "&f")
                                message = message.replace(character, "*")
                        message = message.replace("%0", "&0")
                        message = message.replace("%1", "&1")
                        message = message.replace("%2", "&2")
                        message = message.replace("%3", "&3")
                        message = message.replace("%4", "&4")
                        message = message.replace("%5", "&5")
                        message = message.replace("%6", "&6")
                        message = message.replace("%7", "&7")
                        message = message.replace("%8", "&8")
                        message = message.replace("%9", "&9")
                        message = message.replace("%a", "&a")
                        message = message.replace("%b", "&b")
                        message = message.replace("%c", "&c")
                        message = message.replace("%d", "&d")
                        message = message.replace("%e", "&e")
                        message = message.replace("%f", "&f")
                        message = message.replace("./", " /")
                        message = message.replace(".!", " !")
                        message = message.replace(".@", " @")
                        message = message.replace(".#", " #")
                        if message[len(message) - 3] == "&":
                            self.sendServerMessage("You cannot use a color at the end of a message.")
                            return
                        if message.startswith("/"):
                            message = message.split(" ")
                            message[0] = message[0][1:]
                            message[len(message) - 1] = message[len(message) - 1][:len(message[len(message) - 1]) - 1]
                            self.factory.runCommand(message[0], message, "console", True, client=self)
                        elif message.startswith("@"):
                            # It's a whisper
                            try:
                                username, text = message[1:].strip().split(" ", 1)
                            except ValueError:
                                self.sendServerMessage("Please include a username and a message to send.")
                            else:
                                username = username.lower()
                                if username in self.factory.usernames:
                                    self.factory.usernames[username].sendWhisper(self.username, text)
                                    self.factory.logger.info("Console to %s: %s" % (username, text))
                                    self.factory.chatlogs["whisper"].write(
                                            {"self": "Console", "other": username, "text": text})
                                    self.factory.chatlogs["main"].write(
                                            {"self": "Console", "other": username, "text": text},
                                        formatter=MSGLOGFORMAT["whisper"])
                                else:
                                    self.sendServerMessage("%s is currently offline." % username)
                        elif message.startswith("!"):
                            # It's a world message.
                            if len(message) < 2:
                                self.sendServerMessage("Please include a message and a world to send to.")
                            else:
                                world, out = message[1:len(message) - 1].split(" ")
                                if world not in self.factory.worlds.keys():
                                    self.sendServerMessage("World %s is not booted." % world)
                                else:
                                    self.factory.sendMessageToAll(out, "world", user="Console")
                        elif message.startswith("#"):
                            # It's an staff-only message.
                            if len(message) == 1:
                                self.sendServerMessage("Please include a message to send.")
                            else:
                                text = message[1:]
                                text = text[:len(text) - 1]
                                self.factory.sendMessageToAll(text, "staff", user="Console")
                        else:
                            self.factory.sendMessageToAll(message[0:len(message) - 1], "chat", user="Console")
            except:
                self.logger.error(traceback.format_exc())
        finally:
            time.sleep(0.1)

    def sendServerMessage(self, message, user=None):
        print(message)

    sendSplitServerMessage = sendWorldMessage = sendPlainWorldMessage = sendNormalMessage = sendServerMessage

    def isSpectator():
        return False

    def isRank():
        return True # The console is everything. Really.

    isSpectator = isBuilder = isOp = isWorldOwner = isHelper = isMod = isAdmin = isDirector = isOwner = AllowedToBuild = canBreakAdminBlocks = isRank

    def GetBlockValue(self, block):
        return None

    def send(self, *args, **kwargs):
        pass

    canBreakAdminBlocks = sendPacked = sendError = sendRankUpdate = respawn = sendBlock = sendPlayerPos = sendPlayerDir = sendNewPlayer = sendPlayerLeave = sendKeepAlive = sendOverload =\
        sendOverloadChunk = sendLevel = sendLevelStart = sendLevelChunk = endSendLevel = sendAllNew = sendWelcome = send

    def getBlbLimit(self):
        return 0