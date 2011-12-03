# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import gzip, os, shutil, sys, traceback
from ConfigParser import RawConfigParser as ConfigParser
from Queue import Empty

from twisted.internet.defer import Deferred

from arc.blockstore import BlockStore
from arc.constants import *
from arc.globals import *
from arc.logger import ColouredLogger
from arc.blocktracker import Tracker

debug = (True if "--debug" in sys.argv else False)

import logging

class World(object):
    """
    Represents... well, a World.
    This is the new, efficient version, that uses the disk as the main backing
    store. Any changes are stored in self.queued_blocks (and that is looked in
    for specfic blook lookups first) until the level is flushed, at which point
    the gzip on disk is updated with the new blocks.
    """

    def __init__(self, basename, load=True, factory=None):
        self.logger = ColouredLogger(debug)
        self.basename = basename
        self.hidden = False
        if self.basename.split("/")[1].startswith("."):
            self.hidden = True
        self.blocks_path = os.path.join(basename, "blocks.gz")
        self.meta_path = os.path.join(basename, "world.meta")
        self.id = None
        self.factory = factory
        # Other settings
        self.ops = set()
        self.builders = set()
        self.status = dict()
        self.status["cfgversion"] = ".".join([str(s) for s in CFGVERSION["world.meta"]])
        self.status["owner"] = "n/a"
        self.status["all_build"] = True
        self.status["private"] = False
        self.status["is_archive"] = False
        self.status["autoshutdown"] = True
        self.status["saving"] = False
        self.status["zoned"] = False
        self.status["physics"] = False
        self.status["finite_water"] = True
        self._physics = False
        self._finite_water = False
        self.portals = {}
        self.msgblocks = {}
        self.worldbans = set()
        self.cmdblocks = {}
        self.mines = list([])
        self.userzones = {}
        self.rankzones = {}
        self.entitylist = []
        # Unsaved variables
        self.entities_worldblockchangesdict = {}
        self.entities_childerenlist = []
        self.entities_childerenlist_index = 0
        self.entities_epicentity = []
        self.status["modified"] = False
        self.status["last_access_count"] = 0
        # Dict of deferreds to call when a block is gotten.
        self.blockgets = {}
        # Current deferred to call after a flush is complete
        self.flush_deferred = None
        if load:
            assert os.path.isfile(self.blocks_path), "No blocks file: %s" % self.blocks_path
            assert os.path.isfile(self.meta_path), "No meta file: %s" % self.blocks_path
            self.load_meta()

    def start(self):
        "Starts up this World; we spawn a BlockStore, and run it."
        self.blocktracker = Tracker("blocks", directory=self.basename)
        self.blockstore = BlockStore(self.blocks_path, self.x, self.y, self.z)
        self.blockstore.start()
        # If physics is on, turn it on
        if self._physics:
            self.blockstore.in_queue.put([TASK_PHYSICSON])
        if self._finite_water:
            self.blockstore.in_queue.put([TASK_FWATERON])

    def stop(self):
        "Signals the BlockStore to stop."
        self.blockstore.in_queue.put([TASK_STOP])
        self.save_meta()
        try:
            self.blocktracker.close()
            del self.blocktracker
        except AttributeError:
            pass

    def read_queue(self):
        "Reads messages from the BlockStore and acts on them."
        try:
            for i in range(1000):
                task = self.blockstore.out_queue.get_nowait()
                try:
                    # We might have been told a flush is complete!
                    if task[0] is TASK_FLUSH:
                        if self.flush_deferred:
                            self.flush_deferred.callback(None)
                            self.flush_deferred = None
                    # Or got a response to a BLOCKGET
                    elif task[0] is TASK_BLOCKGET:
                        try:
                            self.blockgets[task[1]].callback(task[2])
                            del self.blockgets[task[1]]
                        except KeyError:
                            pass # We already sent this one.
                    # Or the physics changes a block
                    elif task[0] is TASK_BLOCKSET:
                        self.factory.queue.put((self, TASK_BLOCKSET, task[1]))
                    # Or there's a world message
                    elif task[0] is TASK_WORLDMESSAGE:
                        self.factory.queue.put((self, TASK_WORLDMESSAGE, (255, self, task[1])))
                    # Or a message for the admins
                    elif task[0] is TASK_ADMINMESSAGE:
                        self.factory.queue.put((self, TASK_ADMINMESSAGE, (task[1] % {"id": self.id},)))
                    # ???
                    else:
                        raise ValueError("Unknown World task: %s" % task)
                except:
                    self.logger.error(traceback.format_exc())
        except Empty:
            pass

    def get_physics(self):
        return self._physics

    def set_physics(self, value):
        self._physics = value
        if hasattr(self, "blockstore"):
            if value:
                self.blockstore.in_queue.put([TASK_PHYSICSON])
            else:
                self.blockstore.in_queue.put([TASK_PHYSICSOFF])
    physics = property(get_physics, set_physics)

    def get_finite_water(self):
        return self._finite_water

    def set_finite_water(self, value):
        self._finite_water = value
        if hasattr(self, "blockstore"):
            if value:
                self.blockstore.in_queue.put([TASK_FWATERON])
            else:
                self.blockstore.in_queue.put([TASK_FWATEROFF])
    finite_water = property(get_finite_water, set_finite_water)

    def start_unflooding(self):
        self.blockstore.in_queue.put([TASK_UNFLOOD])

    def load_meta(self):
        config = ConfigParser()
        config.read(self.meta_path)
        if config.has_section("cfginfo"):
            self.status["cfgversion"] = config.get("cfginfo", "version")
        else:
            self.status["cfgversion"] = "1.0.0"
        if not checkConfigVersion(self.status["cfgversion"], CFGVERSION["world.meta"]):
            self.logger.warn("World %s has an outdated world.meta, data may be lost." % self.basename)
            self.logger.warn("A copy of the original file has been made as world.meta.orig.")
            shutil.copy(self.meta_path, os.path.join(self.basename, "world.meta.orig"))
        self.x = config.getint("size", "x")
        self.y = config.getint("size", "y")
        self.z = config.getint("size", "z")
        self.spawn = (
            config.getint("spawn", "x"),
            config.getint("spawn", "y"),
            config.getint("spawn", "z"),
            config.getint("spawn", "h"),
        )
        if config.has_section("options"):
            if config.has_option("options", "autoshutdown"):
                self.status["autoshutdown"] = config.getboolean("options", "autoshutdown")
            else:
                self.status["autoshutdown"] = False
            if config.has_option("options", "owner"):
                self.status["owner"] = config.get("options", "owner").lower()
            else:
                self.status["owner"] = "n/a"
            if config.has_option("options", "all_build"):
                self.status["all_build"] = config.getboolean("options", "all_build")
            else:
                self.status["all_build"] = True
            if config.has_option("options", "private"):
                self.status["private"] = config.getboolean("options", "private")
            else:
                self.status["private"] = False
            if config.has_option("options", "zoned"):
                self.status["zoned"] = config.getboolean("options", "zoned")
            else:
                self.status["zoned"] = True
            if config.has_option("options", "physics"):
                self.status["physics"] = config.getboolean("options", "physics")
            else:
                self.status["physics"] = False
            if config.has_option("options", "finite_water"):
                self.status["finite_water"] = config.getboolean("options", "finite_water")
            else:
                self.status["finite_water"] = False
        if config.has_section("ops"):
            self.ops = set(x.lower() for x in config.options("ops"))
        else:
            self.ops = set()
        if config.has_section("builders"):
            self.builders = set(x.lower() for x in config.options("builders"))
        else:
            self.builders = set()
        if config.has_section("portals"):
            for option in config.options("portals"):
                offset = int(option)
                destination = [x.strip() for x in config.get("portals", option).split(",")]
                coords = map(int, destination[1:])
                if len(coords) == 3:
                    coords = coords + [0]
                if not (0 <= coords[3] <= 255):
                    coords[3] = 0
                self.portals[offset] = destination[:1] + coords
        if config.has_section("msgblocks"):
            for option in config.options("msgblocks"):
                self.msgblocks[int(option)] = config.get("msgblocks", option)
        if config.has_section("worldbans"):
            self.worldbans = set(x.lower() for x in config.options("worldbans"))
        if config.has_section("cmdblocks"):
            for option in config.options("cmdblocks"):
                cmd = config.get("cmdblocks", option)
                listofcmd = cmd.split("&n")
                for x in listofcmd:
                    x = x.replace("&n", "")
                    if x == "":
                        listofcmd.remove(x)
                self.cmdblocks[int(option)] = listofcmd
        if config.has_section("mines"):
            for option in config.options("mines"):
                self.mines.append(int(option))
        if config.has_section("userzones"):
            for option in config.options("userzones"):
                destination = [x.strip() for x in config.get("userzones", option).split(",")]
                coords = map(int, destination[1:7])
                users = map(str, destination[7:])
                i = 1
                while True:
                    if not i in self.userzones:
                        self.userzones[i] = destination[:1] + coords + users
                        break
                    else:
                        i += 1
        if config.has_section("rankzones"):
            for option in config.options("rankzones"):
                user = option
                destination = [x.strip() for x in config.get("rankzones", option).split(",")]
                coords = map(int, destination[1:7])
                i = 1
                while True:
                    if not i in self.rankzones:
                        self.rankzones[i] = destination[:1] + coords + destination[7:]
                        break
                    else:
                        i += 1
        if config.has_section("entitylist"):
            for option in config.options("entitylist"):
                entry = config.get("entitylist", option)
                if entry.find("[") != -1:
                    self.entitylist.append(eval(entry))
                else:
                    entry = [x.strip() for x in config.get("entitylist", option).split(",")]
                    for i in range(len(entry)):
                        try:
                            entry[i] = int(entry[i])
                        except:
                            if entry[i] == "False":
                                entry[i] = False
                            elif entry[i] == "True":
                                entry[i] = True
                    self.entitylist.append([entry[0],(entry[1],entry[2],entry[3])] + entry[4:])

    @property
    def store_raw_blocks(self):
        return self.physics

    def saved(self):
        self.factory.saving = False

    def flush(self):
        self.blockstore.in_queue.put([TASK_FLUSH, self.saved])

    def save_meta(self):
        config = ConfigParser()
        config.add_section("entitylist")
        config.add_section("rankzones")
        config.add_section("userzones")
        config.add_section("mines")
        config.add_section("cmdblocks")
        config.add_section("msgblocks")
        config.add_section("portals")
        config.add_section("worldbans")
        config.add_section("ops")
        config.add_section("builders")
        config.add_section("options")
        config.add_section("spawn")
        config.add_section("size")
        config.add_section("cfginfo")
        config.set("cfginfo", "version", str(self.status["cfgversion"]))
        config.set("cfginfo", "name", "world.meta")
        config.set("size", "z", str(self.z))
        config.set("size", "y", str(self.y))
        config.set("size", "x", str(self.x))
        config.set("spawn", "h", str(self.spawn[3]))
        config.set("spawn", "z", str(self.spawn[2]))
        config.set("spawn", "y", str(self.spawn[1]))
        config.set("spawn", "x", str(self.spawn[0]))
        # Store display settings
        config.set("options", "finite_water", str(self.status["finite_water"]))
        config.set("options", "physics", str(self.status["physics"]))
        # Store Autoshutdown
        config.set("options", "autoshutdown", str(self.status["autoshutdown"]))
        # Store permissions
        config.set("options", "zoned", str(self.status["zoned"]))
        config.set("options", "private", str(self.status["private"]))
        config.set("options", "all_build", str(self.status["all_build"]))
        # Store owner
        config.set("options", "owner", str(self.status["owner"]))
        # Store ops
        for op in self.ops:
            config.set("ops", op, "true")
        # Store builders
        for builder in self.builders:
            config.set("builders", builder, "true")
        # Store portals
        for offset, dest in self.portals.items():
            config.set("portals", str(offset), ", ".join(map(str, dest)))
        # Store msgblocks
        for offset, msg in self.msgblocks.items():
            config.set("msgblocks", str(offset), msg)
        # Store worldbans
        for name in self.worldbans:
            config.set("worldbans", str(name), "True")
        # Store cmdblocks
        for offset, cmd in self.cmdblocks.items():
            cmdstr = ""
            for x in cmd:
                cmdstr = cmdstr + x + "&n"
            config.set("cmdblocks", str(offset), cmdstr)
        # Store mines
        for offset in self.mines:
            config.set("mines", str(offset), "True")
        # Store user zones
        for name, zone in self.userzones.items():
            config.set("userzones", str(name), ", ".join(map(str, zone)))
        # Store rank zones
        for name, zone in self.rankzones.items():
            config.set("rankzones", str(name), ", ".join(map(str, zone)))
        # Store entitylist
        for i in range(len(self.entitylist)):
            entry = self.entitylist[i]
            config.set("entitylist", str(i), str(entry))
        fp = open(self.meta_path, "w")
        config.write(fp)
        fp.flush()
        os.fsync(fp.fileno())
        fp.close()

    @classmethod
    def create(cls, basename, x, y, z, sx, sy, sz, sh, levels):
        "Creates a new World file set"
        if not os.path.exists("worlds/"):
            os.mkdir("worlds/")
        os.mkdir(basename)
        world = cls(basename, load=False)
        BlockStore.create_new(world.blocks_path, x, y, z, levels)
        world.x = x
        world.y = y
        world.z = z
        world.spawn = (sx, sy, sz, sh)
        world.save_meta()
        world.load_meta()
        return world

    # The following methods should be simplified into 1 method
    def add_portal(self, x, y, z, to):
        offset = self.get_offset(x, y, z)
        self.portals[offset] = to

    def delete_portal(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.portals[offset]
            return True
        except KeyError:
            return False

    def get_portal(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.portals[offset]

    def has_portal(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.portals

    def clear_portals(self):
        self.portals = {}

    def add_msgblock(self, x, y, z, msg):
        offset = self.get_offset(x, y, z)
        self.msgblocks[offset] = msg

    def delete_msgblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.msgblocks[offset]
            return True
        except KeyError:
            return False

    def get_msgblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.msgblocks[offset]

    def has_msgblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.msgblocks

    def clear_msgblocks(self):
        self.msgblocks = {}

    def add_worldban(self, name):
        self.worldbans.add(name)

    def delete_worldban(self, name):
        try:
            self.worldbans.remove(name)
            return True
        except KeyError:
            return False

    def add_cmdblock(self, x, y, z, cmd):
        offset = self.get_offset(x, y, z)
        self.cmdblocks[offset] = cmd

    def delete_cmdblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.cmdblocks[offset]
            return True
        except KeyError:
            return False

    def get_cmdblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.cmdblocks[offset]

    def has_cmdblock(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.cmdblocks

    def add_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        self.mines.append(offset)

    def delete_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            self.mines.remove(offset)
            return True
        except KeyError:
            return False

    def has_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.mines

    def clear_mines(self):
        self.mines = []
    # The above methods needs to be simplified into 1 method

    def isWorldBanned(self, name):
        return name.lower() in self.worldbans

    def __getitem__(self, (x, y, z)):
        "Gets the value of a block. Returns a Deferred."
        self.blockstore.in_queue.put([TASK_BLOCKGET, (x, y, z)])
        if (x, y, z) not in self.blockgets:
            self.blockgets[x, y, z] = Deferred()
        return self.blockgets[x, y, z]

    def __setitem__(self, (x, y, z), block):
        "Sets the value of a block."
        assert isinstance(block, str) and len(block) == 1
        # Make sure this is inside boundaries
        self.get_offset(x, y, z)
        self.blockstore.in_queue.put([TASK_BLOCKSET, (x, y, z), block])

    def get_offset(self, x, y, z):
        "Turns block coordinates into a data offset"
        assert 0 <= x < self.x
        assert 0 <= y < self.y
        assert 0 <= z < self.z
        return y*(self.x*self.z) + z*(self.x) + x

    def get_coords(self, offset):
        "Turns a data offset into coordinates"
        x = offset % self.x
        z = (offset // self.x) % self.z
        y = offset // (self.x * self.z)
        return x, y, z

    def get_gzip_handle(self):
        """
        Returns a Deferred that will eventually yield a handle to this world's
        gzip blocks file (gzipped, not the contents).
        """
        # First, queue it
        self.blockstore.in_queue.put([TASK_FLUSH,self.saved])
        # Now, make the flush deferred if we haven't.
        if not self.flush_deferred:
            self.flush_deferred = Deferred()
        # Next, make a deferred for us to return
        handle_deferred = Deferred()
        # Now, make a function that will call that on the first one
        def on_flush(result):
            handle_deferred.callback((
                open(self.blocks_path, "rb"),
                os.stat(self.blocks_path).st_size,
            ))
        self.flush_deferred.addCallback(on_flush)
        return handle_deferred
