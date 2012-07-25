# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, datetime, gc, os, re, shutil, string, sys, time, traceback
from collections import defaultdict
import ConfigParser
from Queue import Queue, Empty

try:
    import OpenSSL
except:
    NOSSL = True
else:
    from twisted.internet import ssl
from twisted.internet import defer, reactor, task
from twisted.internet.protocol import Factory

from arc.console import Console
from arc.constants import *
from arc.globals import *
from arc.heartbeat import Heartbeat
from arc.irc_client import ChatBotFactory
from arc.logger import ColouredLogger, ChatLogHandler
from arc.protocol import ArcServerProtocol
from arc.world import World

class ArcFactory(Factory):
    """
    Factory that deals with the general world actions and cross-user comms.
    """
    protocol = ArcServerProtocol

    def __init__(self, debug=False):
        self.printable = string.printable
        self.logger = ColouredLogger(debug)
        self.cfginfo = {"version": defaultdict(str)}
        self.plugins = {} # {"Name": class()}
        self.commands = {}
        self.hooks = {}
        self.aliases = {}
        # Load up the plugins specified
        self.plugins_config = ConfigParser.RawConfigParser()
        try:
            self.plugins_config.read("config/plugins.conf")
        except Exception as e:
            self.logger.error("Unable to read plugins.conf (%s)" % e)
            sys.exit(1)
        try:
            plugins = self.plugins_config.options("plugins")
        except Exception as e:
            print ("Error parsing plugins.conf: %s" % e)
            sys.exit(1)
        self.loadPlugins(plugins)
        self.logger.info("Loaded plugins.")
        # Initialise internal datastructures
        self.loops = {}
        self.worlds = {}
        self.owners = set()
        self.directors = set()
        self.admins = set()
        self.mods = set()
        self.helpers = set()
        self.spectators = set()
        self.silenced = set()
        self.banned = {}
        self.ipbanned = {}
        self.lastseen = {}
        self.default_loaded = False
        self.useLowLag = False
        self.saving = False
        self.chatlogs = {}
        for k, v in MSGLOGFORMAT.items():
            self.chatlogs[k] = ChatLogHandler("logs/%s.log" % k, v)
        # Load the config
        self.loadConfig()
        # Read in the greeting
        try:
            r = open('config/greeting.txt', 'r')
        except:
            r = open('config/greeting.example.txt', 'r')
        self.greeting = r.readlines()
        r.close()
        self.use_irc = False
        if (os.path.exists("config/irc.conf")): # IRC bot will be updated soon, no need for cfginfo
            self.use_irc = True
            self.irc_config = ConfigParser.RawConfigParser()
            try:
                self.irc_config.read("config/irc.conf")
            except Exception as a:
                self.logger.error("Unable to read irc.conf (%s)" % a)
                sys.exit(1)
        if self.use_irc:
            try:
                self.irc_nick = self.irc_config.get("irc", "nick")
                self.irc_pass = self.irc_config.get("irc", "password")
                self.irc_channel = self.irc_config.get("irc", "channel")
                self.irc_cmdlogs = self.irc_config.getboolean("irc", "cmdlogs")
                self.ircbot = self.irc_config.getboolean("irc", "ircbot")
                self.staffchat = self.irc_config.getboolean("irc", "staffchat")
                self.irc_relay = ChatBotFactory(self)
                if self.ircbot and not self.irc_channel == "#channel" and not self.irc_nick == "botname":
                    reactor.connectTCP(self.irc_config.get("irc", "server"), self.irc_config.getint("irc", "port"),
                        self.irc_relay)
                else:
                    self.logger.error("IRC Bot failed to connect, you could modify, rename or remove irc.conf")
                    self.logger.error(
                        "You need to change your 'botname' and 'channel' fields to fix this error or turn the bot off by disabling 'ircbot'")
            except Exception as e:
                self.logger.warn("Error parsing irc.conf (%s)" % e)
                self.logger.warn("IRC bot will not be started.")
                self.irc_relay = None
        else:
            self.irc_relay = None
        self.runHook("configLoaded")
        # Open the chat log, ready for appending
        self.chatlog = open("logs/chat.log", "a")
        # Create a default world, if there isn't one.
        if not os.path.isdir("worlds/%s" % self.default_name):
            self.logger.info("Generating %s world..." % self.default_name)
            sx, sy, sz = 64, 64, 64
            grass_to = (sy // 2)
            world = World.create(
                "worlds/%s" % self.default_name,
                sx, sy, sz, # Size
                sx // 2, grass_to + 2, sz // 2, 0, # Spawn
                ([BLOCK_DIRT] * (grass_to - 1) + [BLOCK_GRASS] + [BLOCK_AIR] * (sy - grass_to)) # Levels
            )
            self.logger.info("Generated.")
            # Load up the contents of data.
        self.loadMeta()
        # Set up a few more things.
        self.queue = Queue()
        self.clients = {}
        self.usernames = {}

    def loadConfig(self, reload=False):
        configParsers = dict()
        for config in CONFIG:
            if reload and config[3] == False:
                # Non-dynamic
                continue
            if not config[1][0] in configParsers.keys():
                # Create an instance of ConfigParser if we don't already have one
                configParsers[config[1][0]] = ConfigParser.RawConfigParser()
                try:
                    self.logger.debug("Reading file config/%s..." % config[1][0])
                    configParsers[config[1][0]].read("config/%s" % config[1][0])
                except Exception as e:
                    self.logger.error("Unable to read %s (%s)" % (config[1][0], e))
                    sys.exit(1)
                    # Check Config version
                if config[1][0] in CFGVERSION:
                    if configParsers[config[1][0]].has_section("cfginfo"):
                        self.cfginfo["version"][config[1][0]] = configParsers[config[1][0]].get("cfginfo", "version")
                    else:
                        # No config version - unacceptable! Exit
                        self.logger.error("File %s has no config version. Unable to continue." % config[1][0])
                        sys.exit(1)
                if not checkConfigVersion(self.cfginfo["version"][config[1][0]], CFGVERSION[config[1][0]]):
                    if config[1][0] in CFGVERSION:
                        # Inside official dist
                        self.logger.error("You have an outdated %s, please redownload the Arc package and fill in the configuration again." %
                            config[1][0])
                        sys.exit(1)
                    else:
                        # Plugin
                        self.logger.error("You have an outdated %s, please contact the plugin author." % config[1][0])
                        sys.exit(1)
                # Any prerequistics?
            if config[2] != None:
                evaluate = eval(config[2], {"self": self})
                self.logger.debug("Criteria result: %s" % str(evaluate))
                if not evaluate:
                    self.logger.debug("Criteria not met. Skipping.")
                    self.logger.debug("Criteria: %s" % config[2])
                    continue
                # Get the correct ConfigParser method
            valueFunc = getattr(configParsers[config[1][0]], config[4])
            theError = 0
            if config[4] == "options":
                try:
                    value = valueFunc(config[1][1])
                except ConfigParser.NoSectionError as e:
                    theError = 1
            else:
                try:
                    value = valueFunc(config[1][1], config[1][2])
                except ConfigParser.NoSectionError as e:
                    # If there's a default value, use that
                    if not config[6]:
                        value = config[7]
                    else:
                        theError = 1
                except ConfigParser.NoOptionError as e:
                    if not config[6]:
                        value = config[7]
                    else:
                        theError = 2
            if theError in [1, 2]:
                self.logger.error("Unable to read config %s." % config[1][2])
                self.logger.error(str(e))
                sys.exit(1)
            else:
                try:
                    setattr(self, config[0], value)
                except Exception as e:
                    self.logger.error("Unable to set %s (%s)" % (config[0], e))
                    sys.exit(1)
                else:
                    if config[5] != None:
                        try:
                            callbackFunc = getattr(self, config[5])
                            callbackFunc(reload=reload)
                        except Exception as e:
                            self.logger.error("Unable to run callback function %s!" % config[5])
                            self.logger.error(traceback.format_exc())
                    self.logger.debug("Loaded config %s." % config[0])

    # Dummy callback functions until I figure out a better way to do all of these

    def checkSalt(self, reload):
        if self.salt in ["", "Select this text and mash your keyboard."]:
            self.logger.critical("Salt is required.")
            sys.exit(1)

    def modifyHeartbeatURL(self, reload):
        "Called to recheck URL."
        if reload:
            self.heartbeat.hburl = "http://www.minecraft.net/heartbeat.jsp" if not self.factory.wom_heartbeat else "http://direct.worldofminecraft.com/hb.php"

    def startASDLoop(self, reload):
        "Called to start the ASD loop."
        if reload:
            self.loops["asd"].stop()
        if self.asd_delay != 0:
            if "asd" in self.loops:
                del self.loops["asd"]
            self.loops["asd"] = task.LoopingCall(self.checkASD)
            self.loops["asd"].start(60, now=False)
            self.logger.info("ASD Checking process initialized.")

    def initBackupLoop(self, reload):
        "Called to initialize the backup loop."
        if reload:
            self.loops["autobackup"].stop()
        elif self.backup_auto != False:
            self.loops["autobackup"] = task.LoopingCall(self.autoBackup)

    def modifyBackupFrequency(self, reload):
        "Called to start the backup loop."
        if reload:
            self.loops["autobackup"].stop()
        elif self.backup_auto != False:
            self.loops["autobackup"].run(self.backup_freq, now=False)

    def enableArchiver(self, reload):
        if reload:
            self.loops["loadarchives"].stop()
        elif self.enable_archives != False:
            self.loops["loadarcives"] = task.LoopingCall(self.loadArchives)
            self.loops["loadarcives"].start(300)

    def initBLBLimiter(self, reload):
        if not self.useblblimit:
            if reload:
                del self.blblimit
            return
        self.blblimit = {}
        config = ConfigParser.RawConfigParser()
        config.read("config/options.conf") # This can't fail because it has been checked before
        self.blblimit["player"] = config.getint("blb", "player")
        self.blblimit["builder"] = config.getint("blb", "builder")
        self.blblimit["op"] = config.getint("blb", "op")
        self.blblimit["worldowner"] = config.getint("blb", "worldowner")
        self.blblimit["helper"] = config.getint("blb", "helper")
        self.blblimit["mod"] = config.getint("blb", "mod")
        self.blblimit["admin"] = config.getint("blb", "admin")
        self.blblimit["director"] = config.getint("blb", "director")
        self.blblimit["owner"] = config.getint("blb", "owner")

    # End of dummy callbacks
    def loadPlugins(self, plugins, cleardata=True):
        """Loads a set of plugins."""
        if cleardata:
            self.hooks = {} # Clear the list of hooks
            self.commands = {} # Clear the list of server commands
            self.aliases = {} # Clear the list of server command aliases
        self.logger.info("Loading plugins..")
        for plugin in plugins:
            self.loadPlugin(plugin)
        self.runHook("pluginsLoaded")

    def loadPlugin(self, plugin, client=None):
        """Loads a plugin."""
        if "arc.plugins.%s" % plugin in sys.modules.keys(): # Check if we already imported it
            self.logger.error("Plugin %s is already imported. Skipping." % plugin)
            if client: client.sendServerMessage("Plugin %s is already imported." % plugin)
            return
        if not os.path.exists("arc/plugins/%s.py" % plugin):
            self.logger.error("Plugin %s does not exist." % plugin)
            if client: client.sendServerMessage("Plugin %s does not exist." % plugin)
            return
        #try:
        __import__("arc.plugins.%s" % plugin) # If not, import it
        #except Exception as a: # Got an error!
        #    self.logger.error("Unable to load plugin from %s.py!" % plugin)
        #    self.logger.error("Error: %s" % a)
        #    self.logger.error(traceback.format_exc())
        #    if client: client.sendServerMessage("Unable to load plugin from %s.py." % plugin)
        #    return
        try:
            mod = sys.modules["arc.plugins.%s" % plugin].serverPlugin()
            mod.name = mod.__class__.__name__ # What's the name?
            mod.factory = self
            mod.logger = self.logger
            if hasattr(mod, "gotServer"): mod.gotServer()
            if hasattr(self, "usernames"): # If this throws an AttributeError, we are booting up
                if hasattr(mod, "hooks"):
                    if "onPlayerConnect" in mod.hooks.keys():
                        pc_hook = getattr(mod, mod.hooks["onPlayerConnect"])
                        for p in self.usernames.values():
                            pc_hook(p)
        except Exception as a:
            self.logger.error("Unable to load plugin from %s.py" % plugin)
            self.logger.error("Error: %s" % a)
            if client: client.sendServerMessage("Unable to load plugin from %s.py." % plugin)
            return
        self.plugins[plugin] = mod # Put it in the plugins list
        self.logger.debug("Getting hooks and commands for plugin %s.." % plugin)
        if hasattr(mod, "hooks"):
            for element, fname in mod.hooks.items(): # For every hook in the plugin,
                try:
                    func = getattr(mod, fname)
                except AttributeError:
                    self.logger.warn("Cannot find hook code for hook %s (plugin is %s)." % (element, mod))
                    if client:
                        client.sendSplitServerMessage("Cannot find hook code for hook %s (plugin is %s). Skipping..." % (element, mod))
                    continue
                if element not in self.hooks.keys():
                    self.hooks[element] = [] # Make a note of the hook in the hooks dict
                self.hooks[element].append([mod, getattr(mod, fname)])
                self.logger.debug("Loaded hook '%s' for plugin '%s'." % (element, mod.name))
        if hasattr(mod, "commands"):
            for element, data in mod.commands.items():
                try:
                    func = getattr(mod, data)
                except AttributeError:
                    self.logger.warn("Cannot find command code for command %s (plugin is %s)." % (element, plugin))
                    if client:
                        client.sendSplitServerMessage("Cannot find command code for command %s (plugin is %s). Skipping..." % (element, plugin))
                    continue
                if element in self.commands.keys():
                    self.logger.warn("Command %s is already registered. Overriding." % element)
                self.commands[element] = func
                if hasattr(func, "config"):
                    for alias in func.config["aliases"]:
                        if alias in self.aliases:
                            self.logger.warn("Alias %s is already registered. Overriding." % alias)
                        if client: client.sendServerMessage("Alias %s is already registered. Overriding." % alias)
                        self.aliases[alias] = element
                self.logger.debug("Loaded command '%s' for plugin '%s'." % (element, mod.name))
        self.logger.info("Plugin %s loaded." % plugin)
        if client: client.sendServerMessage("Plugin %s loaded." % plugin)
        self.runHook("pluginLoaded", {"plugin": plugin, "client": client})

    def unloadPlugin(self, plugin, client=None):
        """Unloads a plugin."""
        if not ("arc.plugins.%s" % plugin in sys.modules.keys()): # Check if we have imported it
            self.logger.error("Plugin %s is not loaded." % plugin)
            if client: client.sendServerMessage("Plugin %s is not loaded." % plugin)
            return
        mod = self.plugins[plugin]
        if hasattr(mod, "properties"):
            if "allow-unload" in mod.properties:
                if not mod.properties["allow-unload"]:
                    self.logger.error("Plugin %s does not allow unloading." % plugin)
                    if client: client.sendServerMessage("Plugin %s does not allow unloading." % plugin)
                    return
        if hasattr(mod, "tearDown"):
            mod.tearDown()
        self.logger.debug("Unloading all hooks and commands for plugin %s.." % plugin)
        if hasattr(mod, "hooks"):
            for element, fname in mod.hooks.items(): # For every hook in the plugin,
                if element in self.hooks.keys():
                    del self.hooks[element]
                self.logger.debug("Unloaded hook '%s' for plugin '%s'." % (element, mod.name))
        if hasattr(mod, "commands"):
            for element, data in mod.commands.items():
                func = self.commands[element]
                if hasattr(func, "config"):
                    for alias in func.config["aliases"]:
                        if alias in self.aliases:
                            del self.aliases[alias]
                del self.commands[element]
                self.logger.debug("Unloaded command '%s' for plugin '%s'." % (element, mod.name))
        del mod, self.plugins[plugin], sys.modules["arc.plugins.%s" % plugin] # Unimport it by deleting it
        self.logger.info("Plugin %s unloaded." % plugin)
        if client: client.sendServerMessage("Plugin %s unloaded." % plugin)
        self.runHook("pluginUnloaded", {"plugin": plugin, "client": client})

    def reloadPlugin(self, plugin, client=None):
        """Reloads a plugin."""
        if not ("arc.plugins.%s" % plugin in sys.modules.keys()): # Check if we have imported it
            self.logger.error("Plugin %s is not loaded." % plugin)
            if client: client.sendServerMessage("Plugin %s is not loaded." % plugin)
            return
        mod = self.plugins[plugin]
        if hasattr(mod, "properties"):
            if "allow-reload" in mod.properties:
                if not mod.properties["allow-reload"]:
                    self.logger.error("Plugin %s does not allow reloading." % plugin)
                    if client: client.sendServerMessage("Plugin %s does not allow reloading." % plugin)
                    return
        self.unloadPlugin(plugin, client)
        self.loadPlugin(plugin, client)

    def serverPluginExists(self, plugin):
        return plugin in self.plugins.keys()

    def runCommand(self, command, parts, fromloc, overriderank, client=None, username=None):
        data = {"client": client, "command": command, "parts": parts, "fromloc": fromloc, "overriderank": overriderank}
        if fromloc in ["user", "cmdblock"]: # User
            user = client.username
            def sendMessage(message):
                client.sendServerMessage(message)
        elif fromloc in ["irc", "irc_query"]: # IRC client
            user = username if username != None else "IRC Client"
            def sendMessage(message):
                if username != None: # If we overrided the username
                    client.msg(username, message)
                else: # Else send this as a server message
                    self.irc_relay.sendServerMessage(message)
        elif fromloc == "console":
            user = "Console"
            def sendMessage(message):
                print(message)
        else: # Where does this come from?
            self.logger.warn("Unknown source tried to run a command.")
            self.logger.warn("Command: %s, fromloc: %s, client: %s" % (command, fromloc, repr(client)))
            return
        if command in self.commands.keys():
            func = self.commands[command]
        elif command in self.aliases.keys():
            func = self.commands[self.aliases[command]]
        else: # Nope, did't find it
            sendMessage("Command %s does not exist." % command)
            return
        if hasattr(func, "config"):
            config = func.config
        else:
            config = {"aliases": "", "usage": "", "rank": "guest", "disabled-on": "", "category": ""}
        # Check if the command can be run from that source.
        if fromloc == "user" and "user" in config["disabled-on"]:
            sendMessage("This command cannot be run from the game.")
            self.logger.info("%s just tried '%s' but it has been disabled for in-game users." % (user, " ".join(parts)))
            return
        elif fromloc == "cmdblock" and "cmdblock" in config["disabled-on"]:
            sendMessage("This command cannot be run from a cmdblock.")
            self.logger.info("%s just tried '%s' but it has been disabled for CMD Block usage." % (user, " ".join(parts)))
            return
        elif fromloc == "irc" and "irc" in config["disabled-on"]:
            sendMessage("This command cannot be run from the IRC Client.")
            self.logger.info("%s just tried '%s' but it has been disabled for the IRC Client." % (user, " ".join(parts)))
            return
        elif fromloc == "irc_query" and "irc_query" in config["disabled-on"]:
            sendMessage("This command cannot be run from an IRC query.")
            self.logger.info("%s just tried '%s' but it has been disabled from an IRC query." % (user, " ".join(parts)))
            return
        elif fromloc == "console" and "console" in config["disabled-on"]:
            sendMessage("This command cannot be run from the console.")
            return
        if config["disabled"] and (fromloc == "user" and not client.isOwner()): # Owners and server can run anything 
            sendMessage("Command %s has been disabled by the server owner." % command)
            self.logger.info("%s just tried '%s' but it has been disabled." % (user, " ".join(parts)))
            return
        if fromloc == "user": # Rank checking for in-game users
            if client.isSpectator() and config["rank"]:
                sendMessage("'%s' is not available to spectators." % command)
                self.logger.info("%s just tried '%s' but is a spectator." % (user, " ".join(parts)))
                return
            if config["rank"] == "owner" and not client.isOwner():
                sendMessage("'%s' is an Owner-only command!" % command)
                self.logger.info("%s just tried '%s' but is not an owner." % (user, " ".join(parts)))
                return
            if config["rank"] == "director" and not client.isDirector():
                sendMessage("'%s' is a Director-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a director." % (user, " ".join(parts)))
                return
            if config["rank"] == "admin" and not client.isAdmin():
                sendMessage("'%s' is an Admin-only command!" % command)
                self.logger.info("%s just tried '%s' but is not an admin." % (user, " ".join(parts)))
                return
            if config["rank"] == "mod" and not client.isMod():
                sendMessage("'%s' is a Mod-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a mod." % (user, " ".join(parts)))
                return
            if config["rank"] == "helper" and not client.isHelper():
                sendMessage("'%s' is a Helper-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a helper." % (user, " ".join(parts)))
                return
            if config["rank"] == "worldowner" and not client.isWorldOwner():
                sendMessage("'%s' is an WorldOwner-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a world owner." % (user, " ".join(parts)))
                return
            if config["rank"] == "op" and not client.isOp():
                sendMessage("'%s' is an Op-only command!" % command)
                self.logger.info("%s just tried '%s' but is not an op." % (user, " ".join(parts)))
                return
            if config["rank"] == "builder" and not client.isBuilder():
                sendMessage("'%s' is a Builder-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a builder." % (user, " ".join(parts)))
                return
        elif fromloc == "irc" or fromloc == "irc_query":
            if not username in self.irc_relay.instance.ops:
                sendMessage("'%s' is an channelop-only command!" % command)
                self.logger.info("%s just tried '%s' but is not a channel operator." % (user, " ".join(parts)))
                return
        # Using custom message?
        if config["custom_cmdlog_msg"]:
            self.logger.command("%s %s" % (user, config["custom_cmdlog_msg"]))
            if self.irc_relay and self.irc_cmdlogs:
                self.irc_relay.sendServerMessage("%s %s" % (user, config["custom_cmdlog_msg"]))
        else:
            self.logger.command("(%s) /%s" % (user, " ".join(parts)))
            if self.irc_relay and self.irc_cmdlogs:
                self.irc_relay.sendServerMessage("%s just used: /%s" % (user, " ".join(parts)))
        try:
            func(data)
        except Exception as e:
            sendMessage("Unable to run that command!")
            sendMessage("Error: %s" % e)
            sendMessage("Please report this to the staff!")
            self.logger.error("Error in command '%s': %s" % (command.title(), e))
            error = traceback.format_exc()
            errorsplit = error.split("\n")
            for element in errorsplit:
                if not element.strip(" ") == "":
                    self.logger.error(element)

    def runHook(self, hook, data=None):
        """Used to run hooks for plugins"""
        finaldata = []
        if hook in self.hooks.keys():
            for element in self.hooks[hook]:
                self.logger.debug("Ran hook %s" % hook)
                if data is not None:
                    value = element[1](data)
                else:
                    value = element[1]()
                if value is not None:
                    return value
        return None # Stupid workaround, need to fix

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        self.runHook("protocolBuilt")
        return p

    def startFactory(self):
        self.console = Console(self)
        self.console.start()
        self.runHook("consoleLoaded")
        self.heartbeat = Heartbeat(self)
        self.runHook("heartbeatStarted")
        # Boot default
        self.loadWorld("worlds/%s" % self.default_name, self.default_name)
        # Set up tasks to run during execution
        self.loops["sendmessages"] = task.LoopingCall(self.sendMessages)
        self.loops["sendmessages"].start(0.1)
        self.loops["printinfo"] = task.LoopingCall(self.printInfo)
        self.loops["printinfo"].start(60)
        # Initial startup is instant, but it updates every 10 minutes.
        self.world_save_stack = []
        self.loops["saveworlds"] = task.LoopingCall(self.saveWorlds)
        self.loops["saveworlds"].start(60, now=False)
        gc.disable()
        self.loops["cleangarbage"] = task.LoopingCall(self.cleanGarbage)
        self.loops["cleangarbage"].start(60 * 15)
        self.runHook("factoryStarted")

    def cleanGarbage(self):
        count = gc.collect()
        self.logger.info("%i garbage objects collected, %i were uncollected." % (count, len(gc.garbage)))
        self.runHook("garbageCollected", {"collected": count, "uncollected": len(gc.garbage)})

    def checkASD(self):
        for world in self.worlds.values():
            if world.id == self.default_name:
                continue
            elif not world.status["autoshutdown"]:
                continue
            if world.status["last_access_count"] >= self.asd_delay:
                name = world.id
                self.unloadWorld(name)
            else:
                if len(world.clients) == 0: # Nobody's in it
                    world.status["last_access_count"] += 1

    def loadMeta(self):
        "Loads the 'meta' - variables that change with the server (worlds, admins, etc.)"
        config = ConfigParser.RawConfigParser()
        specs = ConfigParser.RawConfigParser()
        lastseen = ConfigParser.RawConfigParser()
        bans = ConfigParser.RawConfigParser()
        try:
            config.read("config/data/ranks.meta")
            specs.read("config/data/spectators.meta")
            lastseen.read("config/data/lastseen.meta")
            bans.read("config/data/bans.meta")
        except ConfigParser.MissingSectionHeaderError as e: # This happens when the server crashes, but is rare
            self.logger.critical("One of the .metas are corrupt.")
            self.logger.critical(str(e))
            sys.exit(1)
        if config.has_section("cfginfo"):
            # Config version?
            self.cfginfo["version"]["ranks.meta"] = config.get("cfginfo", "version")
        else:
            self.cfginfo["version"]["ranks.meta"] = "1.0.0"
        if specs.has_section("cfginfo"):
            # Config version?
            self.cfginfo["version"]["spectators.meta"] = specs.get("cfginfo", "version")
        else:
            self.cfginfo["version"]["spectators.meta"] = "1.0.0"
        if lastseen.has_section("cfginfo"):
            # Config version?
            self.cfginfo["version"]["lastseen.meta"] = lastseen.get("cfginfo", "version")
        else:
            self.cfginfo["version"]["lastseen.meta"] = "1.0.0"
        if bans.has_section("cfginfo"):
            # Config version?
            self.cfginfo["version"]["bans.meta"] = bans.get("cfginfo", "version")
        else:
            self.cfginfo["version"]["bans.meta"] = "1.0.0"
        if not checkConfigVersion(self.cfginfo["version"]["ranks.meta"], CFGVERSION["ranks.meta"]):
            self.logger.error(
                "You have an outdated ranks.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["spectators.meta"], CFGVERSION["spectators.meta"]):
            self.logger.error(
                "You have an outdated spectators.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["lastseen.meta"], CFGVERSION["lastseen.meta"]):
            self.logger.error(
                "You have an outdated lastseen.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["bans.meta"], CFGVERSION["bans.meta"]):
            self.logger.error(
                "You have an outdated bans.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
            # Read in the admins
        if config.has_section("admins"):
            for name in config.options("admins"):
                self.admins.add(name)
            # Read in the mods
        if config.has_section("mods"):
            for name in config.options("mods"):
                self.mods.add(name)
        if config.has_section("helpers"):
            for name in config.options("helpers"):
                self.helpers.add(name)
            # Read in the directors
        if config.has_section("directors"):
            for name in config.options("directors"):
                self.directors.add(name)
            # Read in the owners
        if config.has_section("owners"):
            for name in config.options("owners"):
                self.owners.add(name)
        if config.has_section("silenced"):
            for name in config.options("silenced"):
                self.silenced.add(name)
            # Read in the spectators
        if specs.has_section("spectators"):
            for name in specs.options("spectators"):
                self.spectators.add(name)
            # Read in the bans
        if bans.has_section("banned"):
            for name in bans.options("banned"):
                self.banned[name] = bans.get("banned", name)
            # Read in the ipbans
        if bans.has_section("ipbanned"):
            for ip in bans.options("ipbanned"):
                self.ipbanned[ip] = bans.get("ipbanned", ip)
            # Read in the lastseen
        if lastseen.has_section("lastseen"):
            for username in lastseen.options("lastseen"):
                self.lastseen[username] = lastseen.getfloat("lastseen", username)
        self.runHook("metaLoaded")

    def saveMeta(self):
        "Saves the server's meta back to a file."
        config = ConfigParser.RawConfigParser()
        specs = ConfigParser.RawConfigParser()
        lastseen = ConfigParser.RawConfigParser()
        bans = ConfigParser.RawConfigParser()
        # Make the sections
        config.add_section("cfginfo")
        config.add_section("owners")
        config.add_section("directors")
        config.add_section("admins")
        config.add_section("mods")
        config.add_section("helpers")
        config.add_section("silenced")
        bans.add_section("cfginfo")
        bans.add_section("banned")
        bans.add_section("ipbanned")
        specs.add_section("cfginfo")
        specs.add_section("spectators")
        lastseen.add_section("cfginfo")
        lastseen.add_section("lastseen")
        # Write out things
        for owner in self.owners:
            config.set("owners", owner, "true")
        for director in self.directors:
            config.set("directors", director, "true")
        for admin in self.admins:
            config.set("admins", admin, "true")
        for mod in self.mods:
            config.set("mods", mod, "true")
        for helper in self.helpers:
            config.set("helpers", helper, "true")
        for ban, reason in self.banned.items():
            bans.set("banned", ban, reason)
        for spectator in self.spectators:
            specs.set("spectators", spectator, "true")
        for silence in self.silenced:
            config.set("silenced", silence, "true")
        for ipban, reason in self.ipbanned.items():
            bans.set("ipbanned", ipban, reason)
        for username, ls in self.lastseen.items():
            lastseen.set("lastseen", username, str(ls))
        config.set("cfginfo", "name", "ranks.meta")
        config.set("cfginfo", "version", self.cfginfo["version"]["ranks.meta"])
        bans.set("cfginfo", "name", "bans.meta")
        bans.set("cfginfo", "version", self.cfginfo["version"]["bans.meta"])
        specs.set("cfginfo", "name", "spectators.meta")
        specs.set("cfginfo", "version", self.cfginfo["version"]["spectators.meta"])
        lastseen.set("cfginfo", "name", "lastseen.meta")
        lastseen.set("cfginfo", "version", self.cfginfo["version"]["lastseen.meta"])
        fp = open("config/data/ranks.meta", "w")
        config.write(fp)
        fp.close()
        fp = open("config/data/spectators.meta", "w")
        specs.write(fp)
        fp.close()
        fp = open("config/data/lastseen.meta", "w")
        lastseen.write(fp)
        fp.close()
        fp = open("config/data/bans.meta", "w")
        bans.write(fp)
        fp.close()
        self.runHook("metaSaved")

    def printInfo(self):
        if not len(self.clients) == 0:
            self.logger.info("There are %s users on the server." % len(self.clients))
            for key in self.worlds:
                if len(self.worlds[key].clients) > 0:
                    self.logger.info("%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))
            if len(self.clients) >= self.lowlag_players:
                if self.useLowLag != True:
                    self.useLowLag = True
                    self.logger.warn("Enabling low lag mode.")
            else:
                if self.useLowLag != False:
                    self.useLowLag = False
                    self.logger.warn("Disabling low lag mode.")

    def loadArchive(self, filename):
        "Boots an archive given a filename. Returns the new world ID."
        # Get an unused world name
        i = 1
        while self.world_exists("a-%i" % i):
            i += 1
        world_id = "a-%i" % i
        # Copy and boot
        self.newWorld(world_id, "../arc/archives/%s" % filename)
        self.loadWorld("worlds/%s" % world_id, world_id)
        world = self.worlds[world_id]
        world.status["is_archive"] = True
        self.runHook("archiveLoaded", {"filename": filename, "id": world_id})
        return world_id

    def saveWorlds(self):
        "Saves the worlds, one at a time, with a 1 second delay."
        self._saveWorlds()

    def _saveWorlds(self):
        "Handles actual saving process."
        if not self.saving:
            if not self.world_save_stack:
                self.world_save_stack = list(self.worlds)
            key = self.world_save_stack.pop()
            self.saveWorld(key)
            if not self.world_save_stack:
                self.saveMeta()
            else:
                reactor.callLater(1, self._saveWorlds)

    def saveWorld(self, world_id, shutdown=False):
        value = self.runHook("worldSaving", {"world_id": world_id, "shutdown": shutdown})
        if value is False: return
        try:
            world = self.worlds[world_id]
            world.save_meta()
            world.flush()
            self.logger.info("World '%s' has been saved." % world_id)
            if shutdown: del self.worlds[world_id]
        except Exception as e:
            self.logger.error("Error saving world %s." % world_id)
            self.logger.error("Error: %s" % e)
        self.runHook("worldSaved", {"world_id": world_id, "shutdown": shutdown})

    def claimId(self, client):
        for i in range(1, self.max_clients + 1):
            if i not in self.clients:
                self.clients[i] = client
                self.runHook("idClaimed", {"id": i, "client": client})
                return i
        # Server is full, claim ID only for staff
        if client.isHelper():
            i = len(self.clients.keys()) + 1
            self.clients[i] = client
            self.runHook("idClaimed", {"id": i, "client": client})
            return i
        raise ServerFull

    def releaseId(self, id):
        self.runHook("idReleased", {"id": id, "client": self.clients[id]})
        del self.clients[id]

    def joinWorld(self, worldid, user):
        "Makes the user join the given World."
        value = self.runHook("worldJoining", {"world_id": worldid, "client": user})
        if value is False:
            return self.worlds[user.world.id]
        new_world = self.worlds[worldid]
        try:
            self.logger.info("%s is joining world %s" % (user.username, new_world.basename))
        except:
            self.logger.info("%s is joining world %s" % (user.transport.getPeer().host, new_world.basename))
        if hasattr(user, "world") and user.world:
            self.leaveWorld(user.world, user)
        user.world = new_world
        new_world.clients.add(user)
        self.runHook("worldJoined", {"world_id": worldid, "client": user})
        return new_world

    def leaveWorld(self, world, user):
        world.clients.remove(user)
        self.runHook("worldLeft", {"world_id": world.id, "client": user})
        if world.status["is_archive"] and not world.clients:
            self.unloadWorld(world.id)

    def loadWorld(self, filename, world_id):
        """
        Loads the given world file under the given world ID.
        Returns the ID of the new world.
        """
        # Check if the world actually exists
        if not (os.path.isfile("%s/blocks.gz" % filename) or os.path.isfile("%s/blocks.gz.old" % filename)):
            raise AssertionError # Lazy workaround, need to fix
        world = self.worlds[world_id] = World(filename, factory=self)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        self.logger.info("World '%s' Booted." % world_id)
        self.runHook("worldLoaded", {"world_id": world_id})
        return world_id

    def unloadWorld(self, world_id, skiperror=False):
        """
        Unloads the given world ID.
        """
        # Devs should check this on input level
        if world_id == self.default_name and not skiperror:
            raise ValueError
        for client in list(list(self.worlds[world_id].clients))[:]:
            client.changeToWorld(self.default_name)
            client.sendServerMessage("World '%s' has been shut down." % world_id)
        self.worlds[world_id].stop()
        self.saveWorld(world_id, shutdown=True)
        self.logger.info("World '%s' Shutdown." % world_id)
        self.runHook("worldUnloaded", {"world_id": world_id})

    def rebootWorld(self, world_id):
        """
        Reboots a world in a crash case
        """
        if world_id == self.default_name:
            if self.default_backup not in self.worlds:
                self.loadWorld("worlds/%s" % self.default_backup, self.default_backup)
        for client in list(list(self.worlds[world_id].clients))[:]:
            if world_id == self.default_name:
                client.changeToWorld(self.default_backup)
            else:
                client.changeToWorld(self.default_name)
            client.sendServerMessage("%s has been rebooted." % world_id)
        self.worlds[world_id].stop()
        self.worlds[world_id].flush()
        self.worlds[world_id].save_meta()
        del self.worlds[world_id]
        filename = "worlds/%s" % world_id
        world = self.worlds[world_id] = World(filename, factory=self)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        self.logger.info("Rebooted %s" % world_id)
        self.runHook("worldRebooted", {"world_id": world_id})

    def publicWorlds(self):
        """
        Returns the IDs of all public worlds
        """
        for world_id, world in self.worlds.items():
            if not world.status["private"]:
                yield world_id

    def recordPresence(self, username):
        """
        Records a sighting of 'username' in the lastseen dict.
        """
        self.runHook("lastseenRecorded", {"username": username, "time": time.time()})
        self.lastseen[username.lower()] = time.time()

    def sendMessages(self):
        "Sends all queued messages, and lets worlds recieve theirs."
        try:
            while True: # I don't get this line? -tyteen
                # Get the next task
                source_client, task, data = self.queue.get_nowait()
                if isinstance(source_client, World):
                    world = source_client
                elif isinstance(source_client, Console): # Console
                    world = self.worlds[self.default_name]
                else:
                    try:
                        world = source_client.world
                    except AttributeError:
                        world = self.worlds[self.default_name]
                time = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
                # Someone built/deleted a block
                if task is TASK_BLOCKSET:
                    value = self.runHook("onBlockset", {"client": source_client, "data": data})
                    if value is not False:
                        world.status["modified"] = True
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client is not source_client:
                                client.sendBlock(*data)
                # Someone moved
                elif task is TASK_PLAYERPOS:
                    value = self.runHook("onPlayerPos", {"client": source_client, "data": data})
                    if value is not False:
                    # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerPos(*data)
                # Someone moved only their direction
                elif task is TASK_PLAYERDIR:
                    value = self.runHook("onPlayerDir")
                    if value is not False:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerDir(*data)
                # Someone finished a mass replace that requires respawn for everybody.
                elif task is TASK_INSTANTRESPAWN:
                    value = self.runHook("onInstantRespawn")
                    if value is not False:
                        for client in world.clients:
                            # Save their initial position
                            client.initial_position = client.x >> 5, client.y >> 5, client.z >> 5, client.h
                            client.sendPlayerLeave(data)
                            client.loading_world = True
                            breakable_admins = client.runHook("canbreakadmin")
                            client.sendPacked(TYPE_INITIAL, 7, ("%s: %s" % (self.server_name, world.id)),
                                "Respawning world '%s'..." % world.id, 100 if breakable_admins else 0)
                            client.sendLevel()
                # Someone connected to the server
                elif task is TASK_PLAYERCONNECT:
                    for client in self.usernames:
                        self.usernames[client].sendNewPlayer(*data)
                        if not self.useLowLag:
                            self.usernames[client].sendNormalMessage(
                                "%s%s&e has come online." % (source_client.userColour(), source_client.username))
                    if self.irc_relay and world:
                        if not self.useLowLag:
                            self.irc_relay.sendServerMessage("07%s has come online." % source_client.username)
                # Someone joined a world!
                elif task is TASK_NEWPLAYER:
                    value = self.runHook("onNewPlayer", {"client": source_client})
                    if value is not False:
                        for client in world.clients:
                            if client != source_client:
                                client.sendNewPlayer(*data)
                            sendmessage = self.runHook("worldChanged", {"client": source_client})
                            if sendmessage and not self.useLowLag:
                                client.sendNormalMessage("%s%s&e has joined the world." % (
                                source_client.userColour(), source_client.username))
                # Someone left!
                elif task is TASK_PLAYERLEAVE:
                    self.runHook("onPlayerLeave", {"client": source_client, "skipmsg": data})
                    # Only run it for clients who weren't the source.
                    for client in self.clients.values():
                        client.sendPlayerLeave(data[0])
                        if not source_client.username is None and not self.useLowLag:
                            client.sendNormalMessage(
                                "%s%s&e has gone offline." % (source_client.userColour(), source_client.username))
                    if not source_client.username is None:
                        if self.irc_relay and world and not self.useLowLag:
                            self.irc_relay.sendServerMessage("07%s has gone offline." % source_client.username)
                # Someone changed worlds!
                elif task is TASK_WORLDCHANGE:
                    self.runHook("onWorldChange", {"client": source_client, "world": world})
                    # Only run it for clients who weren't the source.
                    for client in data[1].clients:
                        client.sendPlayerLeave(data[0])
                        if not self.useLowLag:
                            client.sendNormalMessage("%s%s&e joined '%s'" % (
                            source_client.userColour(), source_client.username, world.id))
                    if self.irc_relay and world and not self.useLowLag:
                        self.irc_relay.sendServerMessage("07%s joined '%s'" % (source_client.username, world.id))
                    self.logger.info("%s%s&f has now joined '%s'" % (
                    source_client.userColour(), source_client.username, world.id))
                elif task == TASK_PLAYERRESPAWN:
                    # We need to immediately respawn the user to update their nick.
                    self.runHook("onPlayerRespawn", {"client": source_client})
                    for client in world.clients:
                        if client != source_client:
                            id, username, x, y, z, h, p = data
                            client.sendPlayerLeave(id)
                            client.sendNewPlayer(id, username, x, y, z, h, p)
                # Messages
                elif task is TASK_MESSAGE:
                    # More Word Filter
                    id, colour, username, text, channel, theWorld = data
                    value = self.runHook("onMessage",
                            {"id": id, "colour": colour, "username": username, "text": text, "channel": channel,
                             "world": (world if theWorld == None else theWorld)})
                    if value is not False:
                        # Send the message to everybody
                        if channel == "world":
                            if theWorld != None:
                                for client in self.worlds[theWorld].clients: # World was overriden
                                    client.sendNormalMessage(
                                        "%s!%s%s%s: %s" % (COLOUR_YELLOW, colour, username, COLOUR_WHITE, text))
                            else:
                                for client in world.clients:
                                    client.sendNormalMessage(
                                        "%s!%s%s%s: %s" % (COLOUR_YELLOW, colour, username, COLOUR_WHITE, text))
                        else:
                            for client in self.clients.values():
                                if channel == "staff" and client.isMod():
                                    client.sendMessage(id, COLOUR_YELLOW + "#" + colour, username, text)
                                elif channel == "action":
                                    client.sendAction(id, colour, username, text)
                                elif channel == "server":
                                    client.sendNormalMessage(text)
                                elif channel == "irc":
                                    client.sendMessage(id, ("[IRC] %s" % COLOUR_PURPLE), username, text)
                                else:
                                    client.sendMessage(id, colour, username, text)
                            # Log them
                        log = True
                        if channel == "chat":
                            self.logger.info("%s&f: %s" % (username, text))
                        elif channel == "irc":
                            self.logger.irc("%s %s" % ((("<%s>" % username) if username != "" else ""), text))
                        elif channel == "staff":
                            self.logger.info("#%s: %s" % (username, text))
                        elif channel == "action":
                            self.logger.info("* %s %s" % (username, text))
                        elif channel == "world":
                            w = (str(world.id) if theWorld == None else theWorld)
                            self.logger.info("%s in %s: %s" % (username, w, text))
                            self.chatlogs["world"].write(
                                    {"time": time, "username": username, "world": w, "text": text})
                            self.chatlogs["main"].write(
                                    {"time": time, "username": username, "world": w, "text": text},
                                formatter=MSGLOGFORMAT["world"])
                            log = False
                        elif channel == "server":
                            self.logger.info(text)
                        else: # This message has no channel, just dump everything we see
                            self.logger.warn("Message has no channel. Data: (%s, %s, %s, %s, %s)" % (
                            id, colour, username, text, channel))
                            continue
                        if log:
                            self.chatlogs[channel].write({"time": time, "username": username, "text": text})
                            self.chatlogs["main"].write({"time": time, "username": username, "text": text},
                                formatter=MSGLOGFORMAT[channel])
                            # Relay it to the IRC
                        if self.irc_relay and world and channel not in ["irc", "staff"]:
                            if channel == "action":
                                self.irc_relay.sendAction(username, text)
                            elif channel == "world":
                                self.irc.relay.sendMessage(
                                    "%s!%s in %s" % (COLOUR_YELLOW, colour + username + COLOUR_BLACK, world), text)
                            else:
                                self.irc_relay.sendMessage(username, text)
        except Empty:
            pass
        except Exception as e:
            self.logger.error(traceback.format_exc())
        # OK, now, for every world, let them read their queues
        for world in self.worlds.values():
            world.read_queue()

    def sendMessageToAll(self, message, channel="chat", client=None, id=None, colour=None, user=None, world=None, fromloc="user"):
        """Quick method for sending message to all clients."""
        if client == None or fromloc != "user":
            uid = id if id != None else 127
            c = colour if colour != None else COLOUR_WHITE
            username = user if user != None else "Server"
            w = world
        else:
            uid = id if id != None else client.id
            c = colour if colour != None else client.userColour()
            username = user if user != None else client.username
            w = world if world != None else client.world.id
        self.queue.put((client, TASK_MESSAGE, (uid, c, username, message, channel, w)))

    def newWorld(self, new_name, template="default"):
        "Creates a new world from some template."
        # Make the directory
        try:
            os.mkdir("worlds/%s" % new_name)
        except:
            if not client is None:
                client.sendServerMessage("Sorry, that world already exists!")
            return False
            # Find the template files, copy them to the new location
        for filename in ["blocks.gz", "world.meta"]:
            try:
                shutil.copyfile("arc/templates/%s/%s" % (template, filename), "worlds/%s/%s" % (new_name, filename))
            except IOError:
                return False
            except:
                raise
        self.runHook("worldCreated", {"name": new_name, "template": template})
        return True

    def renameWorld(self, old_worldid, new_worldid):
        "Renames a world."
        assert old_worldid not in self.worlds
        assert self.world_exists(old_worldid)
        assert not self.world_exists(new_worldid)
        os.rename("worlds/%s" % (old_worldid), "worlds/%s" % (new_worldid))
        self.runHook("worldRenamed", {"old_world_id": old_worldid, "new_world_id": new_worldid})

    def numberWithPhysics(self):
        "Returns the number of worlds with physics enabled."
        return len([world for world in self.worlds.values() if world.physics])

    def isSilenced(self, username):
        return username.lower() in self.silenced

    def isOwner(self, username):
        return username.lower() in self.owners

    def isDirector(self, username):
        return username.lower() in self.directors or self.isOwner(username)

    def isAdmin(self, username):
        return username.lower() in self.admins or self.isDirector(username)

    def isMod(self, username):
        return username.lower() in self.mods or self.isAdmin(username)

    def isHelper(self, username):
        return username.lower() in self.helpers or self.isMod(username)

    def isSpectator(self, username):
        return username.lower() in self.spectators

    def isBanned(self, username):
        return username.lower() in self.banned

    def isIpBanned(self, ip):
        return ip in self.ipbanned

    def addBan(self, username, reason, admin="Local"):
        self.banned[username.lower()] = reason
        self.runHook("playerBanned", {"username": username.lower(), "reason": reason, "admin": admin})

    def removeBan(self, username):
        del self.banned[username.lower()]
        self.runHook("playerUnbanned", {"username": username.lower()})

    def banReason(self, username):
        return self.banned[username.lower()]

    def addIpBan(self, ip, reason):
        self.ipbanned[ip] = reason
        self.runHook("playerIpBanned", {"ip": ip, "reason": reason})

    def removeIpBan(self, ip):
        del self.ipbanned[ip]
        self.runHook("playerUnIpBanned", {"ip": ip})

    def ipBanReason(self, ip):
        return self.ipbanned[ip]

    def world_exists(self, world_id):
        "Says if the world exists (even if unbooted)"
        return os.path.isdir("worlds/%s/" % world_id)

    def autoBackup(self):
        for world in self.worlds:
            if world.status["modified"] == True:
                self.doBackup(world, "server", None)
                # Reset modification flag
                world.status["modified"] = False

    def doBackup(self, world_id, fromloc, id=None):
        world_dir = ("worlds/%s/" % world_id)
        if world_id == self.default_name and (not self.backup_default and fromloc == "server"):
            # Server is backing up default
            return (0, 1)
        if not os.path.exists(world_dir):
            # World does not exist
            return (0, 2)
        if not os.path.exists(world_dir + "backup/"):
            os.mkdir(world_dir + "backup/")
        if id != None:
            path = os.path.join(world_dir + "backup/", parts[2])
            if os.path.exists(path):
                return (0, 3) # Named backup exists
        else:
            backups = list([])
            for x in folders:
                if x.isdigit():
                    backups.append(x)
            backups.sort(lambda x, y: int(x) - int(y))
            path = os.path.join(world_dir + "backup/", "0")
            if backups:
                path = os.path.join(world_dir + "backup/", str(int(backups[-1]) + 1))
        os.mkdir(path)
        shutil.copy(world_dir + "blocks.gz", path)
        shutil.copy(world_dir + "world.meta", path)
        if id == None:
            try:
                backupname = str(int(backups[-1]) + 1)
            except:
                backupname = 0
        else: backupname = id
        if len(backups) + 1 > self.backup_max:
            for i in range(0, ((len(backups) + 1) - self.backup_max)):
                shutil.rmtree(os.path.join(world_dir + "backup/", str(int(backups[i]))))
        self.runHook("onBackup", {"world_id": world_id, "backupname": backupname, "fromloc": fromloc})
        return (1, backupname)

    def loadArchives(self):
        self.archives = {}
        for name in os.listdir("arc/archives/"):
            if os.path.isdir(os.path.join("arc/archives", name)):
                for subfilename in os.listdir(os.path.join("arc/archives", name)):
                    match = re.match(r'^(\d\d\d\d\-\d\d\-\d\d_\d?\d\_\d\d)$', subfilename)
                    if match:
                        when = match.groups()[0]
                        try:
                            when = datetime.datetime.strptime(when, "%Y/%m/%d %H:%M:%S")
                        except ValueError as e:
                            self.logger.warning("Bad archive filename %s." % subfilename)
                            continue
                        if name not in self.archives:
                            self.archives[name] = {}
                        self.archives[name][when] = "%s/%s" % (name, subfilename)
        self.logger.info("Loaded %s discrete archives." % len(self.archives))
        self.runHook("archivesLoaded", {"number": len(self.archives)})

    def reloadIrcBot(self):
        if (self.irc_relay):
            try:
                self.irc_relay.quit("Reloading the IRC Bot...")
                global ChatBotFactory
                del ChatBotFactory
                from arc.irc_client import ChatBotFactory

                if self.ircbot and self.use_irc:
                    self.irc_nick = self.irc_config.get("irc", "nick")
                    self.irc_pass = self.irc_config.get("irc", "password")
                    self.irc_channel = self.irc_config.get("irc", "channel")
                    self.irc_cmdlogs = self.irc_config.getboolean("irc", "cmdlogs")
                    self.ircbot = self.irc_config.getboolean("irc", "ircbot")
                    self.staffchat = self.irc_config.getboolean("irc", "staffchat")
                    self.irc_relay = ChatBotFactory(self)
                    if self.ircbot and not self.irc_channel == "#channel" and not self.irc_nick == "botname":
                        reactor.connectTCP(self.irc_config.get("irc", "server"), self.irc_config.getint("irc", "port"),
                            self.irc_relay)
                        self.runHook("IRCBotReloaded")
                    else:
                        self.logger.error("IRC Bot failed to connect, you could modify, rename or remove irc.conf")
                        self.logger.error(
                            "You need to change your 'botname' and 'channel' fields to fix this error or turn the bot off by disabling 'ircbot'")
                    return True
            except:
                return False
        return False

    def applyBlockChanges(self, changeset, world, save=True, secperloop=10):
        """Applies block changes."""
        # Check if world is booted
        if world not in self.worlds:
            raise ValueError, "World not booted"
        else:
            w = self.worlds[world]
        d = defer.Deferred()
        iter = changeset.iteritems()
        def doStep():
            try:
                for x in range(secperloop):
                    key, value = iter.next()
                    x, y, z = key
                    if save: w[x, y, z] = value
                    self.queue.add((w, TASK_BLOCKSET, (x, y, z, value)))
                    reactor.callLater(0.01, doStep)
            except StopIteration:
                d.callback(True)
            except Exception as e:
                d.errback(e)
        doStep()
        return d