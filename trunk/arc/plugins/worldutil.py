# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import inspect, os, random, shutil

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.world import World

class WorldUtilPlugin(object):
    commands = {
        "backup": "commandBackup",
        "backups": "commandBackups",
        "restore": "commandRestore",
        "deletebackup": "commandDeleteBackup",

        "physics": "commandPhysics",
        "physflush": "commandPhysflush",
        "unflood": "commandUnflood",
        "fwater": "commandFwater",

        "private": "commandPrivate",
        "lock": "commandLock",
        #"ponly": "commandPOnly"

        "asd": "commandAutoShutdown",

        "new": "commandNew",
        "rename": "commandRename",
        "shutdown": "commandShutdown",
        "boot": "commandBoot",
        "reboot": "commandReboot",
        "create": "commandCreate",
        "delete": "commandDelete",
        "undelete": "commandUnDelete",
        "deleted": "commandDeleted",
        "copyworld": "commandCopyWorld",

        "worlds": "commandWorlds",

        "templates": "commandTemplates",

        "l": "commandLoad",

        "home": "commandHome",
        "random": "commandRandom",

        "status": "commandStatus",
        "setspawn": "commandSetspawn",
        "worldstaff": "commandWorldStaff",
        "where": "commandWhere",
        "ops": "commandOps",
        "builders": "commandBuilders",
        }

    @config("category", "world")
    @config("rank", "op")
    @config("usage", "world")
    def commandBackup(self, data):
        "Makes a backup copy of the world."
        if len(data["parts"]) == 1:
            world_id = data["client"].world.id
        else:
            world_id = data["parts"][1]
        if len(data["parts"]) > 2:
            backupname = data["parts"][2]
        else:
            backupname = None
        response = self.factory.doBackup(world_id, "user", backupname)
        if response[0] == 1: # Success
            data["client"].sendServerMessage("World %s's backup %s is saved." % (world_id, response[1]))
            return
        if response[1] == 2:
            data["client"].sendServerMessage("World %s does not exist." % world_id)
        elif response[1] == 3:
            data["client"].sendServerMessage("Backup %s for world %s already exists." % (backupname, world_id))

    @config("category", "world")
    @config("rank", "op")
    @config("usage", "worldname [backupname]")
    def commandRestore(self, data):
        "Restore world to the indicated backup name/number.\nIf no backup name is specified, restore to the last backup."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Please specify a world ID")
            return
        world_id = data["parts"][1].lower()
        world_dir = ("worlds/%s/" % world_id)
        if len(data["parts"]) < 3:
            backups = os.listdir(world_dir + "backup/")
            backups.sort(lambda x, y: int(x) - int(y))
            backup_number = str(int(backups[-1]))
        else:
            backup_number = data["parts"][2]
        if not os.path.exists(world_dir + "backup/%s/" % backup_number):
            data["client"].sendServerMessage("Backup %s does not exist." % backup_number)
            return
        if not os.path.exists(world_dir + "blocks.gz.new"):
            shutil.copy((world_dir + "backup/%s/blocks.gz" % backup_number), world_dir)
            if os.path.exists(world_dir + "backup/%s/world.meta" % backup_number):
                shutil.copy((world_dir + "backup/%s/world.meta" % backup_number), world_dir)
        else:
            reactor.callLater(1, self.commandRestore, self, data)
        self.factory.unloadWorld(world_id, skiperror=True)
        data["client"].sendServerMessage("%s has been restored to %s and booted." % (world_id, backup_number))
        if world_id in self.factory.worlds:
            for client in self.factory.worlds[world_id].clients:
                client.changeToWorld(world_id)

    @config("category", "world")
    @config("usage", "world")
    def commandBackups(self, data):
        "Lists all backups this world has.\nIf world is not specified, the current world is used."
        if len(data["parts"]) > 1:
            world = data["parts"][1]
        else:
            if data["fromloc"] == "user":
                world = data["client"].world.id
            else:
                data["client"].sendServerMessage("You must supply a world.")
        if not os.path.exists("worlds/%s/" % world):
            data["client"].sendServerMessage("No backups found for %s." % world)
            return
        world_dir = "worlds/%s/" % world
        folders = os.listdir(world_dir + "backup/")
        Num_backups = list([])
        Name_backups = list([])
        for x in folders:
            if x.isdigit():
                Num_backups.append(x)
            else:
                Name_backups.append(x)
        Num_backups.sort(lambda x, y: int(x) - int(y))
        if Num_backups > 2:
            data["client"].sendServerList(["Backups for %s:" % world] + [Num_backups[0] + "-" + Num_backups[-1]] + Name_backups)
        else:
            data["client"].sendServerList(["Backups for %s:" % world] + Num_backups + Name_backups)

    @config("category", "world")
    @config("rank", "worldowner")
    @config("usage", "worldname backupname")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandDeleteBackup(self, data):
        "Deletes a backup of the world."
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        if not os.path.exists("worlds/%s/backup/%s" % (data["parts"][1], data["parts"][2])):
            data["client"].sendServerMessage("Backup %s for world %s doesn't exist." % (data["parts"][2], data["parts"][1]))
            return
        name = data["parts"][1]
        extra = "_0"
        if os.path.exists("worlds/.trash/%s" % name):
            def doRename():
                if os.path.exists("worlds/.trash/%s" % (name + extra)):
                    extra = "_" + str(int(extra[1:]) + 1)
                    reactor.callLater(0.1, doRename)
                else:
                    name = name + extra
            doRename()
        shutil.copytree("worlds/%s/backup/%s" % (parts[1], parts[2]), "worlds/.trash/%s/%s" % (name, parts[2]))
        shutil.rmtree("worlds/%s/backup/%s" % (parts[1], parts[2]))
        data["client"].sendServerMessage("Backup deleted as %s." % name)

    @config("category", "world")
    @config("rank", "op")
    @config("usage", "worldname")
    def commandUnflood(self, data):
        "Slowly removes all water and lava from the world."
        data["client"].world.start_unflooding()
        data["client"].sendWorldMessage("Unflooding has been initiated.")

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "on|off")
    @on_off_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandPhysics(self, data):
        "Enables or disables physics in this world."
        if data["onoff"] == "on":
            if data["client"].world.status["physics"]:
                data["client"].sendWorldMessage("Physics is already on here.")
                return
            if self.factory.numberWithPhysics() >= self.factory.physics_limit:
                data["client"].sendWorldMessage("There are already %s worlds with physics on (the max)." % self.factory.physics_limit)
            else:
                data["client"].world.status["physics"] = True
                data["client"].sendWorldMessage("This world now has physics enabled.")
                data["client"].world.status["modified"] = True
        else:
            if not data["client"].world.status["physics"]:
                data["client"].sendWorldMessage("Physics is already off here.")
            else:
                data["client"].world.status["physics"] = False
                data["client"].sendWorldMessage("This world now has physics disabled.")
                data["client"].world.status["modified"] = True

    @config("category", "world")
    @config("rank", "op")
    @config("usage", "on|off")
    @on_off_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandFwater(self, data):
        "Enables or disables finite water in this world."
        if data["onoff"] == "on":
            data["client"].world.status["finite_water"] = True
            data["client"].sendWorldMessage("This world now has finite water enabled.")
        else:
            data["client"].world.status["finite_water"] = False
            data["client"].sendWorldMessage("This world now has finite water disabled.")
        data["client"].world.status["modified"] = True

    @config("category", "world")
    @config("rank", "admin")
    def commandPhysflush(self, data):
        "Tells the physics engine to rescan the world."
        if data["client"].world.status["physics"]:
            if self.factory.numberWithPhysics() >= self.factory.physics_limit:
                data["client"].sendServerMessage("There are already %s worlds with physics on (the max)." % self.factory.physics_limit)
            else:
                data["client"].world.status["physics"] = False
                data["client"].world.status["physics"] = True
                data["client"].sendWorldMessage("This world now has a physics flush running.")
        else:
            data["client"].sendServerMessage("This world does not have physics on.")

    @config("category", "world")
    @config("rank", "op")
    @config("usage", "on|off")
    @on_off_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandPrivate(self, data):
        "/private on|off - Op\nEnables or disables the private status for this world."
        if data["onoff"] == "on":
            data["client"].world.status["private"] = True
            data["client"].sendWorldMessage("This world is now private.")
            data["client"].sendServerMessage("%s is now private." % data["client"].world.id)
        else:
            data["client"].world.status["private"] = False
            data["client"].sendWorldMessage("This world is now public.")
            data["client"].sendServerMessage("%s is now public." % data["client"].world.id)
        data["client"].world.status["modified"] = True

    @config("category", "world")
    @config("rank", "op")
    @on_off_command
    @config("disabled-on", ["cmdblock", "irc"])
    def commandLock(self, data):
        "/lock on|off - Op\nEnables or disables the world lock."
        if data["onoff"] == "on":
            data["client"].world.status["all_build"] = False
            data["client"].sendWorldMessage("This world is now locked.")
            data["client"].sendServerMessage("Locked %s." % data["client"].world.id)
        else:
            data["client"].world.status["all_build"] = True
            data["client"].sendWorldMessage("This world is now unlocked.")
            data["client"].sendServerMessage("Unlocked %s." % data["client"].world.id)
        data["client"].world.status["modified"] = True

        #@config("rank", "op")
        #@on_off_command
        #def commandPOnly(self, onoff, fromloc, rankoverride):
        #"/ponly on/off - Makes the world only accessable by portals."
        #if data["onoff"] == "on":
        #data["client"].world.portal_only = True
        #data["client"].sendWorldMessage("This world is now portal only.")
        #data["client"].sendServerMessage("%s is now only accessable through portals." % data["client"].world.id)
        #else:
        #data["client"].world.portal_only = False
        #elf.client.sendWorldMessage("This world is now accesable through commands.")
        #data["client"].sendServerMessage("%s is now accessable through commands." % data["client"].world.id)
        #data["client"].world.status["modified"] = True

    @config("category", "world")
    @config("rank", "mod")
    @on_off_command
    def commandAutoShutdown(self, data):
        "/asd on|off - World Owner\nAliases: autoshutdown\nEnable or disable autoshutdown in this world."
        if data["onoff"] == "on":
            data["client"].world.status["autoshutdown"] = True
            data["client"].sendServerMessage("Enabled ASD on %s." % data["client"].world.id)
        else:
            data["client"].world.status["autoshutdown"] = False
            data["client"].sendServerMessage("Enabled ASD on %s." % data["client"].world.id)
        data["client"].world.status["modified"] = True

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "worldname templatename")
    @config("aliases", ["mapadd", "worldadd"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandNew(self, data):
        "Makes a new world, and boots it."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a new worldname.")
            return
        if self.factory.world_exists(data["parts"][1]):
            data["client"].sendServerMessage("World name in use.")
            return
        if len(data["parts"]) == 2:
            data["client"].sendServerMessage("Please specify a template.")
            return
        else:
            template = data["parts"][2]
        world_id = data["parts"][1].lower()
        result = self.factory.newWorld(world_id, template)
        if result:
            self.factory.loadWorld("worlds/%s" % world_id, world_id)
            self.factory.worlds[world_id].status["all_build"] = False
            data["client"].sendServerMessage("World '%s' made and booted." % world_id)
        else:
            data["client"].sendServerMessage("Template %s doesn't exist." % parts[2])

    @config("category", "world")
    @config("rank", "mod")
    @config("usage", "worldname newworldname")
    @config("aliases", ["maprename", "worldrename"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandRename(self, data):
        "Renames a SHUT DOWN world."
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("Please specify two worldnames.")
            return
        old_worldid, new_worldid = data["parts"][1:2]
        if old_worldid in self.factory.worlds:
            data["client"].sendServerMessage("World '%s' is booted, please shut it down first." % old_worldid)
        elif not self.factory.world_exists(old_worldid):
            data["client"].sendServerMessage("World '%s' doesn't exist." % old_worldid)
        elif self.factory.world_exists(new_worldid):
            data["client"].sendServerMessage("There is already a world called '%s'." % new_worldid)
        else:
            self.factory.renameWorld(old_worldid, new_worldid)
            data["client"].sendServerMessage("World '%s' renamed to '%s'." % (old_worldid, new_worldid))

    @config("category", "world")
    @config("rank", "mod")
    @config("usage", "worldname")
    def commandShutdown(self, data):
        "Turns off the named world."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        if data["parts"][1] in self.factory.worlds:
            self.factory.unloadWorld(data["parts"][1])
            data["client"].sendServerMessage("World '%s' unloaded." % parts[1])
        else:
            data["client"].sendServerMessage("World '%s' doesn't exist." % parts[1])

    @config("category", "world")
    @config("rank", "mod")
    @config("aliases", ["reload"])
    @config("usage", "worldname")
    def commandReboot(self, data):
        "Reboots a world."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        if data["parts"][1] in self.factory.worlds:
            self.factory.rebootWorld(data["parts"][1])
            data["client"].sendServerMessage("World %s rebooted." % data["parts"][1])
        else:
            data["client"].sendServerMessage("World '%s' isn't booted." % data["parts"][1])

    @config("category", "world")
    @config("rank", "mod")
    @config("usage", "worldname")
    def commandBoot(self, data):
        "Starts up a new world."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        if data["parts"][1] in self.factory.worlds:
            data["client"].sendServerMessage("World '%s' already booted." % data["parts"][1])
        elif not os.path.exists("worlds/%s" % data["parts"][1]):
            data["client"].sendServerMessage("There is no world by that name.")
            return
        else:
            try:
                self.factory.loadWorld("worlds/%s" % data["parts"][1], data["parts"][1])
            except AssertionError:
                data["client"].sendServerMessage("World files missing, the world cannot be loaded.")
            else:
                data["client"].sendServerMessage("World '%s' booted." % data["parts"][1])

    @config("category", "world")
    @config("usage", "[search term|all] [pagenum]")
    @config("aliases", ["maps"])
    def commandWorlds(self, data):
        "Lists available worlds - by search term, online, or all."
        if len(data["parts"]) < 2:
            data["client"].sendNormalMessage("Do /worlds all for all worlds or choose a search term.")
            data["client"].sendServerList(["Online:"] + [id for id, world in self.factory.worlds.items() if data["client"].canEnter(world)], plain=True)
            return
        worldlist = os.listdir("worlds/")
        newworldlist = []
        hidden = 0
        for world in worldlist:
            if (not world.startswith(".")) or data["client"].isHelper(): # World hidden, showing them to helper+ only
                newworldlist.append(world)
            else:
                hidden += 1
        if data["parts"][1] == "all":
            if len(newworldlist) <= 20:
                done = newworldlist
                if len(done) > 0:
                    data["client"].sendServerMessage("Showing %s worlds:" % len(done))
                    data["client"].sendServerList(done, plain=True)
                else:
                    data["client"].sendServerMessage("There are no worlds to list.")
                return
            done = []
            alldone = []
            for element in newworldlist:
                done.append(element)
                if len(done) == 20:
                    alldone.append(done)
                    done = []
            if len(done) > 0:
                alldone.append(done)
            pages = len(alldone)
            if len(parts) < 3:
                data["client"].sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)." % (pages, hidden))
                data["client"].sendServerMessage("Syntax: /worlds all pagenumber")
                return
            data["client"].sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)." % (pages, hidden))
            index = data["parts"][2]
            try:
                index = int(index)
            except:
                data["client"].sendServerMessage("The page number must be an integer!")
            else:
                if index > pages:
                    data["client"].sendServerMessage("Please specify a page number, from 1 to %s." % pages)
                    return
                i = index - 1
                page = alldone[i]
                data["client"].sendServerMessage("Listing page %s of all worlds:" % index)
                data["client"].sendServerList(page, plain=True)
            return
        # World name search
        letter = data["parts"][1].lower()
        newlist = []
        for world in newworldlist:
            if world.lower().startswith(letter):
                newlist.append(world.replace(letter, "%s%s%s" % (COLOUR_RED, letter, COLOUR_WHITE)))
            elif letter in world.lower():
                newlist.append(world.replace(letter, "%s%s%s" % (COLOUR_RED, letter, COLOUR_WHITE)))
        if len(newlist) <= 20:
            done = newlist
            if len(done) > 0:
                data["client"].sendServerMessage("Showing %s worlds containing %s:" % (len(done), letter))
                data["client"].sendServerList(done, plain=True)
            else:
                data["client"].sendServerMessage("No worlds starting with %s." % letter)
        done = []
        alldone = []
        for element in newlist:
            done.append(element)
            if len(done) == 20:
                alldone.append(done)
                done = []
        if len(done) > 0:
            alldone.append(done)
        pages = len(alldone)
        if len(parts) < 3:
            data["client"].sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)" % (pages, hidden))
            data["client"].sendServerMessage("containing %s." % letter)
            data["client"].sendServerMessage("Syntax: /worlds letter pagenumber")
            return
        data["client"].sendServerMessage(
            "There are %s pages of worlds (excluding %s hidden worlds)" % (pages, hidden))
        data["client"].sendServerMessage("containing %s." % letter)
        index = data["parts"][2]
        try:
            index = int(index)
        except:
            data["client"].sendServerMessage("The page number must be an integer!")
        else:
            if index > pages:
                data["client"].sendServerMessage("Please specify a page number, from 1 to %s." % pages)
                return
            i = index - 1
            page = alldone[i]
            data["client"].sendServerMessage("Listing page %s of worlds containing %s:" % (index, letter))
            data["client"].sendServerList(page, plain=True)

    @config("category", "world")
    def commandTemplates(self, data):
        "Lists available templates"
        data["client"].sendServerList(["Templates:"] + os.listdir("arc/templates/"))

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "worldname width height length")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandCreate(self, data):
        "Creates a new world with specified dimensions."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a world name.")
        elif self.factory.world_exists(data["parts"][1]):
            data["client"].sendServerMessage("World name in use.")
        elif len(data["parts"]) < 5:
            data["client"].sendServerMessage("Please specify dimensions. (width, length, height)")
        elif int(data["parts"][2]) < 16 or int(data["parts"][3]) < 16 or int(data["parts"][4]) < 16:
            data["client"].sendServerMessage("No dimension may be smaller than 16.")
        elif int(data["parts"][2]) > 1024 or int(data["parts"][3]) > 1024 or int(data["parts"][4]) > 1024:
            data["client"].sendServerMessage("No dimension may be greater than 1024.")
        elif (int(data["parts"][2]) % 16) > 0 or (int(data["parts"][3]) % 16) > 0 or (int(data["parts"][4]) % 16) > 0:
            data["client"].sendServerMessage("All dimensions must be divisible by 16.")
        else:
            world_id = data["parts"][1].lower()
            sx, sy, sz = [int(i) for i in data["parts"][2:4]]
            grass_to = (sy // 2)
            world = World.create(
                "worlds/%s" % world_id,
                sx, sy, sz, # Size
                sx // 2, grass_to + 2, sz // 2, 0, # Spawn
                ([BLOCK_DIRT] * (grass_to - 1) + [BLOCK_GRASS] + [BLOCK_AIR] * (sy - grass_to)) # Levels
            )
            self.factory.loadWorld("worlds/%s" % world_id, world_id)
            self.factory.worlds[world_id].status["all_build"] = False
            data["client"].sendServerMessage("World '%s' made and booted." % world_id)

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "worldname")
    @config("aliases", ["mapdelete"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandDelete(self, data):
        "Sets the specified world to 'ignored'."
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        if not os.path.exists("worlds/%s" % data["parts"][1]):
            data["client"].sendServerMessage("World %s doesn't exist." % (data["parts"][1]))
            return
        if data["parts"][1] in self.factory.worlds:
            self.factory.unloadWorld(data["parts"][1])
        name = data["parts"][1]
        extra = "_0"
        if os.path.exists("worlds/.trash/%s" % name):
            def doRename():
                if os.path.exists("worlds/.trash/%s" % (name + extra)):
                    extra = "_" + str(int(extra[1:]) + 1)
                    reactor.callLater(0.1, doRename)
                else:
                    name = name + extra
            doRename()
        shutil.copytree("worlds/%s" % data["parts"][1], "worlds/.trash/%s" % (name))
        shutil.rmtree("worlds/%s" % data["parts"][1])
        data["client"].sendServerMessage("World deleted as %s." % (name))

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "worldname")
    @config("disabled-on", ["cmdblock", "irc"])
    def commandUnDelete(self, data):
        "Restores a deleted world."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Please specify a worldname.")
            return
        name = data["parts"][1]
        world_dir = ("worlds/.trash/%s/" % name)
        if not os.path.exists(world_dir):
            data["client"].sendServerMessage("World %s is not in the world trash bin." % name)
            return
        extra = "_0"
        if os.path.exists("worlds/%s/" % (name)):
            def doRename():
                if os.path.exists("worlds/%s/" % (name + extra)):
                    extra = "_" + str(int(extra[1:]) + 1)
                    reactor.callLater(0.1, doRename)
                else:
                    name = name + extra
            doRename()
        path = ("worlds/%s/" % name)
        shutil.move(world_dir, path)
        data["client"].sendServerMessage("World restored as %s." % name)

    @config("category", "world")
    @config("rank", "admin")
    @config("usage", "[letter]")
    def commandDeleted(self, data):
        "Lists deleted worlds - by letter or all."
        if len(data["parts"]) != 2 and len(data["parts"]) != 3:
            data["client"].sendServerMessage("Do '/deleted letter' for all starting with a letter.")
            data["client"].sendServerList(["Deleted:"] + os.listdir("worlds/.trash/"))
            return
        if len(data["parts"][1]) != 1:
            data["client"].sendServerMessage("Only specify one starting letter per entry, not multiple")
            return
        if len(data["parts"]) == 3:
            if len(data["parts"][2]) != 1:
                data["client"].sendServerMessage("Only specify one starting letter per entry, not multiple")
                return
        letter1 = ord(data["parts"][1].lower())
        if len(data["parts"]) == 3:
            letter2 = ord(data["parts"][2].lower())
        else:
            letter2 = letter1
        if letter1 > letter2:
            a = letter1
            letter1 = letter2
            letter2 = a
        worldlist = os.listdir("worlds/.trash/")
        newlist = []
        for world in worldlist:
            if letter1 <= ord(world[0]) <= letter2:
                newlist.append(world)
        data["client"].sendServerList(["Deleted:"] + newlist)

    @config("category", "world")
    @config("usage", "worldname[/backupname]")
    @config("aliases", ["j", "join", "load", "map"])
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandLoad(self, data):
        "Moves you into world 'worldname'"
        world_id = data["parts"][1].replace("/", "/backup/")
        if world_id not in self.factory.worlds:
            data["client"].sendServerMessage("Attempting to boot and join '%s'" % world_id)
            if not os.path.exists("worlds/%s" % world_id):
                data["client"].sendServerMessage("There is no world by that name.")
                return
            try:
                self.factory.loadWorld("worlds/%s" % world_id, world_id)
            except AssertionError as e:
                data["client"].sendServerMessage("That world is broken. Please report!")
                data["client"].logger.error("World %s is broken!" % world_id)
                data["client"].logger.error("Error: %s" % e)
                try:
                    data["client"].logger.debug("File: %s" % inspect.getfile(self))
                except:
                    pass
                return
        try:
            world = self.factory.worlds[world_id]
        except KeyError:
            data["client"].sendServerMessage("There is no world by that name.")
        else:
            if not data["client"].canEnter(world):
                if world.status["private"]:
                    data["client"].sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                    return
                else:
                    data["client"].sendServerMessage("You're WorldBanned from '%s', you're not allowed in." % world_id)
                    return
            data["client"].changeToWorld(world_id)

    @config("category", "world")
    @config("rank", "mod")
    @config("usage", "worldname newworldname removebackup")
    @config("aliases", ["cw"])
    @config("disabled-on", ["cmdblock", "irc"])
    def commandCopyWorld(self, data):
        "Copies a SHUT DOWN world.\nSpecify True for removebackup to remove all backups in the new world."
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("Please specify two worldnames.")
            return
        old_worldid = data["parts"][1].lower()
        copied_worldid = data["parts"][2].lower()
        if len(data["parts"]) == 4:
            if data["parts"][3].lower() == "true":
                rmbackup = True
            else:
                rmbackup = False
        else:
            rmbackup = True
        if old_worldid in self.factory.worlds:
            data["client"].sendServerMessage("World '%s' is booted, please shut it down!" % old_worldid)
        elif not self.factory.world_exists(old_worldid):
            data["client"].sendServerMessage("World '%s' doesn't exist." % old_worldid)
        elif self.factory.world_exists(copied_worldid):
            data["client"].sendServerMessage("There is already a world called '%s'." % copied_worldid)
        else:
            os.mkdir("worlds/%s/" % copied_worldid)
            shutil.copytree(("worlds/%s" % old_worldid), ("worlds/%" % copied_worldid))
            if rmbackup: shutil.rmtree("worlds/%/backup" % copied_worldid)
            data["client"].sendServerMessage("World '%s' copied to '%s'." % (old_worldid, copied_worldid))

    def commandHome(self, data):
        "Takes you home, where else?"
        data["client"].changeToWorld("default")

    @config("category", "info")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandOps(self, data):
        "/ops - Guest\nLists this world's ops"
        if not data["client"].world.ops:
            data["client"].sendServerMessage("This world has no ops.")
        else:
            data["client"].sendServerList(["Ops for %s:" % data["client"].world.id] + list(data["client"].world.ops))

    @config("category", "info")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandBuilders(self, data):
        "/builders - Guest\nAliases: writers\nLists this world's builders."
        if not data["client"].world.builders:
            data["client"].sendServerMessage("This world has no builders.")
        else:
            data["client"].sendServerList(["Builders for %s:" % data["client"].world.id] + list(data["client"].world.builders))

    @config("category", "info")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandWorldStaff(self, data):
        "/worldstaff - Guest\nLists this world's builders, ops and the world owner."
        data["client"].sendServerMessage("The Staff of %s:" % (data["client"].world.id))
        data["client"].sendServerMessage("World Owner: %s" % data["client"].world.status["owner"])
        if data["client"].world.ops:
            data["client"].sendServerList(["Ops:"] + list(data["client"].world.ops))
        if data["client"].world.builders:
            data["client"].sendServerList(["Builders:"] + list(data["client"].world.builders))

    @config("category", "info")
    @config("aliases", ["mapinfo"])
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandStatus(self, data):
        "Returns info about the current world."
        data["client"].sendServerMessage("%s (%sx%sx%s)" % 
                    (data["client"].world.id, data["client"].world.x, data["client"].world.y, data["client"].world.z))
        if not data["client"].world.status["owner"].lower() == "n/a":
            data["client"].sendServerMessage("Owner: %s" % (data["client"].world.status["owner"]))
        data["client"].sendNormalMessage(
            (data["client"].world.status["all_build"] and "&4Unlocked" or "&2Locked") + " " +\
            (data["client"].world.status["zoned"] and "&2Zones" or "&4Zones") + " " +\
            (data["client"].world.status["private"] and "&2Private" or "&4Private") + " " +\
            (data["client"].world.status["physics"] and "&2Physics" or "&4Physics") + " " +\
            (data["client"].world.status["finite_water"] and "&4FWater" or "&2FWater")
        )
        if data["client"].world.ops:
            data["client"].sendServerList(["Ops:"] + list(data["client"].world.ops))
        if data["client"].world.builders:
            data["client"].sendServerList(["Builders:"] + list(data["client"].world.builders))

    @config("category", "world")
    @config("rank", "op")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandSetspawn(self, data):
        "/setspawn - Op\nSets this world's spawn point to the current location."
        x, y, z, h = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5, int(data["client"].h * (360 / 255.0))
        data["client"].world.spawn = (x, y, z, h)
        data["client"].sendServerMessage("Set spawn point to %s, %s, %s" % (x, y, z))

    @config("category", "info")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandWhere(self, data):
        "/where - Guest\nReturns your current coordinates."
        x, y, z, h, p = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5, data["client"].h, data["client"].p
        data["client"].sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))

    @config("category", "world")
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandRandom(self, data):
        "Takes you to a random world."
        # Get all public worlds
        target_worlds = list(self.factory.publicWorlds())
        # Try excluding us (we may not be public)
        try:
            target_worlds.remove(data["client"].world.id)
        except ValueError:
            pass
        # Anything left?
        if not target_worlds:
            data["client"].sendServerMessage("There is only one world, and you're in it.")
        else:
            data["client"].changeToWorld(random.choice(target_worlds))

serverPlugin = WorldUtilPlugin