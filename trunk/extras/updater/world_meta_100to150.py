# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import ConfigParser, fnmatch, logging, os, sys, time, traceback

class Updater(object):
    def __init__(self):
        self.logger = logging.getLogger("Updater")
        self.update()

    def update(self):
        self.i = 0
        self.j = 0
        if not os.path.isdir("worlds/"):
            self.logger.error("Please copy this updater to the root director (where the run.bat resides) and run this updater again.")
            sys.exit(1)
        self.logger.info("Now resaving worlds in newest format...")

        matches = [os.path.join(r, f) for r, d, fs in os.walk("worlds") for f in fs if f == "world.meta"]
        for world in matches:
            self.logger.info("Processing world %s..." % world)
            try:
                self.resaveMeta(world)
            except Exception as e:
                self.logger.error("Error in processing world %s: %s" % (world, e))
                self.logger.error(traceback.format_exc())
                self.j += 1
            else:
                self.i += 1
        self.logger.info("Finished processing. %s worlds were processed, and %s worlds cannot be processed." % (i, j))

    def resaveMeta(self, worldname):
        config = ConfigParser.ConfigParser()
        try:
            config.read(worldname)
        except Exception as e:
            self.logger.error("Error reading file %s." % worldname)
            self.logger.error(traceback.format_exc())
            self.logger.error("Resuming process in 5 seconds.")
            self.j += 1
            time.sleep(5)
            return
        if config.has_section("cfginfo"):
            cfgversion = config.get("cfginfo", "version")
            if cfgversion == "1.5.0":
                # Does not need update
                self.logger.info("World %s is already at the latest format." % worldname)
                return
        else:
            self.logger.warn("Unable to fetch config version, errors may occur.")
        try:
            x = config.getint("size", "x")
            y = config.getint("size", "y")
            z = config.getint("size", "z")
            spawn = (
                config.getint("spawn", "x"),
                config.getint("spawn", "y"),
                config.getint("spawn", "z"),
                config.getint("spawn", "h"),
            )
        except Exception as e:
            self.logger.error("World %s has a meta that does not contain size or spawn information." % worldname)
            self.logger.error(traceback.format_exc())
            self.logger.error("Resuming process in 5 seconds.")
            self.j += 1
            time.sleep(5)
            return
        if config.has_section("autoshutdown"):
            autoshutdown = config.get("autoshutdown", "autoshutdown")
        else:
            autoshutdown = True
        if config.has_section("owner"):
            owner = config.get("owner", "owner").lower()
        else:
            owner = "n/a"
        if config.has_section("ops"):
            ops = set(g.lower() for g in config.options("ops"))
        else:
            ops = set()
        if config.has_section("builders"):
            builders = set(m.lower() for m in config.options("builders"))
        else:
            builders = set()
        if config.has_section("permissions"):
            if config.has_option("permissions", "all_write"):
                all_build = config.getboolean("permissions", "all_write")
            else:
                all_build = True
            if config.has_option("permissions", "private"):
                private = config.getboolean("permissions", "private")
            else:
                private = False
            if config.has_option("permissions", "zoned"):
                zoned = config.getboolean("permissions", "zoned")
            else:
                zoned = True
        else:
            all_build = True
            private = False
            zoned = True
        if config.has_section("display"):
            if config.has_option("display", "physics"):
                physics = config.getboolean("display", "physics")
            else:
                physics = False
            if config.has_option("display", "finite_water"):
                finite_water = config.getboolean("display", "finite_water")
            else:
                finite_water = True
        else:
            physics = False
            finite_water = True
        portals = {}
        if config.has_section("teleports"):
            for option in config.options("teleports"):
                offset = int(option)
                destination = [j.strip() for j in config.get("teleports", option).split(",")]
                coords = map(int, destination[1:])
                if len(coords) == 3:
                    coords = coords + [0]
                if not (0 <= coords[3] <= 255):
                    coords[3] = 0
                portals[offset] = destination[:1] + coords
        msgblocks = {}
        if config.has_section("messages"):
            for option in config.options("messages"):
                msgblocks[int(option)] = config.get("messages", option)
        worldbans = {}
        if config.has_section("worldbans"):
            for option in config.options("worldbans"):
                worldbans[option] = "True"
        cmdblocks = {}
        if config.has_section("commands"):
            for option in config.options("commands"):
                cmd = config.get("commands", option)
                listofcmd = cmd.split("&n")
                for l in listofcmd:
                    l = l.replace("&n", "")
                    if l == "":
                        listofcmd.remove(l)
                cmdblocks[int(option)] = listofcmd
        mines = list([])
        if config.has_section("mines"):
            for option in config.options("mines"):
                mines.append(int(option))
        userzones = {}
        if config.has_section("userzones"):
            for option in config.options("userzones"):
                destination = [f.strip() for f in config.get("userzones", option).split(",")]
                coords = map(int, destination[1:7])
                users = map(str, destination[7:])
                i = 1
                while True:
                    if not i in userzones:
                        userzones[i] = destination[:1] + coords + users
                        break
                    else:
                        i += 1
        rankzones = {}
        if config.has_section("rankzones"):
            for option in config.options("rankzones"):
                user = option
                destination = [d.strip() for d in config.get("rankzones", option).split(",")]
                coords = map(int, destination[1:7])
                i = 1
                while True:
                    if not i in rankzones:
                        rankzones[i] = destination[:1] + coords + destination[7:]
                        break
                    else:
                        i += 1
        entitylist = []
        if config.has_section("entitylist"):
            for option in config.options("entitylist"):
                entry = config.get("entitylist", option)
                if entry.find("[") != -1:
                    entitylist.append(eval(entry))
                else:
                    entry = [w.strip() for w in config.get("entitylist", option).split(",")]
                    for i in range(len(entry)):
                        try:
                            entry[i] = int(entry[i])
                        except:
                            if entry[i] == "False":
                                entry[i] = False
                            elif entry[i] == "True":
                                entry[i] = True
                    entitylist.append([entry[0],(entry[1],entry[2],entry[3])] + entry[4:])
        # Okay, save them in new format.
        del config
        config = ConfigParser.ConfigParser()
        config.add_section("cfginfo")
        config.add_section("size")
        config.add_section("spawn")
        config.add_section("options")
        config.add_section("ops")
        config.add_section("builders")
        config.add_section("portals")
        config.add_section("msgblocks")
        config.add_section("worldbans")
        config.add_section("cmdblocks")
        config.add_section("mines")
        config.add_section("userzones")
        config.add_section("rankzones")
        config.add_section("entitylist")
        config.set("cfginfo", "name", "world.meta")
        config.set("cfginfo", "version", "1.5.0")
        config.set("size", "x", str(x))
        config.set("size", "y", str(y))
        config.set("size", "z", str(z))
        config.set("spawn", "x", str(spawn[0]))
        config.set("spawn", "y", str(spawn[1]))
        config.set("spawn", "z", str(spawn[2]))
        config.set("spawn", "h", str(spawn[3]))
        # Store Autoshutdown
        config.set("options", "autoshutdown", str(autoshutdown))
        # Store owner
        config.set("options", "owner", str(owner))
        # Store permissions
        config.set("options", "all_build", str(all_build))
        config.set("options", "private", str(private))
        config.set("options", "zoned", str(zoned))
        # Store display settings
        config.set("options", "physics", str(physics))
        config.set("options", "finite_water", str(finite_water))
        # Store ops
        for op in ops:
            config.set("ops", op, "true")
        # Store builders
        for builder in builders:
            config.set("builders", builder, "true")
        # Store portals
        for offset, dest in portals.items():
            config.set("portals", str(offset), ", ".join(map(str, dest)))
        # Store msgblocks
        for offset, msg in msgblocks.items():
            config.set("msgblocks", str(offset), msg)
        # Store worldbans
        for name in worldbans:
            config.set("worldbans", str(name), "True")
        # Store cmdblocks
        for offset, cmd in cmdblocks.items():
            cmdstr = ""
            for x in cmd:
                cmdstr = cmdstr + x + "&n"
            config.set("cmdblocks", str(offset), cmdstr)
        # Store mines
        for offset in mines:
            config.set("mines", str(offset), "True")
        # Store user zones
        for name, zone in userzones.items():
            config.set("userzones", str(name), ", ".join(map(str, zone)))
        # Store rank zones
        for name, zone in rankzones.items():
            config.set("rankzones", str(name), ", ".join(map(str, zone)))
        # Store entitylist
        for i in range(len(entitylist)):
            entry = entitylist[i]
            config.set("entitylist", str(i), str(entry))
        fp = open(meta_path, "w")
        config.write(fp)
        fp.flush()
        os.fsync(fp.fileno())
        fp.close()

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
        datefmt="%m/%d/%Y %H:%M:%S",
    )
    Updater()