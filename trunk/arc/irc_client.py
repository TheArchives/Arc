# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cmath, datetime, random, sys, time, traceback

from twisted.internet import protocol
from twisted.words.protocols import irc
from twisted.words.protocols.irc import IRC

from arc.constants import *
from arc.decorators import *
from arc.globals import *
from arc.logger import ColouredLogger

debug = (True if "--debug" in sys.argv else False)

class ChatBot(irc.IRCClient):
    """An IRC-server chat integration bot."""

    def connectionMade(self):
        self.logger = ColouredLogger(debug)
        self.ops = []
        self.nickname = self.factory.main_factory.irc_nick
        self.password = self.factory.main_factory.irc_pass
        irc.IRCClient.connectionMade(self)
        self.factory.instance = self
        self.factory, self.irc_factory = self.factory.main_factory, self.factory
        self.world = None
        self.sendLine('NAMES ' + self.factory.irc_channel)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.info("IRC client disconnected. (%s)" % reason)

    # callbacks for events

    def ctcpQuery_VERSION(self, user, channel, data):
        """Called when received a CTCP VERSION request."""
        nick = user.split("!")[0]
        self.ctcpMakeReply(nick, [('VERSION', 'The Archives %s - a Minecraft server written in Python.' % VERSION)])

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.logger.info("IRC client connected.")
        self.msg("NickServ", "IDENTIFY %s %s" % (self.nickname, self.password))
        self.msg("ChanServ", "INVITE %s" % self.factory.irc_channel)
        self.join(self.factory.irc_channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.info("IRC client joined %s." % channel)

    def sendError(self, error):
        self.logger.error("Sending error: %s" % error)
        self.sendPacked(TYPE_ERROR, error)
        reactor.callLater(0.2, self.transport.loseConnection)

    def lineReceived(self, line): # use instead of query
        line = irc.lowDequote(line)
        try:
            prefix, command, params = irc.parsemsg(line)
            if irc.numeric_to_symbolic.has_key(command):
                command = irc.numeric_to_symbolic[command]
            self.handleCommand(command, prefix, params)
        except irc.IRCBadMessage:
            self.badMessage(line, *sys.exc_info())
        try:
            if command == "RPL_NAMREPLY":
                names = params[3].split()
                for name in names:
                    if name.startswith("@"):
                        self.ops.append(name[1:])
        except:
            self.logger.error(traceback.format_exc())

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        try:
            user = user.split('!', 1)[0]
            if channel == self.nickname:
                if not (self.nickname == user or "Serv" in user):
                    msg_command = msg.split()
                    self.factory.runCommand(msg_command[0], msg_command, "irc_query", (True if user in self.ops else False), client=self, username=user)
            elif channel.lower() == self.factory.irc_channel.lower():
                if msg.lower().lstrip(self.nickname.lower()).startswith("$" + self.nickname.lower()):
                    msg_command = msg.split()
                    msg_command[1] = msg_command[1].lower()
                    self.factory.runCommand(msg_command[1], msg_command, "irc", (True if user in self.ops else False), client=self)
                elif msg.startswith("$"):
                    self.logger.info("<$%s> %s" % (user, msg))
                elif msg.startswith("!"):
                    # It's a world message.
                    message = msg.split(" ")
                    if len(message) == 1:
                        self.msg(self.factory.irc_channel, "Please include a message to send.")
                    else:
                        try:
                            world = message[0][1:len(message[0])]
                            out = "\n ".join(message[1:])
                        except ValueError:
                            self.msg(self.factory.irc_channel, "07Please include a message to send.")
                        else:
                            if world in self.factory.worlds:
                                self.factory.sendMessageToAll(out, "world", user=user, world=world, fromloc="irc")
                            else:
                                self.msg(self.factory.irc_channel, "07That world does not exist. Try !world message")
                else:
                    msg = sanitizeMessage(msg, [MSGREPLACE["text_colour_to_game"], MSGREPLACE["irc_colour_to_game"], MSGREPLACE["escape_commands"]])
                    for character in msg:
                        if not character.lower() in PRINTABLE:
                            msg = msg.replace(character, "*")
                    if msg[len(msg) - 2] == "&":
                        self.msg(self.factory.irc_channel, "07You cannot use a color at the end of a message.")
                        return
                    self.factory.sendMessageToAll(msg, "irc", user=user, fromloc="irc")
        except:
            self.logger.error(traceback.format_exc())
            self.msg(self.factory.irc_channel, "Internal Server Error (See the Console for more details)")

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        msg = msg.replace("./", " /")
        msg = msg.replace(".!", " !")
        user = user.split('!', 1)[0]
        msg = "".join([char for char in msg if ord(char) < 128 and char != "" or "0"])
        self.factory.sendMessageToAll("%s* %s %s" % (COLOUR_YELLOW, COLOUR_WHITE + user, msg), "irc", user="", fromloc="irc")
        self.logger.info("* %s %s" % (user, msg))
        self.factory.chatlog.write(
            "[%s] * %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), user, msg))
        self.factory.chatlog.flush()

    def sendMessage(self, username, message):
        sanitizeMessage(username, MSGREPLACE["game_colour_to_irc"])
        sanitizeMessage(message, [MSGREPLACE["game_colour_to_irc"], MSGREPLACE["escape_commands"]])
        self.msg(self.factory.irc_channel, "%s: %s" % (username, message))

    def sendServerMessage(self, message, user=None):
        sanitizeMessage(message, [MSGREPLACE["game_colour_to_irc"], MSGREPLACE["escape_commands"]])
        if user != None:
            self.msg(user, "%s" % message)
        else:
            self.msg(self.factory.irc_channel, "%s" % message)

    def sendAction(self, username, message):
        sanitizeMessage(message, MSGREPLACE["game_colour_to_irc"])
        sanitizeMessage(message, [MSGREPLACE["game_colour_to_irc"], MSGREPLACE["escape_commands"]])
        self.msg(self.factory.irc_channel, "* %s %s" % (username, message))

    sendSplitServerMessage = sendWorldMessage = sendPlainWorldMessage = sendNormalMessage = sendServerMessage

    def sendServerList(self, items, wrap_at=63, plain=False, username=None):
        "Sends the items as server messages, wrapping them correctly."
        done = " ".join(items)
        self.irc_factory.sendServerMessage(done)

    # irc callbacks

    def irc_NICK(self, prefix, params):
        "Called when an IRC user changes their nickname."
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        if old_nick in self.ops:
            self.ops.remove(old_nick)
            self.ops.append(new_nick)
        msg = "%s%s is now known as %s" % (COLOUR_YELLOW, old_nick, new_nick)
        self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def userKicked(self, kickee, channel, kicker, message):
        "Called when I observe someone else being kicked from a channel."
        if kickee in self.ops:
            self.ops.remove(kickee)
        msg = "%s%s was kicked from %s by %s" % (COLOUR_YELLOW, kickee, channel, kicker)
        self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
        if not kickee == message:
            msg = "%sReason: %s" % (COLOUR_YELLOW, message)
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def userLeft(self, user, channel):
        "Called when I see another user leaving a channel."
        if user in self.ops:
            self.ops.remove(user)
        msg = "%s%s has left %s" % (COLOUR_YELLOW, user.split("!")[0], channel)
        self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def userJoined(self, user, channel):
        "Called when I see another user joining a channel."
        if user in self.ops:
            self.ops.remove(user)
        msg = "%s%s has joined %s" % (COLOUR_YELLOW, user.split("!")[0], channel)
        self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def modeChanged(self, user, channel, set, modes, args):
        "Called when someone changes a mode."
        setUser = user.split("!")[0]
        arguments = []
        for element in args:
            if element:
                arguments.append(element.split("!")[0])
        if set and modes.startswith("o"):
            if len(arguments) < 2:
                msg = "%s%s was opped on %s by %s" % (COLOUR_YELLOW, arguments[0], channel, setUser)
            else:
                msg = "%sUsers opped on %s by %s: %s (%s)" % (
                COLOUR_YELLOW, channel, setUser, ", ".join(arguments), len(arguments))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            for name in args:
                if not name in self.ops:
                    self.ops.append(name)
        elif not set and modes.startswith("o"):
            done = []
            for name in args:
                done.append(name.split("!")[0])
            if len(arguments) < 2:
                msg = "%s%s was deopped on %s by %s" % (COLOUR_YELLOW, arguments[0], channel, setUser)
            else:
                msg = "%sUsers deopped on %s by %s: %s (%s)" % (
                COLOUR_YELLOW, channel, setUser, ", ".join(arguments), len(arguments))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            for name in args:
                if name in self.ops:
                    self.ops.remove(name)
        elif set and modes.startswith("v"):
            if len(arguments) < 2:
                msg = "%s%s was voiced on %s by %s" % (COLOUR_YELLOW, arguments[0], channel, setUser)
            else:
                msg = "%sUsers voiced on %s by %s: %s (%s)" % (
                COLOUR_YELLOW, channel, setUser, ", ".join(arguments), len(arguments))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            for name in args:
                if not name in self.ops:
                    self.ops.append(name)
        elif not set and modes.startswith("v"):
            done = []
            for name in args:
                done.append(name.split("!")[0])
            if len(arguments) < 2:
                msg = "%s%s was devoiced on %s by %s" % (COLOUR_YELLOW, arguments[0], channel, setUser)
            else:
                msg = "%sUsers devoiced on %s by %s: %s (%s)" % (
                COLOUR_YELLOW, channel, setUser, ", ".join(arguments), len(arguments))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            for name in args:
                if name in self.ops:
                    self.ops.remove(name)
        elif set and modes.startswith("b"):
            msg = "%sBan set in %s by %s" % (COLOUR_YELLOW, channel, setUser)
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            msg = "%s(%s)" % (COLOUR_YELLOW, " ".join(args))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
        elif not set and modes.startswith("b"):
            msg = "%sBan lifted in %s by %s" % (COLOUR_YELLOW, channel, setUser)
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")
            msg = "%s(%s)" % (COLOUR_YELLOW, " ".join(args))
            self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def irc_QUIT(self, user, params):
        userhost = user
        user = user.split('!')[0]
        quitMessage = params[0]
        if userhost in self.ops:
            self.ops.remove(userhost)
        msg = "%s%s has quit IRC." % (COLOUR_YELLOW, user)
        self.factory.sendMessageToAll(msg, "irc", user=user)
        sanitizeMessage(msg, [MSGREPLACE["irc_colour_to_game"], MSGREPLACE["escape_commands"]])
        for character in msg:
            if not character.lower() in PRINTABLE:
                msg = msg.replace(character, "*")
        if msg[len(msg) - 2] == "&":
            return
        msg = "%s(%s%s)" % (COLOUR_YELLOW, quitMessage, COLOUR_YELLOW)
        self.factory.sendMessageToAll(msg, "irc", user="", fromloc="irc")

    def isRank(self):
        return False # For whatever rank, just return False. overriderank is turned on for query so doesn't matter

    isSpectator = isBuilder = isOp = isWorldOwner = isHelper = isMod = isAdmin = isDirector = isOwner = isSilenced = alloweToBuild  = canBreakAdminBlocks = isRank

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
        return 0

class ChatBotFactory(protocol.ClientFactory):
    # the class of the protocol to build when new connection is made
    protocol = ChatBot
    rebootFlag = 0

    def __init__(self, main_factory):
        self.main_factory = main_factory
        self.instance = None
        self.rebootFlag = True

    def quit(self, msg):
        self.rebootFlag = False
        self.instance.sendLine("QUIT :" + msg)

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        self.instance = None
        if self.rebootFlag:
            connector.connect()

    def clientConnectionFailed(self, connector, reason):
        self.main_factory.logger.critical("IRC connection failed: %s" % reason)
        self.instance = None

    def sendMessage(self, username, message):
        if self.instance:
            self.instance.sendMessage(username, message)

    def sendAction(self, username, message):
        if self.instance:
            self.instance.sendAction(username, message)

    def sendServerMessage(self, message, user=None):
        if self.instance:
            self.instance.sendServerMessage(message, user)