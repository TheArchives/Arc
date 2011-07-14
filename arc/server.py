# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import ctypes, datetime, gc, os, platform, random, re, shutil, subprocess, sys, time, traceback, cPickle
from ConfigParser import RawConfigParser as ConfigParser
from Queue import Queue, Empty

from twisted.internet.protocol import Factory
from twisted.internet import reactor

from arc.console import StdinPlugin
from arc.constants import *
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
        self.logger = ColouredLogger(debug)
        self.chatlogger = ChatLogHandler()

        # Load up the server plugins right away
        self.logger.info("Loading server plugins..")
        self.serverPlugins = {} # {"Name": class()}
        self.serverHooks = {}
        self.loadServerPlugins()
        self.logger.info("Loaded server plugins.")

        # Initialise internal datastructures
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
        self.specs = ConfigParser()
        self.last_heartbeat = time.time()
        self.config = ConfigParser()
        self.options_config = ConfigParser()
        self.ploptions_config = ConfigParser()
        self.wordfilter = ConfigParser()
        # self.plugins = [plugin(self) for plugin in server_plugins] <- useful code?
        # Maybe, but I'm initialising them already in the loader
        self.hooks = {}
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
        try:
            self.config.read("config/main.conf")
        except Exception as a:
            self.logger.error("Unable to read main.conf (%s)" % a)
            sys.exit(1)
        try:
            self.options_config.read("config/options.conf")
        except Exception as a:
            self.logger.error("Unable to read options.conf (%s)" % a)
            sys.exit(1)
        try:
            self.ploptions_config.read("config/ploptions.conf")
        except Exception as a:
            self.logger.error("Unable to read ploptions.conf (%s)" % a)
            sys.exit(1)
        self.use_irc = False
        if (os.path.exists("config/irc.conf")):
            self.use_irc = True
            self.irc_config = ConfigParser()
            try:
                self.irc_config.read("config/irc.conf")
            except Exception as a:
                self.logger.error("Unable to read irc.conf (%s)" % a)
                sys.exit(1)
        self.saving = False
        try:
            self.max_clients = self.config.getint("main", "max_clients")
            self.server_message = self.config.get("main", "description")
            self.public = self.config.getboolean("main", "public")
            self.controller_port = self.config.get("network", "controller_port")
            self.controller_password = self.config.get("network", "controller_password")
            self.server_name = self.config.get("main", "name")
            # Salt, for the heartbeat server/verify-names
            self.salt = self.config.get("main", "salt") # Now reads config to cope with WoM's direct connect
            if self.server_name == "iCraft Server":
                self.logger.error("You forgot to give your server a name.")
        except Exception as e:
            self.logger.error("Error parsing main.conf (%s)" % e)
            sys.exit(1)
        if self.salt == "":
            self.logger.error("Salt is required.")
            sys.exit(1)
        try:
            self.duplicate_logins = self.options_config.getboolean("options", "duplicate_logins")
            self.info_url = self.options_config.get("options", "info_url")
            self.away_kick = self.options_config.getboolean("options", "away_kick")
            self.away_time = self.options_config.getint("options", "away_time")
            self.colors = self.options_config.getboolean("options", "colors")
            self.physics_limit = self.options_config.getint("worlds", "physics_limit")
            self.default_name = self.options_config.get("worlds", "default_name")
            self.default_backup = self.options_config.get("worlds", "default_backup")
            self.asd_delay = self.options_config.getint("worlds", "asd_delay")
            self.gchat = self.options_config.getboolean("worlds", "gchat")
        except Exception as e:
            self.logger.error("Error parsing options.conf (%s)" % e)
            sys.exit(1)
        try:
            self.grief_blocks = self.ploptions_config.getint("antigrief", "blocks")
            self.grief_time = self.ploptions_config.getint("antigrief", "time")
            self.backup_freq = self.ploptions_config.getint("backups", "backup_freq")
            self.backup_default = self.ploptions_config.getboolean("backups", "backup_default")
            self.backup_max = self.ploptions_config.getint("backups", "backup_max")
            self.backup_auto = self.ploptions_config.getboolean("backups", "backup_auto")
            self.enable_archives = self.ploptions_config.getboolean("archiver", "enable_archiver")
            self.currency = self.ploptions_config.get("bank", "currency")
            self.useblblimit = self.ploptions_config.getboolean("blb", "use_blb_limiter")
            if self.useblblimit:
                self.blblimit = {}
                self.blblimit["player"] = self.ploptions_config.getint("blb", "player")
                self.blblimit["builder"] = self.ploptions_config.getint("blb", "builder")
                self.blblimit["op"] = self.ploptions_config.getint("blb", "op")
                self.blblimit["worldowner"] = self.ploptions_config.getint("blb", "worldowner")
                self.blblimit["helper"] = self.ploptions_config.getint("blb", "helper")
                self.blblimit["mod"] = self.ploptions_config.getint("blb", "mod")
                self.blblimit["admin"] = self.ploptions_config.getint("blb", "admin")
                self.blblimit["director"] = self.ploptions_config.getint("blb", "director")
                self.blblimit["owner"] = self.ploptions_config.getint("blb", "owner")
            self.usebitly = self.ploptions_config.getboolean("internet", "use_bitly")
            if self.usebitly:
                self.bitly_username = self.ploptions_config.getboolean("internet", "bitly_username")
                self.bitly_apikey = self.ploptions_config.getboolean("internet", "bitly_password")
        except Exception as e:
            self.logger.error("Error parsing ploptions.conf (%s)" % e)
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
                if self.ircbot and not (self.irc_channel == "#icraft" or self.irc_channel == "#channel") and not self.irc_nick == "botname":
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
        self.default_loaded = False
        # Word Filter
        try:
            self.wordfilter.read("config/wordfilter.conf")
        except Exception as e:
            self.logger.error("Unable to read wordfilter.conf (%s)" % e)
            sys.exit(1)
        self.filter = []
        try:
            number = int(self.wordfilter.get("filter", "count"))
        except Exception as e:
            self.logger.error("Error parsing wordfilter.comf (%s)" % e)
            sys.exit(1)
        for x in range(number):
            self.filter = self.filter + [[self.wordfilter.get("filter", "s"+str(x)), self.wordfilter.get("filter","r"+str(x))]]
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
        self.runServerHook("dataLoaded")
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

    def loadServerPlugins(self, something=None):
        "Used to load up all the server plugins. Might get a bit complicated though."
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
        self.logger.debug("Loading server plugins..")
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
                        mod = sys.modules["arc.serverplugins.%s" % element].serverPlugin(self) # Grab the actual plugin class
                        name = mod.name # What's the name?
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
        # Boot worlds that got loaded
        for world in self.worlds:
            self.loadWorld("worlds/%s" % world, world)
        if self.backup_auto:
            reactor.callLater(float(self.backup_freq * 60), self.AutoBackup)
        # Set up tasks to run during execution
        reactor.callLater(0.1, self.sendMessages)
        reactor.callLater(1, self.printInfo)
        # Initial startup is instant, but it updates every 10 minutes.
        self.world_save_stack = []
        reactor.callLater(60, self.saveWorlds)
        if self.enable_archives:
            if "archives" not in protocol_plugins:
                self.loadPlugin('archives')
            reactor.callLater(1, self.loadArchives)
        if self.backup_auto:
            reactor.callLater(float(self.backup_freq * 60), self.AutoBackup)
        gc.disable()
        self.cleanGarbage()
        self.runServerHook("factoryStarted")

    def registerHook(self, hook, func):
        "Registers func as something to be run for hook 'hook'."
        if hook not in self.hooks:
            self.serverHooks[hook] = []
        self.serverHooks[hook].append(func)

    def unregisterHook(self, hook, func):
        "Unregisters func from hook 'hook'."
        try:
            self.serverHooks[hook].remove(func)
        except (KeyError, ValueError):
            self.logger.warn("Hook '%s' is not registered to %s." % (hook, func))

    def runHook(self, hook, *args, **kwds):
        "Runs the hook 'hook'."
        for func in self.hooks.get(hook, []):
            result = func(*args, **kwds)
            # If they return False, we can skip over and return
            if result is not None:
                return result
        return None

    def cleanGarbage(self):
        count = gc.collect()
        self.logger.info("%i garbage objects collected, %i were uncollected." % (count, len(gc.garbage)))
        reactor.callLater(60*15, self.cleanGarbage)
        self.runServerHook({"collected": count, "uncollected": len(gc.garbage)})

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
        worlds = ConfigParser()
        worlds.read("config/data/worlds.meta")
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
        bans = ConfigParser()
        bans.read("config/data/bans.meta")
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
                try:
                    self.lastseen[username] = lastseen.getfloat("lastseen", username)
                except Exception as a:
                    self.logger.error("Unable to read the lastseen for %s!" % username)
                    self.logger.error("%s" % a)
                    self.logger.warn("Giving up on lastseen.")
                    break
        # Read in the worlds
        if worlds.has_section("worlds"):
            for name in worlds.options("worlds"):
                if name is self.default_name:
                    self.default_loaded = True
        else:
            self.worlds[self.default_name] = None
        if not self.default_loaded:
            self.worlds[self.default_name] = None
        self.runServerHook("metaLoaded")

    def saveMeta(self):
        "Saves the server's meta back to a file."
        config = ConfigParser()
        specs = ConfigParser()
        lastseen = ConfigParser()
        bans = ConfigParser()
        worlds = ConfigParser()
        # Make the sections
        config.add_section("owners")
        config.add_section("directors")
        config.add_section("admins")
        config.add_section("mods")
        config.add_section("helpers")
        config.add_section("silenced")
        bans.add_section("banned")
        bans.add_section("ipbanned")
        specs.add_section("spectators")
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
            try:
                lastseen.set("lastseen", username, str(ls))
            except Exception as a:
                self.logger.error("Unable to save lastseen for %s.")
                self.logger.error("%s" % a)
                self.logger.warn("Giving up on lastseen.")
                break
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
        fp = open("config/data/worlds.meta", "w")
        worlds.write(fp)
        fp.close()
        self.runServerHook("metaSaved")

    def printInfo(self):
        if not len(self.clients) == 0:
            self.logger.info("There are %s users on the server." % len(self.clients))
            for key in self.worlds:
                if len(self.worlds[key].clients) > 0:
                    self.logger.info("%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))
        if (time.time() - self.last_heartbeat) > 180:
            self.heartbeat = None
            self.heartbeat = Heartbeat(self)
        reactor.callLater(60, self.printInfo)

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
        if not self.saving:
            if not self.world_save_stack:
                self.world_save_stack = list(self.worlds)
            key = self.world_save_stack.pop()
            self.saveWorld(key)
            if not self.world_save_stack:
                reactor.callLater(60, self.saveWorlds)
                self.saveMeta()
            else:
                reactor.callLater(1, self.saveWorlds)

    def saveWorld(self, world_id,shutdown = False):
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
        except:
            self.logger.info("Error saving %s" % world_id)
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
            self.logger.info("%s is joining world %s" %(user.username, new_world.basename))
        except:
            self.logger.info("%s is joining world %s" %(user.transport.getPeer().host, new_world.basename))
        if hasattr(user, "world") and user.world:
            self.leaveWorld(user.world, user)
        user.world = new_world
        new_world.clients.add(user)
        if not worldid == self.default_name and not new_world.ASD == None:
            new_world.ASD.kill()
            new_world.ASD = None
        self.runServerHook("worldJoined", {"world_id": worldid, "client": user})
        return new_world

    def leaveWorld(self, world, user):
        world.clients.remove(user)
        self.runServerHook("worldLeft", {"world_id": world.id, "client": user})
        if world.autoshutdown and len(world.clients) < 1:
            if world.basename == ("worlds/" + self.default_name):
                return
            else:
                if not self.asd_delay == 0:
                    try:
                        world.ASD = ResettableTimer(self.asd_delay*60, 1 , world.unload, ASD=True)
                    except Exception:
                        world.ASD = ResettableTimer(self.asd_delay*60, 1 , world.unload)
                else:
                    try:
                        world.ASD = ResettableTimer(30, 1, world.unload, ASD=True)
                    except Exception:
                        world.ASD = ResettableTimer(30, 1, world.unload)
                world.ASD.start()

    def loadWorld(self, filename, world_id):
        """
        Loads the given world file under the given world ID, or a random one.
        Returns the ID of the new world.
        """
        world = self.worlds[world_id] = World(filename, factory=self)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        self.logger.info("World '%s' Booted." % world_id)
        self.runServerHook("worldLoaded", {"world_id": world_id})
        return world_id

    def unloadWorld(self, world_id, ASD=False):
        """
        Unloads the given world ID.
        """
        try:
            if ASD and len(self.worlds[world_id].clients) > 0:
                self.worlds[world_id].ASD.kill()
                self.worlds[world_id].ASD = None
                return
        except KeyError:
            return
        # Devs should check this on input level
        assert world_id != self.default_name
        if not self.worlds[world_id].ASD == None:
            self.worlds[world_id].ASD.kill()
            self.worlds[world_id].ASD = None
        for client in list(list(self.worlds[world_id].clients))[:]:
            client.changeToWorld(self.default_name)
            client.sendServerMessage("World '%s' has been Shutdown." % world_id)
        self.worlds[world_id].stop()
        self.saveWorld(world_id,True)
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
            client.sendServerMessage("%s has been Rebooted" % world_id)
        self.worlds[world_id].stop()
        self.worlds[world_id].flush()
        self.worlds[world_id].save_meta()
        del self.worlds[world_id]
        world = self.worlds[world_id] =  World("worlds/%s" % world_id, world_id, factory=self)
        world.source = "worlds/" + world_id
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
            while True:
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
                            data = (id,colour,username,text)
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
                                sendmessage = self.runHook("changeworld", source_client)
                                if sendmessage:
                                    client.sendNormalMessage("%s%s&e has joined the world." % (source_client.userColour(), source_client.username))
                    # Someone left!
                    elif task is TASK_PLAYERLEAVE:
                        self.runServerHook("onPlayerLeave", {"client": source_client})
                        # Only run it for clients who weren't the source.
                        for client in self.clients.values():
                            client.sendPlayerLeave(*data)
                            if not source_client.username is None:
                                client.sendNormalMessage("%s%s&e has gone offline." % (source_client.userColour(), source_client.username))
                            else:
                                source_client.logger.warn("Pinged the server.")
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
                except Exception, e:
                    self.logger.error(traceback.format_exc())
        except Empty:
            pass
        # OK, now, for every world, let them read their queues
        for world in self.worlds.values():
            world.read_queue()
        # Come back soon!
        reactor.callLater(0.1, self.sendMessages)

    def newWorld(self, new_name, template="default", client=None):
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
            except:
                if not client is None:
                    client.sendServerMessage("That template doesn't exist.")
                return False
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

    def addBan(self, username, reason):
        self.banned[username.lower()] = reason
        self.runServerHook("playerBanned", {"username": username.lower(), "reason": reason})

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

    def AutoBackup(self):
        for world in self.worlds:
            self.Backup(world)
        if self.backup_auto:
            reactor.callLater(float(self.backup_freq * 60), self.AutoBackup)

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

    def messagestrip(self, message):
        strippedmessage = ""
        for x in message:
            if ord(str(x)) < 128:
                strippedmessage = strippedmessage + str(x)
        message = strippedmessage
        for x in self.filter:
            rep = re.compile(x[0], re.IGNORECASE)
            message = rep.sub(x[1], message)
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
                        except ValueError, e:
                            self.logger.warning("Bad archive filename %s" % subfilename)
                            continue
                        if name not in self.archives:
                            self.archives[name] = {}
                        self.archives[name][when] = "%s/%s" % (name, subfilename)
        self.logger.info("Loaded %s discrete archives." % len(self.archives))
        reactor.callLater(300, self.loadArchives)
        self.runServerHook("archivesLoaded", {"number": len(self.archives)})

    def getMemoryUsage(self):
        """
        Attempts to retrieve memory usage. Works on Windows and unix like operating systems.
        Returns a float representing how many MB is in use.
        """
        if platform.system() == "Windows":
            return self._getMemoryUsageWin32()
        else:
            result = self._getMemoryUsageUnix()
            if int(result) == 0:
                result = self._getMemoryUsageLinux()
            return result

    def _getMemoryUsageLinux(self):
        "Gets the memory usage, linux style."
        try:
            with open("/proc/%d/status" % os.getpid()) as f:
                for line in f.readlines():
                    tokens = line.split()
                    if tokens[0] == "VmSize:":
                        return float(tokens[1]) / 1024.0
        except:
            return 0.0

    def _getMemoryUsageUnix(self):
        "Gets the memory usage, UNIX style."
        try:
            proc = subprocess.Popen(["ps", "-o", "vsize", "-p", str(os.getpid())], stdout=subprocess.PIPE)
            return float(proc.communicate()[0].split()[1]) / 1024.0
        except:
            return 0.0

    def _getMemoryUsageWin32(self):
        "Gets the memory usage, Win32 style."
        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [('cb', ctypes.c_ulong),
                        ('PageFaultCount', ctypes.c_ulong),
                        ('PeakWorkingSetSize', ctypes.c_size_t),
                        ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t),
                        ('PeakPagefileUsage', ctypes.c_size_t),
                        ('PrivateUsage', ctypes.c_size_t),
                       ]

        mem_struct = PROCESS_MEMORY_COUNTERS_EX()
        ret = ctypes.windll.psapi.GetProcessMemoryInfo(
                    ctypes.windll.kernel32.GetCurrentProcess(),
                    ctypes.byref(mem_struct),
                    ctypes.sizeof(mem_struct)
                    )
        if not ret:
            return 0
        return mem_struct.PrivateUsage / 1024.0 / 1024.0

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
                    if self.ircbot and not (self.irc_channel == "#icraft" or self.irc_channel == "#channel") and not self.irc_nick == "botname":
                        reactor.connectTCP(self.irc_config.get("irc", "server"), self.irc_config.getint("irc", "port"), self.irc_relay)
                        self.runServerHook("IRCBotReloaded")
                    else:
                        self.logger.error("IRC Bot failed to connect, you could modify, rename or remove irc.conf")
                        self.logger.error("You need to change your 'botname' and 'channel' fields to fix this error or turn the bot off by disabling 'ircbot'")
                    return True
            except:
                return False
        return False

    def reloadConfig(self):
        try:
            # TODO: Figure out which of these would work dynamically, otherwise delete them from this area.
            self.duplicate_logins = self.options_config.getboolean("options", "duplicate_logins")
            self.info_url = self.options_config.get("options", "info_url")
            self.away_kick = self.options_config.getboolean("options", "away_kick")
            self.away_time = self.options_config.getint("options", "away_time")
            self.colors = self.options_config.getboolean("options", "colors")
            self.physics_limit = self.options_config.getint("worlds", "physics_limit")
            self.default_backup = self.options_config.get("worlds", "default_backup")
            self.asd_delay = self.options_config.getint("worlds", "asd_delay")
            self.gchat = self.options_config.getboolean("worlds", "gchat")
            self.grief_blocks = self.ploptions_config.getint("antigrief", "blocks")
            self.grief_time = self.ploptions_config.getint("antigrief", "time")
            self.backup_freq = self.ploptions_config.getint("backups", "backup_freq")
            self.backup_default = self.ploptions_config.getboolean("backups", "backup_default")
            self.backup_max = self.ploptions_config.getint("backups", "backup_max")
            self.backup_auto = self.ploptions_config.getboolean("backups", "backup_auto")
            self.enable_archives = self.ploptions_config.getboolean("archiver", "enable_archiver")
            self.currency = self.ploptions_config.get("bank", "currency")
            self.useblblimit = self.ploptions_config.getboolean("blb", "use_blb_limiter")
            if self.useblblimit:
                self.blblimit = {}
                self.blblimit["player"] = self.ploptions_config.getint("blb", "player")
                self.blblimit["builder"] = self.ploptions_config.getint("blb", "builder")
                self.blblimit["op"] = self.ploptions_config.getint("blb", "op")
                self.blblimit["worldowner"] = self.ploptions_config.getint("blb", "worldowner")
                self.blblimit["helper"] = self.ploptions_config.getint("blb", "helper")
                self.blblimit["mod"] = self.ploptions_config.getint("blb", "mod")
                self.blblimit["admin"] = self.ploptions_config.getint("blb", "admin")
                self.blblimit["director"] = self.ploptions_config.getint("blb", "director")
                self.blblimit["owner"] = self.ploptions_config.getint("blb", "owner")
            if self.backup_auto:
                reactor.callLater(float(self.backup_freq * 60),self.AutoBackup)
            self.runServerHook("configReloaded", {"success": True})
            return True
        except:
            self.runServerHook("configReloaded", {"success": False})
            return False