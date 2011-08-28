# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, datetime, hashlib, logging, os, traceback, shutil

from twisted.internet import reactor
from twisted.internet.protocol import Protocol

from arc.constants import *
from arc.decorators import *
from arc.irc_client import ChatBotFactory
from arc.plugins import protocol_plugins
from arc.playerdata import *

class ArcServerProtocol(Protocol):
    """
    Main protocol class for communicating with clients.
    Commands are mainly provided by plugins (protocol plugins).
    """
    
    hooks = {}

    def connectionMade(self):
        "We've got a TCP connection, let's set ourselves up."
        # We use the buffer because TCP is a stream protocol :)
        self.buffer = ""
        self.loading_world = False
        self.chatlogger = self.factory.chatlogger
        self.logger = self.factory.logger
        # Load plugins for ourselves
        self.identified = False
        self.hooks = {}
        self.commands = {}
        self.plugins = []
        self.settings = {}
        for plugin in protocol_plugins:
            try:
                self.plugins.append(plugin(self))
            except Exception as a:
                self.factory.logger.error("Unable to load protocol plugin '%s'" % plugin.__name__)
                self.factory.logger.error("Error: %s" % a)
                error = traceback.format_exc()
                errorsplit = error.split("\n")
                for element in errorsplit:
                    if not element.strip(" ") == "":
                        self.factory.logger.debug(element)
                continue
        # Set identification variable to false
        self.identified = False
        # Get an ID for ourselves
        try:
            self.id = self.factory.claimId(self)
        except ServerFull:
            self.sendError("The server is full.")
            return
        # Open the Whisper Log, Adminchat log and WorldChat Log
        # TODO: Use a chatlog handler, this is stupid and breaks things.
        # Check for IP bans
        ip = self.transport.getPeer().host
        if self.factory.isIpBanned(ip):
            self.sendError("You are banned: %s" % self.factory.ipBanReason(ip))
            return
        self.factory.logger.debug("Assigned ID %i" % self.id)
        self.factory.joinWorld(self.factory.default_name, self)
        self.sent_first_welcome = False
        self.read_only = False
        self.username = None
        self.selected_archive_name = None
        self.initial_position = None
        self.last_block_changes = []
        self.last_block_position = (-1, -1, -1)
        self.gone = 0
        self.frozen = False

    def registerCommand(self, command, func):
        "Registers func as the handler for the command named 'command'."
        # Make sure case doesn't matter
        command = command.lower()
        # Warn if already registered
        if command in self.commands:
            self.factory.logger.warn("Command '%s' is already registered. Overriding." % command)
            self.factory.logger.info("This means that the plugin containing %s has been loaded twice." % command)
        # Register
        self.commands[command] = func

    def unregisterCommand(self, command, func):
        "Unregisters func as command's handler, if it is currently the handler."
        # Make sure case doesn't matter
        command = command.lower()
        try:
            if self.commands[command] == func:
                del self.commands[command]
        except KeyError:
            self.factory.logger.warn("Command '%s' is not registered to %s." % (command, func))

    def registerHook(self, hook, func):
        "Registers func as something to be run for hook 'hook'."
        if hook not in self.hooks:
            self.hooks[hook] = []
        self.hooks[hook].append(func)

    def unregisterHook(self, hook, func):
        "Unregisters func from hook 'hook'."
        try:
            self.hooks[hook].remove(func)
        except (KeyError, ValueError):
            self.factory.logger.warn("Hook '%s' is not registered to %s." % (hook, func))

    def unloadPlugin(self, plugin_class):
        "Unloads the given plugin class."
        for plugin in self.plugins:
            if isinstance(plugin, plugin_class):
                self.plugins.remove(plugin)
                plugin.unregister()

    def loadPlugin(self, plugin_class):
        self.plugins.append(plugin_class(self))

    def runHook(self, hook, *args, **kwds):
        "Runs the hook 'hook'."
        for func in self.hooks.get(hook, []):
            if hook == "blockchange":
                self.factory.hookslog.write(str(func) + "\n")
                self.factory.hookslog.flush()
            result = func(*args, **kwds)
            # If they return False, we can skip over and return
            if result is not None:
                return result
        return None

    def queueTask(self, task, data=[], world=None):
        "Adds the given task to the factory's queue."
        # If they've overridden the world, use that as the client.
        if world:
            self.factory.queue.put((
                world,
                task,
                data,
            ))
        else:
            self.factory.queue.put((
                self,
                task,
                data,
            ))

    def sendWorldMessage(self, message):
        "Sends a message to everyone in the current world."
        self.queueTask(TASK_WORLDMESSAGE, (255, self.world, COLOUR_YELLOW+message))

    def sendPlainWorldMessage(self, message):
        "Sends a message to everyone in the current world, without any added color."
        self.queueTask(TASK_WORLDMESSAGE, (255, self.world, message))

    def connectionLost(self, reason):
        # Leave the world
        try:
            self.factory.leaveWorld(self.world, self)
        except (KeyError, AttributeError):
            pass
        # Remove ourselves from the username list
        if self.username:
            self.factory.recordPresence(self.username)
            try:
                if self.factory.usernames[self.username.lower()] is self:
                    del self.factory.usernames[self.username.lower()]
            except KeyError:
                pass
        # Remove from ID list, send removed msgs
        self.factory.releaseId(self.id)
        self.factory.queue.put((self, TASK_PLAYERLEAVE, (self.id,)))
        if self.username:
            self.factory.logger.info("Disconnected '%s'" % (self.username))
            self.factory.runServerHook("playerQuit", {"client": self})
            self.runHook("playerquit", self.username)
            self.factory.logger.debug("(reason: %s)" % (reason))
        # Kill all plugins
        del self.plugins
        del self.commands
        del self.hooks
        self.connected = 0

    def send(self, data):
        self.transport.write(data)

    def sendPacked(self, mtype, *args):
        fmt = TYPE_FORMATS[mtype]
        self.transport.write(chr(mtype) + fmt.encode(*args))

    def sendError(self, error):
        self.factory.logger.info("Sending error: %s" % error)
        self.sendPacked(TYPE_ERROR, error)
        reactor.callLater(0.2, self.transport.loseConnection)

    def duplicateKick(self):
        "Called when someone else logs in with our username"
        self.sendError("You logged in on another computer.")

    def packString(self, string, length=64, packWith=" "):
        return string + (packWith*(length-len(string)))

    def isOp(self):
        return (self.username.lower() in self.world.ops) or self.isWorldOwner() or self.isHelper() or self.isMod() or self.isAdmin() or self.isDirector() or self.isOwner()

    def isWorldOwner(self):
        return (self.username.lower() in self.world.owner) or self.isHelper() or self.isMod() or self.isAdmin() or self.isDirector() or self.isOwner()

    def isOwner(self):
        return self.factory.isOwner(self.username.lower())

    def isDirector(self):
        return self.factory.isDirector(self.username.lower()) or self.isOwner()

    def isAdmin(self):
        return self.factory.isAdmin(self.username.lower()) or self.isDirector() or self.isOwner()

    def isSilenced(self):
        return self.factory.isSilenced(self.username.lower())

    def isMod(self):
        return self.factory.isMod(self.username.lower()) or self.isAdmin() or self.isDirector() or self.isOwner()

    def isHelper(self):
        return self.factory.isHelper(self.username.lower()) or self.isMod() or self.isAdmin() or self.isDirector() or self.isOwner()

    def isBuilder(self):
        return (self.username.lower() in self.world.builders) or self.isOp() or self.isWorldOwner() or self.isHelper() or self.isMod()

    def isSpectator(self):
        return self.factory.isSpectator(self.username.lower())

    def canEnter(self, world):
        if not world.private and (self.username.lower() not in world.worldbans):
            return True
        else:
            return (self.username.lower() in world.builders) or (self.username.lower() in world.ops) or (self.username.lower() == world.owner) or self.isHelper() or self.isMod() or self.isAdmin() or self.isDirector()

    def dataReceived(self, data):
        "Called when data is received over the socket."
        # First, add the data we got onto our internal buffer
        self.buffer += data
        # While there's still data there...
        while self.buffer:
            # Examine the first byte, to see what the command is
            type = ord(self.buffer[0])
            try:
                format = TYPE_FORMATS[type]
            except KeyError:
                # it's a weird data packet, probably a ping.
                reactor.callLater(0.2, self.transport.loseConnection)
                return
            # See if we have all its data
            if len(self.buffer) - 1 < len(format):
                # Nope, wait a bit
                break
            # OK, decode the data
            parts = list(format.decode(self.buffer[1:]))
            self.buffer = self.buffer[len(format)+1:]
            if type == TYPE_INITIAL:
                # Get the client's details
                protocol, self.username, mppass, utype = parts
                if self.identified == True:
                    self.factory.logger.info("Kicked '%s'; already logged in to server" % (self.username))
                    self.sendError("You already logged in! Foolish bot owners.")
                # Check their password
                correct_pass = hashlib.md5(self.factory.salt + self.username).hexdigest()[-32:].strip("0")
                mppass = mppass.strip("0")
                if not self.transport.getHost().host.split(".")[0:2] == self.transport.getPeer().host.split(".")[0:2]:
                    if mppass != correct_pass:
                        self.factory.logger.info("Kicked '%s'; invalid password (%s, %s)" % (self.username, mppass, correct_pass))
                        self.sendError("Incorrect authentication, please try again.")
                        return
                self.factory.logger.info("Connected, as '%s'" % self.username)
                self.identified = True
                # Are they banned?
                if self.factory.isBanned(self.username):
                    self.sendError("You are banned: %s" % self.factory.banReason(self.username))
                    return
                # OK, see if there's anyone else with that username
                if not self.factory.duplicate_logins and self.username.lower() in self.factory.usernames:
                    self.factory.usernames[self.username.lower()].duplicateKick()
                self.factory.usernames[self.username.lower()] = self
                # Right protocol?
                if protocol != 7:
                    self.sendError("Wrong protocol.")
                    break
                # Send them back our info.
                breakable_admins = self.runHook("canbreakadmin")
                self.sendPacked(
                    TYPE_INITIAL,
                    7, # Protocol version
                    self.packString(self.factory.server_name),
                    self.packString(self.factory.server_message),
                    100 if breakable_admins else 0,
                )
                # Then... stuff
                for client in self.factory.usernames.values():
                    client.sendServerMessage("%s has come online." % self.username)
                if self.factory.irc_relay:
                    self.factory.irc_relay.sendServerMessage("07%s has come online." % self.username)
                reactor.callLater(0.1, self.sendLevel)
                reactor.callLater(1, self.sendKeepAlive)
                self.data = PlayerData(self) # Create a player data object
                self.settings["tpprotect"] = self.data.bool("misc", "tpprotect") # Get their teleport protection setting
                self.factory.runServerHook("onPlayerConnect", {"client": self}) # Run the player connect hook
            elif type == TYPE_BLOCKCHANGE:
                x, y, z, created, block = parts
                if block == 255:
                    block = 0
                if block > 49:
                    self.factory.logger.info("Kicked '%s'; Tried to place an invalid block.; Block: '%s'" % (self.transport.getPeer().host, block))
                    self.sendError("Invalid blocks are not allowed!")
                    return
                if 6 < block < 12:
                    if not block == 9 and not block == 11:
                        self.factory.logger.info("Kicked '%s'; Tried to place an invalid block.; Block: '%s'" % (self.transport.getPeer().host, block))
                        self.sendError("Invalid blocks are not allowed!")
                        return
                if self.identified == False:
                    self.factory.logger.info("Kicked '%s'; did not send a login before building" % (self.transport.getPeer().host))
                    self.sendError("Provide an authentication before building.")
                    return
                try:
                # If we're read-only, reverse the change
                    if self.isSpectator():
                        self.sendBlock(x, y, z)
                        self.sendServerMessage("Spectators cannot edit worlds.")
                        return
                    allowbuild = self.runHook("blockclick", x, y, z, block, "user")
                    if allowbuild is False:
                        self.sendBlock(x, y, z)
                        return
                    elif not self.AllowedToBuild(x, y, z):
                        self.sendBlock(x, y, z)
                        return
                    # This tries to prevent out-of-range errors on the blockstore
                    # Track if we need to send back the block change
                    overridden = False
                    selected_block = block
                    # If we're deleting, block is actually air
                    # (note the selected block is still stored as selected_block)
                    if not created:
                        block = 0
                    # Pre-hook, for stuff like /paint
                    new_block = self.runHook("preblockchange", x, y, z, block, selected_block, "user")
                    if new_block is not None:
                        block = new_block
                        overridden = True
                    # Call hooks
                    new_block = self.runHook("blockchange", x, y, z, block, selected_block, "user")
                    # After the runHook iteration, insert a linebreak
                    self.factory.hookslog.write(("=" * 30) + "\n")
                    self.factory.hookslog.flush()
                    if new_block is False:
                        # They weren't allowed to build here!
                        self.sendBlock(x, y, z)
                        continue
                    elif new_block is True:
                        # Someone else handled building, just continue
                        continue
                    elif new_block is not None:
                        block = new_block
                        overridden = True
                    # OK, save the block
                    self.world[x, y, z] = chr(block)
                    # Now, send the custom block back if we need to
                    if overridden:
                        self.sendBlock(x, y, z, block)
                # Out of bounds!
                except (KeyError, AssertionError):
                    self.sendPacked(TYPE_BLOCKSET, x, y, z, "\0")
                # OK, replay changes to others
                else:
                    self.factory.queue.put((self, TASK_BLOCKSET, (x, y, z, block)))
                    if len(self.last_block_changes) >= 2:
                        self.last_block_changes = [(x, y, z)] + self.last_block_changes[:1]+self.last_block_changes[1:2]
                    else:
                        self.last_block_changes = [(x, y, z)] + self.last_block_changes[:1]
            elif type == TYPE_PLAYERPOS:
                # If we're loading a world, ignore these.
                if self.loading_world:
                    continue
                naff, x, y, z, h, p = parts
                pos_change = not (x == self.x and y == self.y and z == self.z)
                dir_change = not (h == self.h and p == self.p)
                if self.frozen:
                    newx = self.x >> 5
                    newy = self.y >> 5
                    newz = self.z >> 5
                    self.teleportTo(newx, newy, newz, h, p)
                    return
                override = self.runHook("poschange", x, y, z, h, p)
                # Only send changes if the hook didn't say no
                if override is not False:
                    if pos_change:
                        # Send everything to the other clients
                        self.factory.queue.put((self, TASK_PLAYERPOS, (self.id, self.x, self.y, self.z, self.h, self.p)))
                    elif dir_change:
                        self.factory.queue.put((self, TASK_PLAYERDIR, (self.id, self.h, self.p)))
                self.x, self.y, self.z, self.h, self.p = x, y, z, h, p
            elif type == TYPE_MESSAGE:
                # We got a message.
                byte, message = parts
                rank = self.loadRank()
                user = self.username.lower()
                if self.username.lower() in rank:
                    self.title = rank[user]+" "
                else:
                    self.title = ""
                self.usertitlename = self.title + self.username
                override = self.runHook("chatmsg", message)
                goodchars = self.factory.printable
                for c in message.lower():
                    if not c in goodchars:
                        self.factory.logger.info("Kicked '%s'; Tried to use invalid characters; Message: '%s'" % (self.transport.getPeer().host, message))
                        self.sendError("Invalid characters are not allowed!")
                        return
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
                message = message.replace("0", "&f")
                message = message.replace("00", "&f")
                message = message.replace("1", "&0")
                message = message.replace("01", "&0")
                message = message.replace("2", "&1")
                message = message.replace("02", "&1")
                message = message.replace("3", "&2")
                message = message.replace("03", "&2")
                message = message.replace("4", "&c")
                message = message.replace("04", "&c")
                message = message.replace("5", "&4")
                message = message.replace("05", "&4")
                message = message.replace("6", "&5")
                message = message.replace("06", "&5")
                message = message.replace("7", "&6")
                message = message.replace("07", "&6")
                message = message.replace("8", "&e")
                message = message.replace("08", "&e")
                message = message.replace("9", "&a")
                message = message.replace("09", "&a")
                message = message.replace("10", "&3")
                message = message.replace("11", "&b")
                message = message.replace("12", "&9")
                message = message.replace("13", "&d")
                message = message.replace("14", "&8")
                message = message.replace("15", "&7")
                message = message.replace("./", " /")
                message = message.replace(".!", " !")
                message = message.replace(".@", " @")
                message = message.replace(".#", " #")
                message = message.replace("%$rnd", "&$rnd")
                if message[len(message)-2] == "&":
                    self.sendServerMessage("You cannot use a color at the end of a message")
                    return
                if len(message) > 51:
                    moddedmsg = message[:51].replace(" ", "")
                    if moddedmsg[len(moddedmsg)-2] == "&":
                        message = message.replace("&", "*")
                if self.identified == False:
                    self.factory.logger.info("Kicked '%s'; did not send a login before chatting; Message: '%s'" % (self.transport.getPeer().host, message))
                    self.sendError("Provide an authentication before chatting.")
                    return
                if message.startswith("/"):
                    # It's a command
                    parts = [x.strip() for x in message.split() if x.strip()]
                    command = parts[0].strip("/")
                    # See if we can handle it internally
                    try:
                        func = getattr(self, "command%s" % command.title())
                    except AttributeError:
                        # Can we find it from a plugin?
                        try:
                            func = self.commands[command.lower()]
                        except KeyError:
                            self.sendServerMessage("Unknown command '%s'" % command)
                            return
                    if hasattr(func, "config"):
                        if func.config["disabled"]:
                            self.sendServerMessage("Command %s has been disabled by the server owner." % command)
                            self.factory.logger.info("%s just tried '%s' but it has been disabled." % (self.username, " ".join(parts)))
                            return
                        if self.isSpectator() and func.config["rank"]:
                            self.sendServerMessage("'%s' is not available to spectators." % command)
                            self.factory.logger.info("%s just tried '%s' but is a spectator." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "owner" and not self.isOwner():
                            self.sendServerMessage("'%s' is an Owner-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not an owner." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "director" and not self.isDirector():
                            self.sendServerMessage("'%s' is a Director-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not a director." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "admin" and not self.isAdmin():
                            self.sendServerMessage("'%s' is an Admin-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not an admin." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "mod" and not self.isMod():
                            self.sendServerMessage("'%s' is a Mod-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not a mod." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "helper" and not self.isHelper():
                            self.sendServerMessage("'%s' is a Helper-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not a helper." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "worldowner" and not self.isWorldOwner():
                            self.sendServerMessage("'%s' is an WorldOwner-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not a world owner." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "op" and not self.isOp():
                            self.sendServerMessage("'%s' is an Op-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not an op." % (self.username, " ".join(parts)))
                            return
                        if func.config["rank"] == "builder" and not self.isBuilder():
                            self.sendServerMessage("'%s' is a Builder-only command!" % command)
                            self.factory.logger.info("%s just tried '%s' but is not a builder." % (self.username, " ".join(parts)))
                            return
                    # Using custom message?
                    if hasattr(func, "config"):
                        if func.config["custom_cmdlog_msg"]:
                            self.factory.logger.info("%s %s" % (self.username, func.config["custom_cmdlog_msg"]))
                    else:
                        self.factory.logger.info("%s just used '%s'" % (self.username, " ".join(parts)))
                    # Log it in IRC, if enabled.
                    if self.factory.irc_relay:
                        if self.factory.irc_cmdlogs:
                            if hasattr(func, "config"):
                                if func.config["custom_cmdlog_msg"]:
                                    self.factory.irc_relay.sendServerMessage("%s %s" % (self.username, func.config["custom_cmdlog_msg"]))
                                else:
                                    self.factory.irc_relay.sendServerMessage("%s just used: %s" % (self.username, " ".join(parts)))
                            else:
                                self.factory.irc_relay.sendServerMessage("%s just used: %s" % (self.username, " ".join(parts)))
                    # Log it as a command
                    self.factory.logger.command("(%s) %s" % (self.username, " ".join(parts)))
                    try:
                        func(parts, "user", False) # fromloc is user, overriderank is false
                    except Exception as e:
                        self.sendSplitServerMessage("Unable to run that command!")
                        self.sendSplitServerMessage("Error: %s" % e)
                        self.sendSplitServerMessage("Please report this to the staff!")
                        self.factory.logger.error("Error in command '%s': %s" % (command.title(), e))
                        error = traceback.format_exc()
                        errorsplit = error.split("\n")
                        for element in errorsplit:  
                            if not element.strip(" ") == "":
                                self.factory.logger.error(element)
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
                            self.sendWhisper(self.username, text)
                            self.factory.logger.info("@"+username+" (from "+self.username+"): "+text)
                            self.factory.chatlogger.whisper(self.usertitlename, username, text)
                        else:
                            self.sendServerMessage("%s is currently offline." % username)
                elif message.startswith("!"):
                    # It's a world message.
                    if len(message) == 1:
                        self.sendServerMessage("Please include a message to send.")
                    else:
                        try:
                            text = message[1:]
                        except ValueError:
                            self.sendServerMessage("Please include a message to send.")
                        else:
                            self.sendWorldMessage ("!"+self.userColour()+self.usertitlename+":"+COLOUR_WHITE+" "+text)
                            self.factory.logger.info("!"+self.userColour()+self.usertitlename+"&f in &c"+str(self.world.id)+"&f: "+text)
                            self.factory.chatlogger.world(self.usertitlename, str(self.world.id), text)
                            if self.factory.irc_relay:
                                self.factory.irc_relay.sendServerMessage(COLOUR_YELLOW+"!"+self.userColour()+self.usertitlename+COLOUR_BLACK+" in "+str(self.world.id)+": "+text)
                elif message.startswith("#"):
                    # It's a staff-only message.
                    if len(message) == 1:
                        self.sendServerMessage("Please include a message to send.")
                    else:
                        try:
                            text = message[1:]
                        except ValueError:
                            if self.isMod():
                                self.sendServerMessage("Please include a message to send.")
                            else:
                                self.factory.queue.put((self, TASK_MESSAGE, (self.id, self.userColour(), self.username, message)))
                        if self.isMod():
                            self.factory.queue.put((self, TASK_STAFFMESSAGE, (0, self.userColour(), self.username, text, False)))
                            self.factory.chatlogger.staff(self.username, text)
                            self.logger.info("# %s: %s" % (self.username, text))
                        else:
                            self.factory.queue.put((self, TASK_MESSAGE, (self.id, self.userColour(), self.usertitlename, message)))
                else:
                    if self.isSilenced():
                        self.sendServerMessage("You are silenced and cannot speak.")
                    else:
                        if override is not True:
                            self.factory.queue.put((self, TASK_MESSAGE, (self.id, self.userColour(), self.usertitlename, message)))
            else:
                if type == 2:
                    self.factory.logger.warn("Beta client attempted to connect.")
                    self.sendPacked(255, self.packString("Sorry, but this is a Classic-only server."))
                    self.transport.loseConnection()
                else:
                    self.factory.logger.warn("Unable to handle type %s" % type)

    def userColour(self):
        if self.factory.colors:
            if (self.username.lower() in self.factory.spectators):
                colour = COLOUR_BLACK
            elif (self.username.lower() in self.factory.owners):
                colour = COLOUR_DARKGREEN
            elif (self.username.lower() in self.factory.directors):
                colour = COLOUR_GREEN
            elif (self.username.lower() in self.factory.admins):
                colour = COLOUR_RED
            elif (self.username.lower() in self.factory.mods):
                colour = COLOUR_BLUE
            elif (self.username.lower() in self.factory.helpers):
                colour = COLOUR_DARKBLUE
            elif self.username.lower() in INFO_VIPLIST:
                colour = COLOUR_YELLOW
            elif (self.username.lower() in self.world.owner):
                colour = COLOUR_DARKYELLOW
            elif (self.username.lower() in self.world.ops):
                colour = COLOUR_DARKCYAN
            elif (self.username.lower() in self.world.builders):
                colour = COLOUR_CYAN
            else:
                colour = COLOUR_WHITE
        else:
            colour = COLOUR_WHITE
        return colour

    def colouredUsername(self):
        return self.userColour() + self.username

    def teleportTo(self, x, y, z, h=0, p=0):
        "Teleports the client to the coordinates"
        if h > 255:
            h = 255
        self.sendPacked(TYPE_PLAYERPOS, 255, (x<<5)+16, (y<<5)+16, (z<<5)+16, h, p)

    def changeToWorld(self, world_id, position=None):
        self.factory.queue.put((self, TASK_WORLDCHANGE, (self.id, self.world)))
        self.loading_world = True
        world = self.factory.joinWorld(world_id, self)
        self.runHook("newworld", world)
        # These code should be plugin-fied, can anybody check?
        if not self.isOp():
            self.block_overrides = {}
        self.last_block_changes = []
        # End of code that needs to be plugin-fied
        self.initial_position = position
        if self.world.is_archive:
            self.sendSplitServerMessage("This world is an archive, and will cease to exist once the last person leaves.")
            self.sendServerMessage(COLOUR_RED+"Staff: Please do not reboot this world.")
        if self.world.hidden:
            self.sendSplitServerMessage(COLOUR_GREEN+"This world is hidden, and does not show up on the world list.")
        breakable_admins = self.runHook("canbreakadmin")
        self.sendPacked(TYPE_INITIAL, 7, ("%s: %s" % (self.factory.server_name, world_id)), "Entering world '%s'" % world_id, 100 if breakable_admins else 0)
        self.sendLevel()

    def sendRankUpdate(self):
        "Sends a rank update."
        self.runHook("rankchange")
        self.respawn()

    def respawn(self):
        "Respawns the user in-place for other users, updating their nick."
        self.queueTask(TASK_PLAYERRESPAWN, [self.id, self.colouredUsername(), self.x, self.y, self.z, self.h, self.p])

    def sendBlock(self, x, y, z, block=None):
        try:
            def real_send(block):
                self.sendPacked(TYPE_BLOCKSET, x, y, z, block)
            if block is not None:
                real_send(block)
            else:
                self.world[x, y, z].addCallback(real_send)
        except AssertionError:
            self.factory.logger.warn("Block out of range: %s %s %s" % (x, y, z))

    def sendPlayerPos(self, id, x, y, z, h, p):
        self.sendPacked(TYPE_PLAYERPOS, id, x, y, z, h, p)

    def sendPlayerDir(self, id, h, p):
        self.sendPacked(TYPE_PLAYERDIR, id, h, p)

    def sendMessage(self, id, colour, username, text, direct=False, action=False):
        "Sends a message to the user, splitting it up if needed."
        # See if it's muted.
        replacement = self.runHook("recvmessage", colour, username, text, action)
        if replacement is False:
            return
        # See if we should highlight the names
        if action:
            prefix = "%s* %s%s%s " % (COLOUR_YELLOW, colour, username, COLOUR_WHITE)
        else:
            prefix = "%s%s:%s " % (colour, username, COLOUR_WHITE)
        # Send the message in more than one bit if needed
        self._sendMessage(prefix, text, id)

    def _sendMessage(self, prefix, message, id=127):
        "Utility function for sending messages, which does line splitting."
        lines = []
        temp = []
        thisline = ""
        words = message.split()
        linelen = 63 - len(prefix)
        for x in words:
            if len(thisline + " " + x) < linelen:
                thisline = thisline + " " + x
            else:
                if len(x) > linelen:
                    if not thisline == "":
                        lines.append(thisline)
                    while len(x) > linelen:
                        temp.append(x[:linelen])
                        x=x[linelen:]
                    lines = lines + temp
                    thisline = x
                else:
                    lines.append(thisline)
                    thisline = x
        if thisline != "":
            lines.append(thisline)
        for line in lines:
            if len(line) > 0:
                if line[0] == " ":
                    newline = line[1:]
                else:
                    newline = line
                if newline[len(newline)-2] == "&":
                    newline = newline[:len(newline)-2]
                self.sendPacked(TYPE_MESSAGE, id, prefix + newline)

    def sendAction(self, id, colour, username, text):
        self.sendMessage(id, colour, username, text, action=True)

    def sendWhisper(self, username, text):
        self.sendNormalMessage("%s@%s%s: %s%s" % (COLOUR_YELLOW, self.userColour(), username, COLOUR_WHITE, text))

    def sendServerMessage(self, message):
        self.sendPacked(TYPE_MESSAGE, 255, message)

    def sendNormalMessage(self, message):
        self._sendMessage("", message)

    def sendServerList(self, items, wrap_at=63, plain=False):
        "Sends the items as server messages, wrapping them correctly."
        current_line = items[0]
        for item in items[1:]:
            if len(current_line) + len(item) + 1 > wrap_at:
                if plain:
                    self.sendNormalMessage(current_line)
                else:
                    self.sendServerMessage(current_line)
                current_line = item
            else:
                current_line += " " + item
        if plain:
            self.sendNormalMessage(current_line)
        else:
            self.sendServerMessage(current_line)

    def sendSplitServerMessage(self, message):
        linelen = 63
        lines = []
        thisline = ""
        words = message.split()
        for x in words:
            if len(thisline + " " + x) < linelen:
                thisline = thisline + " " + x
            else:
                lines.append(thisline)
                thisline = x
        if thisline != "":
            lines.append(thisline)
        for line in lines:
            self.sendServerMessage(line)

    def splitMessage(self, message, linelen=63):
        lines = []
        thisline = ""
        words = message.split()
        for x in words:
            if len(thisline + " " + x) < linelen:
                thisline = thisline + " " + x
            else:
                lines.append(thisline)
                thisline = x
        if thisline != "":
            lines.append(thisline)
        return lines

    def sendNewPlayer(self, id, username, x, y, z, h, p):
        self.sendPacked(TYPE_SPAWNPOINT, id, username, x, y, z, h, p)

    def sendPlayerLeave(self, id,):
        self.sendPacked(TYPE_PLAYERLEAVE, id)

    def sendKeepAlive(self):
        if self.connected:
            self.sendPacked(TYPE_KEEPALIVE)
            reactor.callLater(1, self.sendKeepAlive)

    def sendOverload(self):
        "Sends an overload - a fake world designed to use as much memory as it can."
        self.sendPacked(TYPE_INITIAL, 7, "Loading...", "Entering world 'default'...", 0)
        self.sendPacked(TYPE_PRECHUNK)
        reactor.callLater(0.001, self.sendOverloadChunk)

    def sendOverloadChunk(self):
        "Sends a level chunk full of 1s."
        if self.connected:
            self.sendPacked(TYPE_CHUNK, 1024, "\1"*1024, 50)
            reactor.callLater(0.001, self.sendOverloadChunk)

    def sendLevel(self):
        "Starts the process of sending a level to the client."
        self.factory.recordPresence(self.username)
        # Ask the World to flush the level and get a gzip handle back to us.
        if hasattr(self, "world"):
            self.world.get_gzip_handle().addCallback(self.sendLevelStart)

    def sendLevelStart(self, (gzip_handle, zipped_size)):
        "Called when the world is flushed and the gzip is ready to read."
        # Store that handle and size
        self.zipped_level, self.zipped_size = gzip_handle, zipped_size
        # Preload our first chunk, send a level stream header, and go!
        self.chunk = self.zipped_level.read(1024)
        self.factory.logger.debug("Sending level...")
        self.sendPacked(TYPE_PRECHUNK)
        reactor.callLater(0.001, self.sendLevelChunk)

    def sendLevelChunk(self):
        if not hasattr(self, 'chunk'):
            self.factory.logger.error("Cannot send chunk, there isn't one! %r %r" % (self, self.__dict__))
            return
        if self.chunk:
            self.sendPacked(TYPE_CHUNK, len(self.chunk), self.chunk, chr(int(100*(self.zipped_level.tell()/float(self.zipped_size)))))
            self.chunk = self.zipped_level.read(1024)
            reactor.callLater(0.001, self.sendLevelChunk)
        else:
            self.zipped_level.close()
            del self.zipped_level
            del self.chunk
            del self.zipped_size
            self.endSendLevel()

    def endSendLevel(self):
        self.factory.logger.debug("Sent level data.")
        self.sendPacked(TYPE_LEVELSIZE, self.world.x, self.world.y, self.world.z)
        sx, sy, sz, sh = self.world.spawn
        self.p = 0
        self.loading_world = False
        # If we have a custom point set (teleport, tp), use that
        if self.initial_position:
            try:
                sx, sy, sz, sh = self.initial_position
            except ValueError:
                sx, sy, sz = self.initial_position
                sh = 0
            self.initial_position = None
        self.x = (sx<<5)+16
        self.y = (sy<<5)+16
        self.z = (sz<<5)+16
        self.h = int(sh*255/360.0)
        self.sendPacked(TYPE_SPAWNPOINT, chr(255), "", self.x, self.y, self.z, self.h, 0)
        self.sendAllNew()
        self.factory.queue.put((self, TASK_NEWPLAYER, (self.id, self.colouredUsername(), self.x, self.y, self.z, self.h, 0)))
        self.sendWelcome()

    def sendAllNew(self):
        "Sends a 'new user' notification for each new user in the world."
        for client in self.world.clients:
            if client is not self and hasattr(client, "x"):
                self.sendNewPlayer(client.id, client.userColour() + client.username, client.x, client.y, client.z, client.h, client.p)

    def sendWelcome(self):
        if not self.sent_first_welcome:
            for line in self.factory.greeting:
                self.sendPacked(TYPE_MESSAGE, 127, line)
            self.sent_first_welcome = True
            self.runHook("playerjoined", self.username)
            self.MessageAlert()
        else:
            self.sendPacked(TYPE_MESSAGE, 255, "You are now in world '%s'" % self.world.id)

    def AllowedToBuild(self,x,y,z):
        build = False
        assigned = []
        try:
            check_offset = self.world.blockstore.get_offset(x, y, z)
            block = ord(self.world.blockstore.raw_blocks[check_offset])
        except:
            self.sendServerMessage("Out of bounds.")
            return False
        if block == BLOCK_SOLID and not self.isOp():
            return False
        for id, zone in self.world.userzones.items():
            x1, y1, z1, x2, y2, z2 = zone[1:7]
            if x1 < x < x2:
                if y1 < y < y2:
                    if z1 < z < z2:
                        if len(zone) > 7:
                            if self.username.lower() in zone[7:] or self.isDirector():
                                build = True
                            else:
                                assigned = zone[7:]
                        else:
                            return False
        if build:
            return True
        elif assigned:
            self.sendServerList(["You are not allowed to build in this zone. Only:"]+assigned+["may."])
            return False
        for id, zone in self.world.rankzones.items():
            if "all" == zone[7]:
                x1, y1, z1, x2, y2, z2 = zone[1:7]
                if x1 < x < x2:
                    if y1 < y < y2:
                        if z1 < z < z2:
                            return True
            if self.world.zoned:
                if "builder" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isBuilder():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "op" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isOp():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "worldowner" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isWorldOwner():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "member" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isMember():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "mod" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isMod():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "admin" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isAdmin():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "director" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isDirector():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
                if "owner" == zone[7]:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    if x1 < x < x2:
                        if y1 < y < y2:
                            if z1 < z < z2:
                                if self.isOwner():
                                    return True
                                else:
                                    self.sendServerMessage("You must be "+zone[7]+" to build here.")
                                    return False
        if self.world.id == self.factory.default_name and self.isHelper() and not self.isMod() and not self.world.all_write:
            self.sendBlock(x, y, z)
            self.sendServerMessage("Only Builder/Op and Mod+ may edit '%s'." % self.factory.default_name)
            return
        if not self.world.all_write and self.isBuilder() or self.isOp():
            return True
        if self.world.all_write:
            return True
        self.sendServerMessage("This world is locked. You must be Builder/Op or Mod+ to build here.")
        return False

    def GetBlockValue(self, value):
        # Try getting the block as a direct integer type.
        try:
            block = chr(int(value))
        except ValueError:
            # OK, try a symbolic type.
            try:
                block = chr(globals()['BLOCK_%s' % value.upper()])
            except KeyError:
                self.sendServerMessage("'%s' is not a valid block type." % value)
                return None
                    # Check the block is valid
        if ord(block) > 49:
            self.sendServerMessage("'%s' is not a valid block type." % value)
            return None
        op_blocks = [BLOCK_SOLID, BLOCK_WATER, BLOCK_LAVA]
        if ord(block) in op_blocks and not self.isOp():
            self.sendServerMessage("Sorry, but you can't use that block.")
            return
        return block

    def MessageAlert(self):
        if os.path.exists("config/data/inbox.dat"):
            self.messages = self.factory.messages
            for client in self.factory.clients.values():
                if client.username in self.messages:
                    client.sendServerMessage("You have a message waiting in your Inbox.")
                    client.sendServerMessage("Use /inbox to check and see.")

    def getBlbLimit(self, factor=1):
        """Fetches BLB Limit, and returns limit multiplied by a factor. 0 is returned if blb is disabled for that usergroup, and -1 for no limit."""
        if self.factory.useblblimit:
            if self.isSpectator():
               limit = 0
            elif self.isOwner():
                limit = self.factory.blblimit["owner"]
            elif self.isDirector():
                limit = self.factory.blblimit["director"]
            elif self.isAdmin():
                limit = self.factory.blblimit["admin"]
            elif self.isMod():
                limit = self.factory.blblimit["mod"]
            elif self.isHelper():
                limit = self.factory.blblimit["mod"]
            elif self.isWorldOwner():
                limit = self.factory.blblimit["worldowner"]
            elif self.isOp():
                limit = self.factory.blblimit["op"]
            elif self.isBuilder():
                limit = self.factory.blblimit["builder"]
            else:
                limit = self.factory.blblimit["player"]
        else:
            if self.isSpectator():
                limit = 0
            elif self.isOwner():
                limit = 8796093022208
            elif self.isDirector():
                limit = 2199023255552
            elif self.isAdmin():
                limit = 1073741824
            elif self.isMod():
                limit = 2097152
            elif self.isHelper():
                limit = 262144
            elif self.isWorldOwner():
                limit = 176128
            elif self.isOp():
                limit = 110592
            elif self.isBuilder():
                limit = 8124
            else:
                limit = 128
        if limit > -1:
            limit *= factor
        return limit

    def loadRank(self):
        return self.factory.rank_dic