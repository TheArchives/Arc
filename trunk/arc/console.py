# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, threading, time, traceback

from twisted.internet.task import LoopingCall
from arc.constants import *
from arc.globals import *
from arc.logger import ColouredLogger

class Console(threading.Thread):
    def __init__(self, factory):
        threading.Thread.__init__(self)
        self.factory = factory
        self.logger = self.factory.logger
        self.stop = False
        self.username = "Console"

    def run(self):
        try:
            try:
                while not self.stop:
                    try:
                        line = sys.stdin.readline()
                    except:
                        return
                    message = line
                    if len(line) < 1:
                        return
                    message = sanitizeMessage(message, [MSGREPLACE["text_colour_to_game"], MSGREPLACE["escape_commands"]])
                    for character in message:
                        if not character.lower() in PRINTABLE:
                            message = message.replace(character, "*")
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
                                self.factory.sendMessageToAll(out, "world", user="Console", fromloc="console")
                    elif message.startswith("#"):
                        # It's an staff-only message.
                        if len(message) == 1:
                            self.sendServerMessage("Please include a message to send.")
                        else:
                            text = message[1:]
                            text = text[:len(text) - 1]
                            self.factory.sendMessageToAll(text, "staff", user="Console", fromloc="console")
                    else:
                        self.factory.sendMessageToAll(message[0:len(message) - 1], "chat", user="Console", client=None, colour=RANK_COLOURS["owner"], fromloc="console")
            except:
                self.logger.error(traceback.format_exc())
        finally:
            time.sleep(0.1)

    def sendServerMessage(self, message, user=None):
        print(message)

    sendSplitServerMessage = sendWorldMessage = sendPlainWorldMessage = sendNormalMessage = sendServerMessage

    def isSpectator(self):
        return False

    isSilenced = isSpectator

    def isRank(self):
        return True # The console is everything. Really.

    isBuilder = isOp = isWorldOwner = isHelper = isMod = isAdmin = isDirector = isOwner = allowedToBuild  = canBreakAdminBlocks = isRank

    def getBlockValue(self, value):
        # Try getting the block as a direct integer type.
        try:
            block = chr(int(value))
        except ValueError:
            # OK, try a symbolic type.
            try:
                block = chr(globals()['BLOCK_%s' % value.upper()])
            except KeyError:
                return None
        # Check the block is valid
        if ord(block) > 49:
            return None
        return block

    def send(self, *args, **kwargs):
        pass

    canBreakAdminBlocks = sendPacked = sendError = sendRankUpdate = respawn = sendBlock = sendPlayerPos = sendPlayerDir = sendNewPlayer = sendPlayerLeave = sendKeepAlive = sendOverload =\
        sendOverloadChunk = sendLevel = sendLevelStart = sendLevelChunk = endSendLevel = sendAllNew = sendWelcome = send

    def getBlbLimit(self):
        return -1

    def sendServerList(self, items, wrap_at=63, plain=False):
        done = " ".join(items)
        self.sendServerMessage(done)