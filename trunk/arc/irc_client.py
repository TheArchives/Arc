# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, time, traceback

from twisted.internet import reactor, protocol
from twisted.words.protocols import irc

from arc.constants import *

class ChatBot(irc.IRCClient):
    """An IRC-server chat integration bot."""

    def connectionMade(self):
        self.logger = self.factory.main_factory.logger
        self.nickname = self.factory.main_factory.irc_nick
        self.password = self.factory.main_factory.irc_password
        self.channels = {}
        self.modules = {}
        self.startupErr = {}
        self.commands = {}
        self.hooks = {}
        self.admins = set()
        self.users = set()
        self.inchannel = False
        self.world = None # MUST... FIX... THIS...
        irc.IRCClient.connectionMade(self)
        self.factory.instance = self
        self.factory, self.irc_factory = self.factory.main_factory, self.factory
        self.logger.info("IRC Client connected.")
        for channel in self.channels:
            self.sendLine('NAMES ' + channel)
        if self.password != "":
            self.msg('NickServ', "IDENTIFY %s" % self.password)
        self.logger.info("Loading IRC Modules...")
        for mod in self.factory.irc_modules:
            self.loadModule(mod, None)
        self.logger.info("Joining channels...")
        self.joining = self.irc_factory._channels[0]
        self.join(self.irc_factory._channels[0])

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.info("IRC client disconnected. (%s)" % reason)

    ## List users in 'channel'. Used for gaining user modes on join.
    # @param channel The channel for which to list names.
    def queryWho(self, channel):
        self.logger.debug("Retreiving user list.")
        self.sendLine('WHO %s' % channel)

    def sendError(self, error):
        self.logger.error("Sending error: %s" % error)
        self.sendPacked(TYPE_ERROR, error)
        reactor.callLater(0.2, self.transport.loseConnection)

    def irc_RPL_WHOREPLY(self, *nargs):
        for mode in self.factory.irc_adminmodes:
            if nargs[1][6].endswith(mode):
                self.channels[self.joining]['admins'].append(nargs[1][5])
                self.admins.add(nargs[1][5])
        self.channels[self.joining]['users'].append(nargs[1][5])
        self.users.add(nargs[1][5])
        self.runHook("irc_rpl_whoreply", *nargs)

    ## Called when WHO output is complete.
    # @param nargs A list of arguments including modes etc. See twisted documentation for details.
    def irc_RPL_ENDOFWHO(self, *nargs):
        self.logger.info("Finished Joining %s." % self.joining)
        self.logger.debug("Found users: %s." % ", ".join(self.channels[self.joining]['users']))
        self.logger.debug("Found admins: %s" % ", ".join(self.channels[self.joining]['admins']))
        self.runHook("joined", self.joining) #This is to stop the hook being run before user lists are populated
        self.runHook("irc_rpl_endofwho", *nargs)
        self.irc_factory._channels.remove(self.joining)
        if len(self.irc_factory._channels) != 0:
            self.joining = self.irc_factory._channels[0]
            self.join(self.joining)

    def topicUpdated(self, user, channel, newTopic):
        self.runHook("topicupdated", user, channel, newTopic)

    def registerCommand(self, command, func):
    ## Runs a given function in all loaded modules. Handles any resulting errors.
    # @param hook The name of the hook to be run. This is a name of a function in the irc.IRCClient class and also the name of the method from which this one will be called in this case.
    # @param args A list of the arguments to be passed to the hook function.
    def runHook(self, hook, *args, **kwds):
        self.logger.debug("Running hook %s" % hook)
        for module in self.modules:
            functionName = self.modules[module]['hooks'].get(hook, None)
            if functionName != None:
                try:
                    function = getattr(self.modules[module]['module'], functionName)
                    function(*args, **kwds)
                except Exception as e:
                    # Print the error to a channel if the hook came from a specific one
                    for arg in args:
                        try:
                            if arg in self.channels:
                                self.say(arg, "Error running %s hook in module %s: %s" % (hook, module, str(sys.exc_info()[1])))
                        except:
                            pass
                    self.logger.error("Error running %s hook in module %s\n%s\n%s\n" % (hook, module, "".join(traceback.format_tb(sys.exc_info()[2])), str(sys.exc_info()[1])))

    def runCommand(self, command, parts, triggeredBy, channel):
        self.logger.debug("%s just used '%s'" % (triggeredBy, command))
        for module in self.modules:
            functionName = self.modules[module]['commands'].get(command, None)
            if functionName != None:
                try:
                    func = getattr(self.modules[module]['module'], functionName)
                    if hasattr(func, "config"):
                        if func.config["disabled"]:
                            self.msg(channel, "Command %s has been disabled by the server owner." % command)
                            self.logger.info("%s just tried '%s' but it has been disabled." % (triggeredBy, (" ".join(parts))))
                            return
                        if func.config["channel_only"] and triggeredBy == channel:
                            self.msg(triggeredBy, "Commnd %s can only be used in a channel!")
                            self.logger.info("%s just tried '%s' but was not allowed to use that command in a PM." % (triggeredBy, (" ".join(parts))))
                        if func.config["pm_only"] and triggeredBy == channel:
                            self.msg(triggeredBy, "Commnd %s can only be used in a PM!")
                            self.logger.info("%s just tried '%s' but was not allowed to use that command in a channel." % (triggeredBy, (" ".join(parts))))
                        if func.config["rank"] == "admin" and triggeredBy not in self.admins:
                            self.msg(channel, "%s is an admin-only command!" % command)
                            self.logger.info("%s just tried '%s' but is not an admin." % (triggeredBy, (" ".join(parts))))
                            return
                    func(parts, triggeredBy, channel)
                except Exception as e:
                    # Print the error to whatever channel the command came from
                    self.logger.error("Error running %s command in module %s\n%s\n%s\n%s\n%s\n" % (command, module, "".join(traceback.format_tb(sys.exc_info()[2])), sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
                    self.say(channel, "Error running %s command in module %s: %s" % (command, module, str(sys.exc_info()[1])))

    ## Tries to load a given module name and handles any errors. If the module is already loaded, it uses 'reload' to reload the module.
    # @param moduleName The name of the module that should be looked for.
    # @param channel The channel to send a loaded/failed message to. Allows load commands sent in PM to be replied to in PM.
    def loadModule(self, moduleName, channel):
        self.logger.debug("Attempting to load '%s'" % moduleName)
        try:
            if moduleName in sys.modules:
                self.logger.debug("%s is in sys.modules - reloading" % moduleName)
                reload(sys.modules[moduleName])
            else:
                try:
                    __import__("arc.ircplugins.%s" % moduleName)
                except ImportError:
                    self.logger.error("Error loading %s, it doesn't exist!" % moduleName)
                    if self.inchannel: #Stop calls to 'msg' when startup modules are loaded
                        self.msg(channel, "%sCannot load module \'%s\', it doesn't exist!" % (COLOUR_GREY, moduleName))
                    return
                except Exception as e:
                    self.logger.error("Error loading %s." % moduleName)
                    self.logger.error(traceback.format_exc())
                    if self.inchannel: #Stop calls to 'msg' when startup modules are loaded
                        self.msg(channel, "%sCannot load module \'%s\'." % (COLOUR_GREY, moduleName))
                        self.msg(channel, str(e))
                    return
            module = sys.modules["arc.ircplugins.%s" % moduleName].ircPlugin() # Grab the actual plugin class
            module.client = self
            module.logger = self.logger
            # Check dependancies
            if hasattr(module, 'depends'):
                for depend in module.depends:
                    if depend in sys.modules:
                        self.logger.debug(" - Dependancy '%s' is loaded" % depend)
                        setattr(module, depend, sys.modules[depend].Module())
                    else:
                        self.logger.error("Failed to load %s: A dependancy (%s) is not loaded." % (moduleName, depend))
                        return
            else:
                self.logger.debug("No dependancies found.")
            self.modules[moduleName] = {'module': module}
            self.modules[moduleName]['hooks'] = getattr(module, 'hooks', {})
            self.modules[moduleName]['commands'] = getattr(module, 'commands', {})
            self.logger.info("Module '%s' has been loaded." % moduleName)
            if self.inchannel: #Stop calls to 'msg' when startup modules are loaded
                self.msg(channel, "%sLoaded module \'%s\'." % (COLOUR_GREY, moduleName))
            if hasattr(module, 'gotIRC'):
                module.gotIRC()
            self.runHook("moduleloaded", moduleName)
        except:
            if self.modules.get(moduleName, None) != None:
                del self.modules[moduleName]
            if sys.modules.get(moduleName, None) != None:
                del sys.modules[moduleName]
            if self.inchannel:
                self.msg(channel, "Couldn't load module \'%s\': %s" % (moduleName, str(sys.exc_info()[1])))
            else:
                self.startupErr[moduleName] = sys.exc_info()[1]
            self.logger.error("Error loading module '%s':\n%s" % (moduleName, "".join(traceback.format_tb(sys.exc_info()[2]))))
            raise

    def unloadModule(self, moduleName, channel):
        if self.modules.get(mod, None) == None:
            self.msg(channel, "Module \'%s\' wasn\'t loaded." % mod)
            return
        else:
            if hasattr(sys.modules[mod], "tearDown"):
                sys.modules[mod].tearDown()
            del self.modules[mod]
            del sys.modules[mod]
            self.msg(channel, "Module \'%s\' unloaded." % mod)

    """ TWISTED HOOKS """

    def ctcpQuery_VERSION(self, user, channel, data):
        """Called when received a CTCP VERSION request."""
        nick = user.split("!")[0]
        self.ctcpMakeReply(nick, [('VERSION', 'Arc %s - a Minecraft server written in Python.' % VERSION)])

    ## Called when the bot recieves a notice.
    # @param user The user that the notice came from.
    # @param channel The channel that the notice was sent to. Will be the bot's username if the notice was sent to the bot directly and not to a channel
    def noticed(self, user, channel, message):
        self.logger.debug("Notice: %s" % message)
        self.runHook("noticed", user, channel, message)

    ## Called when the bot signs on to a server.
    def signedOn(self):
        self.connected = True
        self.runHook("signedOn")
        for channel in self.factory.irc_channels:
            self.join(channel)

    ## Called when the bot joins a channel.
    # @param channel The channel that the bot has joined.
    def joined(self, channel):
        self.joining = channel
        self.channels[channel] = {'users': [], 'admins':[]}
        self.inchannel = True
        #Report startup errors
        if len(self.startupErr) != 0:
            self.say(channel, "Errors occured loading modules on startup:")
            for moduleName in self.startupErr:
                self.say(channel, "Couldn't load module \'%s\': %s" % (moduleName, self.startupErr[moduleName]))
        #Build list of admins in the channel
        self.queryWho(channel)

    ## Called when the bot leaves a channel
    # @param channel The channel that the bot has left.
    def left(self, channel):
        del self.channels[channel]
        self.runHook("leftchannel", channel)

    def kickedFrom(self, channel, kicker, message):
        self.runHook("kickedfrom", channel, kicker, message)
        del self.channels[channel]

    def userKicked(self, kickee, channel, kicker, message):
        "Called when I observe someone else being kicked from a channel."
        if kickee in self.channels[channel]["admins"]:
            self.channels[channel]["admins"].remove(kickee)
        msg = "%s%s was kicked from %s by %s" % (COLOUR_YELLOW, kickee, channel, kicker)
        self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, "IRC", msg)))
        if not kickee == message:
            msg = "%sReason: %s" % (COLOUR_YELLOW, message)
            self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, "IRC", msg)))

    ## Called when a user leaves a channel that the bot is in.
    # @param user The user that has left 'channel'.
    # @param channel The channel that 'user' has left.
    def userLeft(self, user, channel):
        user = user.split('!', 1)[0]
        self.logger.irc("User '%s' has left %s." % (user, "\#" + channel))
        msg = "%s%s has left %s" % (COLOUR_YELLOW, user, channel)
        self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, "IRC", msg)))
        if user in self.channels[channel]['admins']:
            self.channels[channel]['admins'].remove(user)
        self.channels[channel]['users'].remove(user)
        self.admins.remove(user)
        self.users.remove(user)
        self.runHook("userleft", user, channel)

    ## Called when the bot sees a user disconnect.
    # @param user The user that has quit.
    # @param quitMessage The message that the user gave for quitting.
    def userQuit(self, user, quitMessage):
        user = user.split('!', 1)[0]
        self.logger.irc("User '%s' has quit: %s." % (user, quitMessage))
        msg = "%s%s has quit. (%s)" % (COLOUR_YELLOW, user, quitMessage)
        self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, "IRC", msg)))
        for channel in self.channels:
            if user in self.channels[channel]['admins']:
                self.channels[channel]['admins'].remove(user)
                self.admins.remove(user)
            if user in self.channels[channel]['users']:
                self.channels[channel]['users'].remove(user)
                self.users.remove(user)
        self.runHook("userquit", user, quitMessage)

    ## Called when the bot sees a user join a channel that it is in.
    # @param user The user that has joined.
    # @param channel The channel that the user has joined.
    def userJoined(self, user, channel):
        user = user.split('!', 1)[0]
        self.logger.irc("User '%s' has joined %s." % (user, channel))
        msg = "%s%s has joined %s" % (COLOUR_YELLOW, user.split("!")[0], channel)
        self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, "IRC", msg)))
        self.channels[channel]['users'].append(user)
        self.users.add(user)
        self.runHook("userjoined", user, channel)

    ## Called when the bot recieves a message from a user or channel.
    # @param user The user that the message is from.
    # @param channel The channel that the message was sent to. Will be te bot's username if the message was a private message.
    # @param message The message, derp.
    def privmsg(self, user, channel, message):
        user, self.host = user.split('!', 1)
        if channel == self.nickname:
            # Make sure we send to the right user
            # What does this line do? -tyteen
            self.channel = channel
            channel = user
        self.runHook("privmsg", user, channel, message)
        if message.startswith("$%s" % self.nickname):
            # It's a command
            parts = [x.strip() for x in message.split() if x.strip()]
            command = parts[1]
            self.runCommand(command, parts, user, channel)
        elif message.startswith("$"):
            # IRC Only message, just log it
            self.logger.info(message)
        else:
            # Messages to be delievered to the game
            msg = message # Yes I know I am very lazy
            msg = msg.replace("%0", "&0")
            msg = msg.replace("%1", "&1")
            msg = msg.replace("%2", "&2")
            msg = msg.replace("%3", "&3")
            msg = msg.replace("%4", "&4")
            msg = msg.replace("%5", "&5")
            msg = msg.replace("%6", "&6")
            msg = msg.replace("%7", "&7")
            msg = msg.replace("%8", "&8")
            msg = msg.replace("%9", "&9")
            msg = msg.replace("%a", "&a")
            msg = msg.replace("%b", "&b")
            msg = msg.replace("%c", "&c")
            msg = msg.replace("%d", "&d")
            msg = msg.replace("%e", "&e")
            msg = msg.replace("%f", "&f")
            msg = msg.replace("./", " /")
            msg = msg.replace(".!", " !")
            if msg[len(msg)-2] == "&":
                self.msg(channel, "You cannot use a color at the end of a message.")
                return
            if len(msg) > 51:
                moddedmsg = msg[:51].replace(" ", "")
                if moddedmsg[len(moddedmsg)-2] == "&":
                    msg = msg.replace("&", "*")
            self.factory.queue.put((self, TASK_IRCMESSAGE, (127, "[IRC] " + COLOUR_PURPLE, user, msg)))
            self.logger.irc('<%s> %s' % (user, message))

    def action(self, user, channel, data):
        msg = msg.replace("./", " /")
        msg = msg.replace(".!", " !")
        user = user.split('!', 1)[0]
        msg = "".join([char for char in msg if ord(char) < 128 and char != "" or "0"])
        self.factory.queue.put((self, TASK_ACTION, (127, COLOUR_PURPLE, user, msg)))
        self.logger.irc("* %s %s" % (user, msg))
        self.runHook("action", user, channel, data)

    def sendMessage(self, username, message):
        message = message.replace("&0", "01")
        message = message.replace("&1", "02")
        message = message.replace("&2", "03")
        message = message.replace("&3", "10")
        message = message.replace("&4", "05")
        message = message.replace("&5", "06")
        message = message.replace("&6", "07")
        message = message.replace("&7", "15")
        message = message.replace("&8", "14")
        message = message.replace("&9", "12")
        message = message.replace("&a", "09")
        message = message.replace("&b", "11")
        message = message.replace("&c", "04")
        message = message.replace("&d", "13")
        message = message.replace("&e", "08")
        message = message.replace("&f", "14")
        username = username.replace("&0", "01")
        username = username.replace("&1", "02")
        username = username.replace("&2", "03")
        username = username.replace("&3", "10")
        username = username.replace("&4", "05")
        username = username.replace("&5", "06")
        username = username.replace("&6", "07")
        username = username.replace("&7", "15")
        username = username.replace("&8", "14")
        username = username.replace("&9", "12")
        username = username.replace("&a", "09")
        username = username.replace("&b", "11")
        username = username.replace("&c", "04")
        username = username.replace("&d", "13")
        username = username.replace("&e", "08")
        username = username.replace("&f", "14")
        for channel in self.channels.keys():
            self.msg(channel, "%s: %s" % (username, message))

    def sendServerMessage(self, message):
        message = message.replace("./", " /")
        message = message.replace(".!", " !")
        message = message.replace("&0", "01")
        message = message.replace("&1", "02")
        message = message.replace("&2", "03")
        message = message.replace("&3", "10")
        message = message.replace("&4", "05")
        message = message.replace("&5", "06")
        message = message.replace("&6", "07")
        message = message.replace("&7", "15")
        message = message.replace("&8", "14")
        message = message.replace("&9", "12")
        message = message.replace("&a", "09")
        message = message.replace("&b", "11")
        message = message.replace("&c", "04")
        message = message.replace("&d", "13")
        message = message.replace("&e", "08")
        for channel in self.channels.keys():
            self.msg(channel, "%s" % message)

    def sendAction(self, username, message):
        message = message.replace("&0", "01")
        message = message.replace("&1", "02")
        message = message.replace("&2", "03")
        message = message.replace("&3", "10")
        message = message.replace("&4", "05")
        message = message.replace("&5", "06")
        message = message.replace("&6", "07")
        message = message.replace("&7", "15")
        message = message.replace("&8", "14")
        message = message.replace("&9", "12")
        message = message.replace("&a", "09")
        message = message.replace("&b", "11")
        message = message.replace("&c", "04")
        message = message.replace("&d", "13")
        message = message.replace("&e", "08")
        for channel in self.channels.keys():
            self.msg(channel, "* %s %s" % (username, message))

    ## Called when users or channel's modes are changed.
    # @param user The user who instigated the change.
    # @param channel The channel where the modes are changed. If args is empty the channel for which the modes are changing. If the changes are at server level it could be equal to 'user'.
    # @param set True if the mode(s) is being added, False if it is being removed.
    # @param modes The mode or modes which are being changed.
    # @param args Any additional information required for the mode change.
    def modeChanged(self, user, channel, set, modes, args):
        if (channel == channel) and (modes.startswith(tuple(self.factory.irc_adminmodes))):
            if set:
                for username in args:
                    if not username in self.channels[channel]['admins']:
                        self.channels[channel]['admins'].append(username)
                    if not username in self.admins:
                        self.admins.add(username)
            else:
                for username in args:
                    self.channels[channel]['admins'].remove(username)
                    self.admins.remove(username)
        self.runHook("modechanged", user, channel, set, modes, args)

    def nickChanged(self, nick):
        self.logger.info("Nick changed to %s." % nick)
        self.runHook("nickchanged", nick)

    def userRenamed(self, oldnick, newnick):
        for channel, chaninfo in self.channels.items():
            if oldnick in chaninfo['users']:
                chaninfo['users'].append(newnick)
                chaninfo['users'].remove(oldnick)
            self.users.add(newnick)
            self.users.remove(oldnick)
        msg = "* %s is now known as %s" % (oldnick, newnick)
        self.factory.queue.put((self, TASK_IRCMESSAGE, (127, COLOUR_PURPLE, user, msg)))
        self.runHook("userrenamed", oldnick, newnick)

class ChatBotFactory(protocol.ClientFactory):
    protocol = ChatBot
    rebootFlag = False

    def __init__(self, main_factory):
        self.main_factory = main_factory
        self.instance = None
        self.logger = self.main_factory.logger

    def quit(self, msg):
        self.rebootFlag = 0
        self.instance.sendLine("QUIT :" + msg)

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        self.instance = None
        if(self.rebootFlag):
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

    def sendServerMessage(self, message):
        if self.instance:
            message = message.replace("&0", "01")
            message = message.replace("&1", "02")
            message = message.replace("&2", "03")
            message = message.replace("&3", "10")
            message = message.replace("&4", "05")
            message = message.replace("&5", "06")
            message = message.replace("&6", "07")
            message = message.replace("&7", "15")
            message = message.replace("&8", "14")
            message = message.replace("&9", "12")
            message = message.replace("&a", "09")
            message = message.replace("&b", "11")
            message = message.replace("&c", "04")
            message = message.replace("&d", "13")
            message = message.replace("&e", "08")
            message = message.replace("&f", "00")
            message = message.replace("./", " /")
            message = message.replace(".!", " !")
            message = message.replace(".@", " @")
            message = message.replace(".#", " #")
            self.instance.sendServerMessage(message, admin)