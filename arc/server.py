# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, ctypes, datetime, gc, os, random, re, shutil, string, sys, time, traceback
from collections import defaultdict
from ConfigParser import RawConfigParser as ConfigParser
from Queue import Queue, Empty

from twisted.internet.protocol import Factory
from twisted.internet import reactor, task

from arc.console import StdinPlugin
from arc.constants import *
from arc.globals import *
from arc.heartbeat import Heartbeat
from arc.irc_client import ChatBotFactory
from arc.logger import ColouredLogger, ChatLogHandler
from arc.plugins import *
from arc.protocol import ArcServerProtocol
from arc.timer import ResettableTimer
from arc.world import World

class ArcFactory(Factory):
    """
    Factory that deals with the general world actions and cross-user comms.
    """
    protocol = ArcServerProtocol

    def __init__(self, debug=False):
        self.printable = string.printable
        self.logger = ColouredLogger(debug)
        self.chatlogger = ChatLogHandler()
        self.cfginfo = {"version": defaultdict(str)}
        # Load up the server plugins right away
        self.logger.info("Loading server plugins..")
        self.serverPlugins = {} # {"Name": class()}
        self.serverHooks = {}
        self.loadServerPlugins()
        self.logger.info("Loaded server plugins.")
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
        wordfilter = ConfigParser()
        self.default_loaded = False
        self.hooks = {}
        self.saving = False
        self.save_count = 1
        # Read in the greeting
        try:
            r = open('config/greeting.txt', 'r')
        except:
            r = open('config/greeting.example.txt', 'r')
        self.greeting = r.readlines()
        r.close()
        # Read in the titles
        file = open('config/data/titles.dat', 'r')
        self.rank_dic = cPickle.load(file)
        file.close()
        # Read in the messages
        if os.path.exists("config/data/inbox.dat"):
            file = open('config/data/inbox.dat', 'r')
            self.messages = cPickle.load(file)
            file.close()
        self.loadConfig()
        self.use_irc = False
        if (os.path.exists("config/irc.conf")): # IRC bot will be updated soon, no need for cfginfo
            self.use_irc = True
            self.irc_config = ConfigParser()
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
                    reactor.connectTCP(self.irc_config.get("irc", "server"), self.irc_config.getint("irc", "port"), self.irc_relay)
                else:
                    self.logger.error("IRC Bot failed to connect, you could modify, rename or remove irc.conf")
                    self.logger.error("You need to change your 'botname' and 'channel' fields to fix this error or turn the bot off by disabling 'ircbot'")
            except Exception as e:
                self.logger.warn("Error parsing irc.conf (%s)" % e)
                self.logger.warn("IRC bot will not be started.")
                self.irc_relay = None
        else:
            self.irc_relay = None
        # Word Filter
        # Note: worldfilter.conf has no cfgversion at the moment, because we might rewrite this bit - g will know more
        try:
            wordfilter.read("config/wordfilter.conf")
        except Exception as e:
            self.logger.error("Unable to read wordfilter.conf (%s)" % e)
            self.logger.error("Word filtering has been disabled.")
            self.has_wordfilter = False
        else:
            self.has_wordfilter = True
        self.filter = []
        if self.has_wordfilter:
            try:
                number = int(wordfilter.get("filter", "count"))
            except Exception as e:
                self.logger.error("Error parsing wordfilter.conf (%s)" % e)
                sys.exit(1)
            for x in range(number):
                self.filter = self.filter + [[wordfilter.get("filter", "s"+str(x)), wordfilter.get("filter","r"+str(x))]]
        # Load up the plugins specified
        self.plugins_config = ConfigParser()
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
        self.runServerHook("configLoaded")
        self.logger.info("Loading plugins...")
        load_plugins(plugins)
        self.runServerHook("pluginsLoaded")
        self.logger.info("Loaded plugins.")
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
                sx//2,grass_to+2, sz//2, 0, # Spawn
                ([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
            )
            self.logger.info("Generated.")
        # Load up the contents of data.
        self.loadMeta()
        # Set up a few more things.
        self.queue = Queue()
        self.clients = {}
        self.usernames = {}
        # Open the adminchat log.
        self.adlog = open("logs/server.log", "a")

    def loadConfig(self, reload=False):
        configParsers = dict()
        for config in CONFIG:
            if reload and config[3] == False:
                # Non-dynamic
                continue
            if not config[1][0] in configParsers.keys():
                # Create an instance of ConfigParser if we don't already have one
                configParsers[config[1][0]] = ConfigParser()
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
                        self.logger.error("You have an outdated %s, please redownload the Arc package and fill in the configuration again." % config[1][0])
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
            try:
                valueFunc = getattr(configParsers[config[1][0]], config[4])
                if config[4] == "options":
                    value = valueFunc(config[1][1])
                else:
                    value = valueFunc(config[1][1], config[1][2])
            except Exception as e:
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
                            self.logger.error(str(e))
                    self.logger.debug("Loaded config %s." % config[0])

    # Dummy callback functions until I figure out a better way to do all of these

    def checkSalt(self, reload):
        if self.salt in ["", "Select this text and mash your keyboard."]:
            self.logger.critical("Salt is required.")
            sys.exit(1)

    def buildSpoofHeartbeat(self, reload):
        heartbeats = self.hbs
        config = ConfigParser()
        config.read("config/main.conf") # This can't fail because it has been checked before
        self.heartbeats = dict()
        for element in heartbeats:
            name = config.get("heartbeatnames", element)
            port = config.getint("heartbeatports", element)
            self.heartbeats[element] = (name, port)
            reactor.listenTCP(port, self)
            self.logger.info("Starting spoofed heartbeat %s on port %s..." % (name, port))

    def modifyHeartbeatURL(self, reload):
        "Called to recheck URL."
        if reload:
            self.heartbeat.hburl = "http://www.minecraft.net/heartbeat.jsp" if not self.factory.wom_heartbeat else "http://direct.worldofminecraft.com/hb.php"

    def startASDLoop(self, reload):
        "Called to start the ASD loop."
        pass

    def initBackupLoop(self, reload):
        "Called to initialize the backup loop."
        if reload:
            self.loops["autobackup"].stop()
        elif self.backup_auto != False:
            self.loops["autobackup"] = task.LoopingCall(self.AutoBackup)

    def modifyBackupFrequency(self, reload):
        "Called to start the backup loop."
        if reload:
            self.loops["autobackup"].stop()
        elif self.backup_auto != False:
            self.loops["autobackup"].run(self.config["backup_freq"], now=False)

    def enableArchiver(self, reload):
        if reload:
            self.loops["loadarchives"].stop()
        elif self.enable_archives != False:
            self.loops["loadarcives"] = task.LoopingCall("loadarchives")
            self.loops["loadarcives"].start(300)

    def initBLBLimiter(self, reload):
        if not self.useblblimiter:
            if reload:
                del self.blblimit
            return
        self.blblimit = {}
        config = ConfigParser()
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
    def loadServerPlugins(self, something=None):
        "Used to load up all the server plugins."
        files = []
        self.serverHooks = {} # Clear the list of hooks
        self.logger.debug("Listing server plugins..")
        for element in os.listdir("arc/serverplugins"): # List the plugins
            ext = element.split(".")[-1]
            file = element.split(".")[0]
            if element == "__init__.py": # Skip the initialiser
                continue
            elif ext == "py": # Check if it ends in .py
                files.append(file)
        self.logger.debug("Possible server plugins (%s): %s" % (len(files) ,".py, ".join(files)+".py"))
        self.logger.info("Loading server plugins..")
        i = 0
        while i < len(files):
            element = files[i]
            reloaded = False
            if not "arc.serverplugins.%s" % element in sys.modules.keys(): # Check if we already imported it
                try:
                    __import__("arc.serverplugins.%s" % element) # If not, import it
                except Exception as a: # Got an error!
                    self.logger.error("Unable to load server plugin from %s.py!" % element)
                    self.logger.error("Error: %s" % a)
                    i = i + 1
                    continue
                else:
                    try:
                        mod = sys.modules["arc.serverplugins.%s" % element].serverPlugin() # Grab the actual plugin class
                        name = mod.name # What's the name?
                        mod.factory = self
                        mod.logger = self.logger
                        if hasattr(mod, "gotServer"):
                            mod.gotServer()
                    except Exception as a:
                        self.logger.error("Unable to load server plugin from %s" % (element+".py"))
                        self.logger.error("Error: %s" % a)
                        i = i + 1
                        continue
            else: # We already imported it
                mod = self.serverPlugins[element][0] #
                del mod #
                del self.serverPlugins[element] #
                del sys.modules["arc.serverplugins.%s" % element] # Unimport it by deleting it
                try:
                    __import__("arc.serverplugins.%s" % element) # import it again
                except Exception as a: # Got an error!
                    self.logger.error("Unable to load server plugin from %s.py!" % element)
                    self.logger.error("Error: %s" % a)
                    i = i + 1
                    continue
                else:
                    try:
                        mod = sys.modules["arc.serverplugins.%s" % element].serverPlugin(self)
                        name = mod.name # get the name
                    except Exception as a:
                        self.logger.error("Unable to load server plugin from %s" % (element+".py"))
                        self.logger.error("Error: %s" % a)
                        i = i + 1
                        continue
                reloaded = True # Remember that we reloaded it
            mod.filename = element
            self.serverPlugins[name] = mod # Put it in the plugins list
            if not reloaded:
                self.logger.debug("Loaded server plugin: %s" % name)
            else:
                self.logger.debug("Reloaded server plugin: %s" % name)
            i = i + 1
        self.logger.debug("self.serverPlugins: %s" % self.serverPlugins)
        #The following code should be handled by the ServerPlugins class and registerHook
        self.logger.debug("Getting hooks..")
        for plugin in self.serverPlugins.values(): # For every plugin,
            try:
                for element in plugin.hooks.keys(): # For every hook in the plugin,
                    if element not in self.serverHooks.keys():
                        self.serverHooks[element] = [] # Make a note of the hook in the hooks dict
                    self.serverHooks[element].append([plugin, plugin.hooks[element]]) # Make a note of the hook in the hooks dict
                    self.logger.debug("Loaded hook '%s' for server plugin '%s'." % (element, plugin.name))
            except Exception as a:
                self.logger.error("Unable to get hooks from server plugin %s" % plugin.name)
                self.logger.error("Error: %s" % a)
                continue
        self.logger.debug("self.serverHooks: %s" % self.serverHooks)
        self.runServerHook("serverPluginsLoaded")

    def serverPluginExists(self, plugin):
        return plugin in self.serverPlugins.keys()

    def runServerHook(self, hook, data = None):
        "Used to run hooks for ServerPlugins"
        finalvalue = True
        if hook in self.serverHooks.keys():
            for element in self.serverHooks[hook]:
                try:
                    if data is not None:
                        value = element[1](element[0], data)
                    else:
                        value = element[1](element[0])
                    if value == False:
                        finalvalue = False
                except Exception as a:
                    try:
                        self.logger.error("Unable to run %s in server plugin %s!" % (element[1].__name__, element[0].name))
                        self.logger.error("Error: %s" % a)
                    except Exception as b:
                        self.logger.error("Some plugin hook failed!")
                        self.logger.error("Error when getting details: %s" % b)
                        self.logger.error("Error when running hook: %s" % a)
                    self.logger.error("Objects: %s" % element)
        return finalvalue

    def buildProtocol(self, addr):
        "Builds the protocol. Used to switch between Manic Digger and Minecraft."
        # Some male/female/alien idenfication code here
        p = self.protocol()
        p.factory = self
        self.runServerHook("protocolBuilt")
        return p

    def startFactory(self):
        self.console = StdinPlugin(self)
        self.console.start()
        self.heartbeat = Heartbeat(self)
        self.runServerHook("heartbeatStarted")
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
        self.loops["cleangarbage"].start(60*15)
        self.runServerHook("factoryStarted")

    def cleanGarbage(self):
        count = gc.collect()
        self.logger.info("%i garbage objects collected, %i were uncollected." % (count, len(gc.garbage)))
        self.runServerHook("garbageCollected", {"collected": count, "uncollected": len(gc.garbage)})

    def loadMeta(self):
        "Loads the 'meta' - variables that change with the server (worlds, admins, etc.)"
        config = ConfigParser()
        config.read("config/data/ranks.meta")
        specs = ConfigParser()
        specs.read("config/data/spectators.meta")
        lastseen = ConfigParser()
        lastseen.read("config/data/lastseen.meta")
        bans = ConfigParser()
        bans.read("config/data/bans.meta")
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
            print self.cfginfo["version"]["ranks.meta"]
            self.logger.error("You have an outdated ranks.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["spectators.meta"], CFGVERSION["spectators.meta"]):
            self.logger.error("You have an outdated spectators.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["lastseen.meta"], CFGVERSION["lastseen.meta"]):
            self.logger.error("You have an outdated lastseen.meta, please redownload the Arc package and fill in the configuration again.")
            sys.exit(1)
        if not checkConfigVersion(self.cfginfo["version"]["bans.meta"], CFGVERSION["bans.meta"]):
            self.logger.error("You have an outdated bans.meta, please redownload the Arc package and fill in the configuration again.")
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
        self.runServerHook("metaLoaded")

    def saveMeta(self):
        "Saves the server's meta back to a file."
        config = ConfigParser()
        specs = ConfigParser()
        lastseen = ConfigParser()
        bans = ConfigParser()
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
        self.runServerHook("metaSaved")

    def printInfo(self):
        if not len(self.clients) == 0:
            self.logger.info("There are %s users on the server." % len(self.clients))
            for key in self.worlds:
                if len(self.worlds[key].clients) > 0:
                    self.logger.info("%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))

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
        world.is_archive = True
        self.runServerHook("archiveLoaded", {"filename": filename, "id": world_id})
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
        value = self.runServerHook("worldSaving", {"world_id": world_id, "shutdown": shutdown})
        if not value:
            return
        try:
            world = self.worlds[world_id]
            world.save_meta()
            world.flush()
            self.logger.info("World '%s' has been saved." % world_id)
            if self.save_count == 5:
                for client in list(list(world.clients))[:]:
                    client.sendServerMessage("[%s] World '%s' has been saved." % (datetime.datetime.utcnow().strftime("%H:%M"), world_id))
                self.save_count = 1
            else:
                self.save_count += 1
            if shutdown: del self.worlds[world_id]
        except Exception as e:
            self.logger.error("Error saving world %s." % world_id)
            self.logger.error("Error: %s" % e)
        self.runServerHook("worldSaved", {"world_id": world_id, "shutdown": shutdown})

    def claimId(self, client):
        for i in range(1, self.max_clients+1):
            if i not in self.clients:
                self.clients[i] = client
                self.runServerHook("idClaimed", {"id": i, "client": client})
                return i
        raise ServerFull

    def releaseId(self, id):
        self.runServerHook("idReleased", {"id": id, "client": self.clients[id]})
        del self.clients[id]

    def joinWorld(self, worldid, user):
        "Makes the user join the given World."
        value = self.runServerHook("worldJoining", {"world_id": worldid, "client": user})
        if not value:
            return self.worlds(user.world.id)
        new_world = self.worlds[worldid]
        try:
            self.logger.info("%s is joining world %s" % (user.username, new_world.basename))
        except:
            self.logger.info("%s is joining world %s" % (user.transport.getPeer().host, new_world.basename))
        if hasattr(user, "world") and user.world:
            self.leaveWorld(user.world, user)
        user.world = new_world
        new_world.clients.add(user)
        self.runServerHook("worldJoined", {"world_id": worldid, "client": user})
        return new_world

    def leaveWorld(self, world, user):
        world.clients.remove(user)
        self.runServerHook("worldLeft", {"world_id": world.id, "client": user})
        if world.is_archive and not world.clients:
            self.unloadWorld(world.id)

    def loadWorld(self, filename, world_id):
        """
        Loads the given world file under the given world ID, or a random one.
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
        self.runServerHook("worldLoaded", {"world_id": world_id})
        return world_id

    def unloadWorld(self, world_id):
        """
        Unloads the given world ID.
        """
        # Devs should check this on input level
        if world_id == self.default_name:
            raise ValueError
        for client in list(list(self.worlds[world_id].clients))[:]:
            client.changeToWorld(self.default_name)
            client.sendServerMessage("World '%s' has been shut down." % world_id)
        self.worlds[world_id].stop()
        self.saveWorld(world_id, True)
        self.logger.info("World '%s' Shutdown." % world_id)
        self.runServerHook("worldUnloaded", {"world_id": world_id})

    def rebootWorld(self, world_id):
        """
        Reboots a world in a crash case
        """
        for client in list(list(self.worlds[world_id].clients))[:]:
            if world_id == self.default_name:
                client.loadWorld("worlds/%s" % world_id, world_id)
                client.changeToWorld(self.default_backup)
            else:
                client.changeToWorld(self.default_name)
            client.sendServerMessage("%s has been Rebooted." % world_id)
        self.worlds[world_id].stop()
        self.worlds[world_id].flush()
        self.worlds[world_id].save_meta()
        del self.worlds[world_id]
        world = self.worlds[world_id] = World(filename, factory=self)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        self.logger.info("Rebooted %s" % world_id)
        self.runServerHook("worldRebooted", {"world_id": world_id})

    def publicWorlds(self):
        """
        Returns the IDs of all public worlds
        """
        for world_id, world in self.worlds.items():
            if not world.private:
                yield world_id

    def recordPresence(self, username):
        """
        Records a sighting of 'username' in the lastseen dict.
        """
        self.runServerHook("lastseenRecorded", {"username": username, "time": time.time()})
        try:
            self.lastseen[username.lower()] = time.time()
        except Exception as a:
            self.logger.error("Unable to set lastseen for %s" % username)
            self.logger.error("%s" % a)

    def unloadPlugin(self, plugin_name):
        "Unloads the plugin with the given module name."
        # Unload the plugin from everywhere
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.unloadPlugin(plugin)
            elif issubclass(plugin, ServerPlugin):
                self.plugins.remove(plugin)
                plugin.unregister()
        # Unload it
        unload_plugin(plugin_name)
        self.runServerHook("pluginUnloaded", {"plugin_name": plugin_name})

    def loadPlugin(self, plugin_name):
        # Load it
        load_plugin(plugin_name)
        # Load it back into clients etc.
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.loadPlugin(plugin)
            elif issubclass(plugin, ServerPlugin):
                plugins.append(plugins_by_module_name(plugin_name))
        self.runServerHook("pluginLoaded", {"plugin_name": plugin_name})

    def sendMessages(self):
        "Sends all queued messages, and lets worlds recieve theirs."
        try:
            while True: # I don't get this line? -tyteen
                # Get the next task
                source_client, task, data = self.queue.get_nowait()
                try:
                    if isinstance(source_client, World):
                        world = source_client
                    elif str(source_client).startswith("<StdinPlugin"):
                        world = self.worlds[self.default_name]
                    else:
                        try:
                            world = source_client.world
                        except AttributeError:
                            self.logger.warn("Source client for message has no world. Ignoring.")
                            continue
                    # Someone built/deleted a block
                    if task is TASK_BLOCKSET:
                        value = self.runServerHook("onBlockset", {"client": source_client, "data": data})
                        if value:
                            # Only run it for clients who weren't the source.
                            for client in world.clients:
                                if client is not source_client:
                                    client.sendBlock(*data)
                    # Someone moved
                    elif task is TASK_PLAYERPOS:
                        value = self.runServerHook("onPlayerPos", {"client": source_client, "data": data})
                        if value:
                        # Only run it for clients who weren't the source.
                            for client in world.clients:
                                if client != source_client:
                                    client.sendPlayerPos(*data)
                    # Someone moved only their direction
                    elif task is TASK_PLAYERDIR:
                        value = self.runServerHook("onPlayerDir")
                        if value:
                            # Only run it for clients who weren't the source.
                            for client in world.clients:
                                if client != source_client:
                                    client.sendPlayerDir(*data)
                    # Someone finished a mass replace that requires respawn for everybody.
                    elif task is TASK_INSTANTRESPAWN:
                        value = self.runServerHook("onInstantRespawn")
                        if value:
                            for client in world.clients:
                                # Save their initial position
                                client.initial_position = client.x>>5, client.y>>5, client.z>>5, client.h
                                client.sendPlayerLeave(data)
                                client.loading_world = True
                                breakable_admins = client.runHook("canbreakadmin")
                                client.sendPacked(TYPE_INITIAL, 7, ("%s: %s" % (self.server_name, world.id)), "Respawning world '%s'..." % world.id, 100 if breakable_admins else 0)
                                client.sendLevel()
                    # Someone spoke!
                    elif task is TASK_MESSAGE:
                        # More Word Filter
                        id, colour, username, text = data
                        value = self.runServerHook("onMessage", {"id": id, "colour": colour, "username": username, "text": text})
                        if value:
                            text = self.messagestrip(text)
                            data = (id, colour, username, text)
                            for client in self.clients.values():
                                client.sendMessage(*data)
                            id, colour, username, text = data
                            self.logger.info("%s%s&f: %s" % (colour, username, text))
                            self.chatlog.write("[%s] %s: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), colour+username, text))
                            self.chatlog.flush()
                            if self.irc_relay and world:
                                self.irc_relay.sendMessage(username, text)
                    # Someone spoke!
                    elif task is TASK_IRCMESSAGE:
                        id, colour, username, text = data
                        value = self.runServerHook("onIRCMessage", {"id": id, "colour": colour, "username": username, "text": text})
                        if value:
                            for client in self.clients.values():
                                client.sendMessage(*data)
                            self.logger.info("<%s> %s" % (username, text))
                            self.chatlog.write("[%s] <%s> %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), username, text))
                            self.chatlog.flush()
                            if self.irc_relay and world:
                                self.irc_relay.sendMessage(username, text)
                    # Someone actioned!
                    elif task is TASK_ACTION:
                        # More Word Filter
                        id, colour, username, text = data
                        value = self.runServerHook("onAction", {"id": id, "colour": colour, "username": username, "text": text})
                        if value:
                            text = self.messagestrip(text)
                            data = (id, colour, username, text)
                            for client in self.clients.values():
                                client.sendAction(*data)
                            id, colour, username, text = data
                            self.logger.info("&d* %s %s" % (username, text))
                            self.chatlog.write("[%s] * %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), colour+username, text))
                            self.chatlog.flush()
                            if self.irc_relay and world:
                                self.irc_relay.sendAction(username, text)
                    # Someone connected to the server
                    elif task is TASK_PLAYERCONNECT:
                        for client in self.usernames:
                            self.usernames[client].sendNewPlayer(*data)
                            self.usernames[client].sendNormalMessage("%s%s&e has come online." % (source_client.userColour(), source_client.username))
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("07%s has come online." % source_client.username)
                    # Someone joined a world!
                    elif task is TASK_NEWPLAYER:
                        value = self.runServerHook("onNewPlayer", {"client": source_client})
                        if value:
                            for client in world.clients:
                                if client != source_client:
                                    client.sendNewPlayer(*data)
                                sendmessage = self.runServerHook("worldChanged", {"client": source_client})
                                if sendmessage:
                                    client.sendNormalMessage("%s%s&e has joined the world." % (source_client.userColour(), source_client.username))
                    # Someone left!
                    elif task is TASK_PLAYERLEAVE:
                        self.runServerHook("onPlayerLeave", {"client": source_client, "skipmsg": data})
                        # Only run it for clients who weren't the source.
                        for client in self.clients.values():
                            client.sendPlayerLeave(data[0])
                            if not source_client.username is None:
                                client.sendNormalMessage("%s%s&e has gone offline." % (source_client.userColour(), source_client.username))
                            else:
                                try:
                                    del self.usernames[source_client]
                                except Exception as e:
                                    self.logger.warn(str(e))
                        if not source_client.username is None:
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage("07%s has gone offline." % source_client.username)
                    # Someone changed worlds!
                    elif task is TASK_WORLDCHANGE:
                        self.runServerHook("onWorldChange", {"client": source_client, "world": world})
                        # Only run it for clients who weren't the source.
                        for client in data[1].clients:
                            client.sendPlayerLeave(data[0])
                            client.sendNormalMessage("%s%s&e joined '%s'" % (source_client.userColour(), source_client.username, world.id))
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("07%s joined '%s'" % (source_client.username, world.id))
                        self.logger.info("%s%s&f has now joined '%s'" % (source_client.userColour(), source_client.username, world.id))
                    elif task == TASK_STAFFMESSAGE:
                        # Give all staff the message
                        id, colour, username, text, IRC = data
                        value = self.runServerHook("onStaffMessage", {"id": id, "colour": colour, "username": username, "text": text, "IRC": IRC})
                        if value:
                            message = self.messagestrip(text);
                            for user, client in self.usernames.items():
                                if self.isMod(user):
                                    client.sendMessage(100, COLOUR_YELLOW+"#"+colour, username, message, False, False)
                            if self.staffchat and self.irc_relay and len(data)>3:
                                self.irc_relay.sendServerMessage("#"+username+": "+text,True,username,IRC)
                            self.logger.info("#"+colour+username+"&f: "+text)
                            self.adlog.write("["+datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")+"] #"+username+": "+text+"\n")
                            self.adlog.flush()
                    elif task == TASK_GLOBALMESSAGE:
                        # Give all world people the message
                        id, world, message = data
                        value = self.runServerHook("onGlobalMessage", {"id": id, "world": world, "message": message})
                        if value:
                            message = self.messagestrip(message);
                            for client in world.clients:
                                client.sendNormalMessage(message)
                    elif task == TASK_WORLDMESSAGE:
                        # Give all world people the message
                        id, world, message = data
                        value = self.runServerHook("onWorldMessage", {"id": id, "world": world, "message": message})
                        if value:
                            for client in world.clients:
                                client.sendNormalMessage(message)
                    elif task == TASK_SERVERMESSAGE:
                        # Give all people the message
                        message = data
                        value = self.runServerHook("onServerMessage", {"message": message})
                        if value:
                            message = self.messagestrip(message);
                            for client in self.clients.values():
                                client.sendNormalMessage(COLOUR_DARKBLUE + message)
                            self.logger.info(message)
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage(message)
                    elif task == TASK_ONMESSAGE:
                        # Give all people the message
                        id, world, text = data
                        value = self.runServerHook("onOnMessage", {"id": id, "world": world, "text": text})
                        if value:
                            message = self.messagestrip(text)
                            for client in self.clients.values():
                                client.sendNormalMessage(COLOUR_YELLOW + message)
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage(message)
                    elif task == TASK_ADMINMESSAGE:
                        # Give all people the message
                        message = self.messagestrip(data)
                        value = self.runServerHook("onAdminMessage", {"client": source_client, "message": data})
                        if value:
                            for client in self.clients.values():
                                client.sendNormalMessage(COLOUR_YELLOW + message)
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage(message)
                    elif task == TASK_PLAYERRESPAWN:
                        # We need to immediately respawn the user to update their nick.
                        self.runServerHook("onPlayerRespawn", {"client": source_client})
                        for client in world.clients:
                            if client != source_client:
                                id, username, x, y, z, h, p = data
                                client.sendPlayerLeave(id)
                                client.sendNewPlayer(id, username, x, y, z, h, p)
                    elif task == TASK_SERVERURGENTMESSAGE:
                        # Give all people the message
                        message = data
                        value = self.runServerHook("onServerUrgentMessage", {"message": message})
                        if value:
                            for client in self.clients.values():
                                client.sendNormalMessage(COLOUR_DARKRED + message)
                            self.logger.info(message)
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage(message)
                    elif task == TASK_AWAYMESSAGE:
                        # Give all world people the message
                        message = data
                        value = self.runServerHook("onAwayMessage", {"client": source_client, "message": message})
                        if value:
                            for client in self.clients.values():
                                client.sendNormalMessage(COLOUR_DARKPURPLE + message)
                            self.logger.info("AWAY - %s" %message)
                            self.chatlog.write("[%s] %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), "", message))
                            self.chatlog.flush()
                            if self.irc_relay and world:
                                self.irc_relay.sendAction("", message)
                except Exception as e:
                    self.logger.error(traceback.format_exc())
        except Empty:
            pass
        # OK, now, for every world, let them read their queues
        for world in self.worlds.values():
            world.read_queue()

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
        self.runServerHook("worldCreated", {"name": new_name, "template": template})
        return True

    def renameWorld(self, old_worldid, new_worldid):
        "Renames a world."
        assert old_worldid not in self.worlds
        assert self.world_exists(old_worldid)
        assert not self.world_exists(new_worldid)
        os.rename("worlds/%s" % (old_worldid), "worlds/%s" % (new_worldid))
        self.runServerHook("worldRenamed", {"old_world_id": old_worldid, "new_world_id": new_worldid})

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
        self.runServerHook("playerBanned", {"username": username.lower(), "reason": reason, "admin": admin})

    def removeBan(self, username):
        del self.banned[username.lower()]
        self.runServerHook("playerUnbanned", {"username": username.lower()})

    def banReason(self, username):
        return self.banned[username.lower()]

    def addIpBan(self, ip, reason):
        self.ipbanned[ip] = reason
        self.runServerHook("playerIpBanned", {"ip": ip, "reason": reason})

    def removeIpBan(self, ip):
        del self.ipbanned[ip]
        self.runServerHook("playerUnIpBanned", {"ip": ip})

    def ipBanReason(self, ip):
        return self.ipbanned[ip]

    def world_exists(self, world_id):
        "Says if the world exists (even if unbooted)"
        return os.path.isdir("worlds/%s/" % world_id)

    # The following code needs to be rewritten
    def AutoBackup(self):
        for world in self.worlds:
            self.Backup(world)

    def Backup(self, world_id):
        world_dir = ("worlds/%s/" % world_id)
        if world_id == self.default_name and not self.backup_default:
            return
        if not os.path.exists(world_dir):
            self.logger.info("World %s does not exist." % (world.id))
        else:
            if not os.path.exists(world_dir+"backup/"):
                os.mkdir(world_dir+"backup/")
            folders = os.listdir(world_dir+"backup/")
            backups = list([])
            for x in folders:
                if x.isdigit():
                    backups.append(x)
            backups.sort(lambda x, y: int(x) - int(y))
            path = os.path.join(world_dir+"backup/", "0")
            if backups:
                path = os.path.join(world_dir+"backup/", str(int(backups[-1])+1))
            os.mkdir(path)
            shutil.copy(world_dir + "blocks.gz", path)
            shutil.copy(world_dir + "world.meta", path)
            try:
                self.logger.info("%s's backup %s is saved." % (world_id, str(int(backups[-1])+1)))
            except:
                self.logger.info("%s's backup 0 is saved." % (world_id))
            if len(backups)+1 > self.backup_max:
                for i in range(0,((len(backups)+1)-self.backup_max)):
                    shutil.rmtree(os.path.join(world_dir+"backup/", str(int(backups[i]))))
            self.runServerHook("onBackup", {"world_id": world_id})
    # The above code needs to be rewritten

    def messagestrip(self, message):
        if self.has_wordfilter:
            strippedmessage = ""
            for x in message:
                if isinstance(x, list):
                    strippedmessage = strippedmessage + self.messagestrip(x)
                elif isinstance(x, str):
                    if str(x) in self.printable:
                        strippedmessage = strippedmessage + str(x)
                else:
                    self.logger.error("Unknown message type passed to the message stripper.")
                    self.logger.error("Data: %s" % x)
                    return "Error!"
            message = strippedmessage
            for x in self.filter:
                rep = re.compile(x[0], re.IGNORECASE)
                message = rep.sub(x[1], message)
            return message
        else: # No word filter, just return the message
            return message

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
        self.runServerHook("archivesLoaded", {"number": len(self.archives)})

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
                        reactor.connectTCP(self.irc_config.get("irc", "server"), self.irc_config.getint("irc", "port"), self.irc_relay)
                        self.runServerHook("IRCBotReloaded")
                    else:
                        self.logger.error("IRC Bot failed to connect, you could modify, rename or remove irc.conf")
                        self.logger.error("You need to change your 'botname' and 'channel' fields to fix this error or turn the bot off by disabling 'ircbot'")
                    return True
            except:
                return False
        return False