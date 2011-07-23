# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os, shutil

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin
from arc.world import World

class WorldUtilPlugin(ProtocolPlugin):

    commands = {
        "backup": "commandBackup",
        "backups": "commandBackups",
        "restore": "commandRestore",

        "physics": "commandPhysics",
        "physflush": "commandPhysflush",
        "unflood": "commandUnflood",
        "deflood": "commandUnflood",
        "fwater": "commandFwater",

        "private": "commandPrivate",
        "lock": "commandLock",
        #"ponly": "commandPOnly"

        "new": "commandNew",
        "mapadd": "commandNew",
        "rename": "commandRename",
        "maprename": "commandRename",
        "shutdown": "commandShutdown",
        "boot": "commandBoot",
        "reboot": "commandReboot",
        "reload": "commandReboot",
        "create": "commandCreate",
        "delete": "commandDelete",
        "mapdelete": "commandDelete",
        "undelete": "commandUnDelete",
        "deleted": "commandDeleted",

        "worlds": "commandWorlds",
        "maps": "commandWorlds",

        "templates": "commandTemplates",

        "l": "commandLoad",
        "j": "commandLoad",
        "load": "commandLoad",
        "join": "commandLoad",
        "map": "commandLoad",

        "home": "commandHome",

        "status": "commandStatus",
        "mapinfo": "commandStatus",
        "setspawn": "commandSetspawn",
        "setowner": "commandSetOwner",
        "worldowner": "commandSetOwner",
        "worldstaff": "commandWorldStaff",
        "where": "commandWhere",
        "ops": "commandOps",
        "writers": "commandBuilders",
        "builders": "commandBuilders",
    }

    @config("category", "world")
    @config("rank", "op")
    def commandBackup(self, parts, fromloc, overriderank):
        "/backup worldname - Op\nMakes a backup copy of the world."
        if len(parts) == 1:
            parts.append(self.client.world.basename.lstrip("worlds"))
        world_id = parts[1]
        world_dir = ("worlds/%s/" % world_id)
        if not os.path.exists(world_dir):
           self.client.sendServerMessage("World %s does not exist." % (world_id))
        else:
            if not os.path.exists(world_dir+"backup/"):
                os.mkdir(world_dir+"backup/")
            folders = os.listdir(world_dir+"backup/")
            if len(parts) > 2:
                path = os.path.join(world_dir+"backup/", parts[2])
                if os.path.exists(path):
                    self.client.sendServerMessage("Backup %s already exists. Pick a different name." % parts[2])
                    return
            else:
                backups = list([])
                for x in folders:
                    if x.isdigit():
                        backups.append(x)
                backups.sort(lambda x, y: int(x) - int(y))
                path = os.path.join(world_dir+"backup/", "0")
                if backups:
                    path = os.path.join(world_dir+"backup/", str(int(backups[-1])+1))
            os.mkdir(path)
            try:
                shutil.copy(world_dir + "blocks.gz", path)
                shutil.copy(world_dir + "world.meta", path)
            except:
                self.client.sendServerMessage("Your backup attempt has went wrong, please try again.")
            if len(parts) > 2:
                self.client.sendServerMessage("Backup %s saved." % parts[2])
            else:
                try:
                    self.client.sendServerMessage("Backup %s saved." % str(int(backups[-1])+1))
                except:
                    self.client.sendServerMessage("Backup 0 saved.")

    @config("category", "world")
    @config("rank", "op")
    def commandRestore(self, parts, fromloc, overriderank):
        "/restore worldname number - Op\nRestore world to indicated number."
        if len(parts) < 2:
            self.client.sendServerMessage("Please specify at least a world ID!")
        else:
            world_id = parts[1].lower()
            world_dir = ("worlds/%s/" % world_id)
            if len(parts) < 3:
                try:
                    backups = os.listdir(world_dir+"backup/")
                except:
                    self.client.sendServerMessage("Syntax: /restore worldname number")
                    return
                backups.sort(lambda x, y: int(x) - int(y))
                backup_number = str(int(backups[-1]))
            else:
                backup_number = parts[2]
            if not os.path.exists(world_dir + "backup/%s/" % backup_number):
                self.client.sendServerMessage("Backup %s does not exist." % backup_number)
            else:
                if not os.path.exists(world_dir + "blocks.gz.new"):
                    shutil.copy((world_dir + "backup/%s/blocks.gz" % backup_number), world_dir)
                    if os.path.exists(world_dir + "backup/%s/world.meta" % backup_number):
                        shutil.copy((world_dir + "backup/%s/world.meta" % backup_number), world_dir)
                else:
                    reactor.callLater(1, self.commandRestore(self, parts, fromloc, overriderank))
                default_name = self.client.factory.default_name
                self.client.factory.unloadWorld("worlds/%s" % world_id, world_id)
                self.client.sendServerMessage("%s has been restored to %s and booted." % (world_id, backup_number))
                for client in self.client.factory.worlds[world_id].clients:
                    client.changeToWorld(world_id)

    @config("category", "world")
    def commandBackups(self, parts, fromloc, overriderank):
        "/backups - Guest\nLists all backups this world has."
        try:
            world_dir = ("worlds/%s/" % self.client.world.id)
            folders = os.listdir(world_dir+"backup/")
            Num_backups = list([])
            Name_backups = list([])
            for x in folders:
                if x.isdigit():
                    Num_backups.append(x)
                else:
                    Name_backups.append(x)
            Num_backups.sort(lambda x, y: int(x) - int(y))
            if Num_backups > 2:
                self.client.sendServerList(["Backups for %s:" % self.client.world.id] + [Num_backups[0] + "-" + Num_backups[-1]] + Name_backups)
            else:
                self.client.sendServerList(["Backups for %s:" % self.client.world.id] + Num_backups + Name_backups)
        except:
            self.client.sendServerMessage("Sorry, but there are no backups for %s." % self.client.world.id)

    @config("category", "world")
    @config("rank", "op")
    def commandUnflood(self, parts, fromloc, overriderank):
        "/unflood worldname - Op\nAliases: deflood\nSlowly removes all water and lava from the world."
        self.client.world.start_unflooding()
        self.client.sendWorldMessage("Unflooding has been initiated.")

    @config("category", "world")
    @config("rank", "admin")
    @on_off_command
    def commandPhysics(self, onoff, fromloc, overriderank):
        "/physics on|off - Admin\nEnables or disables physics in this world."
        if onoff == "on":
            if self.client.world.physics:
                self.client.sendWorldMessage("Physics is already on here.")
            else:
                if self.client.factory.numberWithPhysics() >= self.client.factory.physics_limit:
                    self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.physics_limit)
                else:
                    self.client.world.physics = True
                    self.client.sendWorldMessage("This world now has physics enabled.")
        else:
            if not self.client.world.physics:
                self.client.sendWorldMessage("Physics is already off here.")
            else:
                self.client.world.physics = False
                self.client.sendWorldMessage("This world now has physics disabled.")

    @config("category", "world")
    @config("rank", "op")
    @on_off_command
    def commandFwater(self, onoff, fromloc, overriderank):
        "/fwater on|off - Op\nEnables or disables finite water in this world."
        if onoff == "on":
            self.client.world.finite_water = True
            self.client.sendWorldMessage("This world now has finite water enabled.")
        else:
            self.client.world.finite_water = False
            self.client.sendWorldMessage("This world now has finite water disabled.")

    @config("category", "world")
    @config("rank", "admin")
    def commandPhysflush(self, parts, fromloc, overriderank):
        "/physflush - Admin\nTells the physics engine to rescan the world."
        if self.client.world.physics:
            if self.client.factory.numberWithPhysics() >= self.client.factory.physics_limit:
                self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.physics_limit)
            else:
                self.client.world.physics = False
                self.client.world.physics = True
                self.client.sendWorldMessage("This world now has a physics flush running.")
        else:
            self.client.sendServerMessage("This world does not have physics on.")

    @config("category", "world")
    @config("rank", "op")
    @on_off_command
    def commandPrivate(self, onoff, fromloc, overriderank):
        "/private on|off - Op\nEnables or disables the private status for this world."
        if onoff == "on":
            self.client.world.private = True
            self.client.sendWorldMessage("This world is now private.")
            self.client.sendServerMessage("%s is now private." % self.client.world.id)
        else:
            self.client.world.private = False
            self.client.sendWorldMessage("This world is now public.")
            self.client.sendServerMessage("%s is now public." % self.client.world.id)

    @config("category", "world")
    @config("rank", "op")
    @on_off_command
    def commandLock(self, onoff, fromloc, overriderank):
        "/lock on|off - Op\nEnables or disables the world lock."
        if onoff == "on":
            self.client.world.all_write = False
            self.client.sendWorldMessage("This world is now locked.")
            self.client.sendServerMessage("Locked %s" % self.client.world.id)
        else:
            self.client.world.all_write = True
            self.client.sendWorldMessage("This world is now unlocked.")
            self.client.sendServerMessage("Unlocked %s" % self.client.world.id)

    #@op_only
    #@on_off_command
    #def commandPOnly(self, onoff, fromloc, rankoverride):
        #"/ponly on/off - Makes the world only accessable by portals."
        #if onoff == "on":
            #self.client.world.portal_only = True
            #self.client.sendWorldMessage("This world is now portal only.")
            #self.client.sendServerMessage("%s is now only accessable through portals." % self.client.world.id)
        #else:
            #self.client.world.portal_only = False
            #elf.client.sendWorldMessage("This world is now accesable through commands.")
            #self.client.sendServerMessage("%s is now accessable through commands." % self.client.world.id)

    @config("category", "world")
    @config("rank", "admin")
    def commandNew(self, parts, fromloc, overriderank):
        "/new worldname templatename - Admin\nAliases: mapadd\nMakes a new world, and boots it."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a new worldname.")
        elif self.client.factory.world_exists(parts[1]):
            self.client.sendServerMessage("World name in use.")
        else:
            if len(parts) == 2:
                self.client.sendServerMessage("Please specify a template.")
                return
            elif len(parts) == 3 or len(parts) == 4:
                template = parts[2]
            else:
                self.client.sendServerMessage("Please specify a template.")
                return
            world_id = parts[1].lower()
            result = self.client.factory.newWorld(world_id, template, client=self.client)
            if result:
                self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
                self.client.factory.worlds[world_id].all_write = False
                if len(parts) < 4:
                    self.client.sendServerMessage("World '%s' made and booted." % world_id)

    @config("category", "world")
    @config("rank", "mod")
    def commandRename(self, parts, fromloc, overriderank):
        "/rename worldname newworldname - Mod\nAliases: maprename\nRenames a SHUT DOWN world."
        if len(parts) < 3:
            self.client.sendServerMessage("Please specify two worldnames.")
        else:
            old_worldid = parts[1]
            new_worldid = parts[2]
            if old_worldid in self.client.factory.worlds:
                self.client.sendServerMessage("World '%s' is booted, please shut it down!" % old_worldid)
            elif not self.client.factory.world_exists(old_worldid):
                self.client.sendServerMessage("There is no world '%s'." % old_worldid)
            elif self.client.factory.world_exists(new_worldid):
                self.client.sendServerMessage("There is already a world called '%s'." % new_worldid)
            else:
                self.client.factory.renameWorld(old_worldid, new_worldid)
                self.client.sendServerMessage("World '%s' renamed to '%s'." % (old_worldid, new_worldid))
    
    @config("category", "world")
    @config("rank", "mod")
    def commandShutdown(self, parts, fromloc, overriderank):
        "/shutdown worldname - Mod\nTurns off the named world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a worldname.")
        else:
            if parts[1] in self.client.factory.worlds:
                self.client.factory.unloadWorld(parts[1])
                self.client.sendServerMessage("World '%s' unloaded." % parts[1])
            else:
                self.client.sendServerMessage("World '%s' doesn't exist." % parts[1])

    @config("category", "world")
    @config("rank", "mod")
    def commandReboot(self, parts, fromloc, overriderank):
        "/reboot worldname - Mod\nAliases: reload\nReboots a world"
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a worldname.")
        else:
            if parts[1] in self.client.factory.worlds:
                self.client.factory.rebootWorld(parts[1])
                self.client.sendServerMessage("World %s rebooted" % parts[1])
            else:
                self.client.sendServerMessage("World '%s' isnt booted." % parts[1])

    @config("category", "world")
    @config("rank", "mod")
    def commandBoot(self, parts, fromloc, overriderank):
        "/boot worldname - Mod\nStarts up a new world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a worldname.")
        else:
            if parts[1] in self.client.factory.worlds:
                self.client.sendServerMessage("World '%s' already exists!" % parts[1])
            else:
                try:
                    self.client.factory.loadWorld("worlds/%s" % parts[1], parts[1])
                    self.client.sendServerMessage("World '%s' booted." % parts[1])
                except AssertionError:
                    self.client.sendServerMessage("There is no world by that name.")

    @config("category", "world")
    def commandWorlds(self, parts, fromloc, overriderank):
        "/worlds [search tem|all] [pagenumber] - Guest\nAliases: maps\nLists available worlds - by search term, online, or all."
        if len(parts) < 2:
            self.client.sendNormalMessage("Do /worlds all for all worlds or choose a search term.")
            self.client.sendServerList(["Online:"] + [id for id, world in self.client.factory.worlds.items() if self.client.canEnter(world)], plain=True)
            return
        else:
            worldlist = os.listdir("worlds/")
            newworldlist = []
            hidden = 0
            for world in worldlist:
                if not world.startswith("."): # Hidden worlds!
                    newworldlist.append(world)
                else:
                    hidden += 1
            if parts[1] == 'all':
                if len(newworldlist) > 20:
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
                        self.client.sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)." % (pages, hidden))
                        self.client.sendServerMessage("Syntax: /worlds all pagenumber")
                        return
                    self.client.sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)." % (pages, hidden))
                    index = parts[2]
                    try:
                        index = int(index)
                    except:
                        self.client.sendServerMessage("The page number must be an integer!")
                    else:
                        if index > pages:
                            self.client.sendServerMessage("Please specify a page number, from 1 to %s." % pages)
                            return
                        i = index - 1
                        page = alldone[i]
                        self.client.sendServerMessage("Listing page %s of all worlds:" % index)
                        self.client.sendServerList(page, plain=True)
                else:
                    done = newworldlist
                    if len(done) > 0:
                        self.client.sendServerMessage("Showing %s worlds:" % len(done))
                        self.client.sendServerList(done, plain=True)
                    else:
                        self.client.sendServerMessage("There are no worlds to list.")
                return
            letter = parts[1].lower()
            newlist = []
            for world in newworldlist:
                if world.lower().startswith(letter):
                    newlist.append(world.replace(letter, "%s%s%s" % (COLOUR_RED, letter, COLOUR_WHITE)))
                elif letter in world.lower():
                    newlist.append(world.replace(letter, "%s%s%s" % (COLOUR_RED, letter, COLOUR_WHITE)))
            if len(newlist) > 20:
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
                    self.client.sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)" % (pages, hidden))
                    self.client.sendServerMessage("containing %s." % letter)
                    self.client.sendServerMessage("Syntax: /worlds letter pagenumber")
                    return
                self.client.sendServerMessage("There are %s pages of worlds (excluding %s hidden worlds)" % (pages, hidden))
                self.client.sendServerMessage("containing %s." % letter)
                index = parts[2]
                try:
                    index = int(index)
                except:
                    self.client.sendServerMessage("The page number must be an integer!")
                else:
                    if index > pages:
                        self.client.sendServerMessage("Please specify a page number, from 1 to %s." % pages)
                        return
                    i = index - 1
                    page = alldone[i]
                    self.client.sendServerMessage("Listing page %s of worlds containing %s:" % (index, letter))
                    self.client.sendServerList(page, plain=True)
            else:
                done = newlist
                if len(done) > 0:
                    self.client.sendServerMessage("Showing %s worlds containing %s:" % (len(done), letter))
                    self.client.sendServerList(done, plain=True)
                else:
                    self.client.sendServerMessage("No worlds starting with %s" % letter)

    @config("category", "world")
    def commandTemplates(self, parts, fromloc, overriderank):
        "/templates - Guest\nLists available templates"
        self.client.sendServerList(["Templates:"] + os.listdir("arc/templates/"))

    @config("category", "world")
    @config("rank", "admin")
    def commandCreate(self, parts, fromloc, overriderank):
        "/create worldname width height length - Admin\nCreates a new world with specified dimensions."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a world name.")
        elif self.client.factory.world_exists(parts[1]):
            self.client.sendServerMessage("World name in use.")
        elif len(parts) < 5:
            self.client.sendServerMessage("Please specify dimensions. (width, length, height)")
        elif int(parts[2]) < 16 or int(parts[3]) < 16 or int(parts[4]) < 16:
            self.client.sendServerMessage("No dimension may be smaller than 16.")
        elif int(parts[2]) > 1024 or int(parts[3]) > 1024 or int(parts[4]) > 1024:
            self.client.sendServerMessage("No dimension may be greater than 1024.")
        elif (int(parts[2]) % 16) > 0 or (int(parts[3]) % 16) > 0 or (int(parts[4]) % 16) > 0:
            self.client.sendServerMessage("All dimensions must be divisible by 16.")
        else:
            world_id = parts[1].lower()
            sx, sy, sz = int(parts[2]), int(parts[3]), int(parts[4])
            grass_to = (sy // 2)
            world = World.create(
                "worlds/%s" % world_id,
                sx, sy, sz, # Size
                sx//2,grass_to+2, sz//2, 0, # Spawn
                ([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
                )
            self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
            self.client.factory.worlds[world_id].all_write = False
            self.client.sendServerMessage("World '%s' made and booted." % world_id)
    
    @config("category", "world")
    @config("rank", "admin")
    def commandDelete(self, parts, fromloc, overriderank):
        "/delete worldname - Admin\nAliases: mapdelete\nSets the specified world to 'ignored'."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a worldname.")
        else:
            if not os.path.exists("worlds/%s" % parts[1]):
                self.client.sendServerMessage("World %s doesn't exist." %(parts[1]))
                return
            if parts[1] in self.client.factory.worlds:
                self.client.factory.unloadWorld(parts[1])
            name = parts[1]
            extra = "_0"
            if os.path.exists("worlds/.trash/%s" %(name)):
                while True:
                    if os.path.exists("worlds/.trash/%s" %(name+extra)):
                        extra = "_" + str(int(extra[1:])+1)
                    else:
                        name = name + extra
                        break
            shutil.copytree("worlds/%s" % parts[1], "worlds/.trash/%s" %(name))
            shutil.rmtree("worlds/%s" % parts[1])
            self.client.sendServerMessage("World deleted as %s." %(name))
    
    @config("category", "world")
    @config("rank", "admin")
    def commandUnDelete(self, parts, fromloc, overriderank):
        "/undelete worldname - Admin\nRestores a deleted world."
        if len(parts) < 2:
            self.client.sendServerMessage("Please specify a worldname.")
            return
        name = parts[1]
        world_dir = ("worlds/.trash/%s/" % name)
        if not os.path.exists(world_dir):
           self.client.sendServerMessage("World %s is not in the world trash bin." % name)
           return
        extra="_0"
        if os.path.exists("worlds/%s/" %(name)):
            while True:
                if os.path.exists("worlds/%s/" %(name+extra)):
                    extra = "_" + str(int(extra[1:])+1)
                else:
                    name = name+extra
                    break
        path = ("worlds/%s/" % name)
        shutil.move(world_dir, path)
        self.client.sendServerMessage("World restored as %s." % name)

    @config("category", "world")
    @config("rank", "admin")
    def commandDeleted(self, parts, fromloc, overriderank):
        "/deleted [letter] - Admin\nLists deleted worlds - by letter or all."
        if len(parts) != 2 and len(parts) != 3:
            self.client.sendServerMessage("Do '/deleted letter' for all starting with a letter.")
            self.client.sendServerList(["Deleted:"] + os.listdir("worlds/.trash/"))
            return
        else:
            if len(parts[1]) != 1:
                self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
                return
            if len(parts)==3:
                if len(parts[2]) != 1:
                    self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
                    return
            letter1 = ord(parts[1].lower())
            if len(parts)==3:
                letter2 = ord(parts[2].lower())
            else:
                letter2 = letter1
            if letter1>letter2:
                a = letter1
                letter1 = letter2
                letter2 = a
            worldlist = os.listdir("worlds/.trash/")
            newlist = []
            for world in worldlist:
                if letter1 <= ord(world[0]) <= letter2 and not world.startswith("."):
                    newlist.append(world)
            self.client.sendServerList(["Deleted:"] + newlist)

    @config("category", "world")
    @only_string_command("world name")
    def commandLoad(self, world_id, fromloc, overriderank, params=None):
        "/l worldname [backup] - Guest\nAliases: j, join, load, map\nMoves you into world 'worldname'"
        world_id = world_id.replace("/", "/backup/")
        if world_id not in self.client.factory.worlds:
            self.client.sendServerMessage("Attempting to boot and join '%s'" % world_id)
            try:
                self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
            except AssertionError:
                self.client.sendServerMessage("There is no world by that name.")
                return
        world = self.client.factory.worlds[world_id]
        if not self.client.canEnter(world):
            if world.private:
                self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                return
            else:
                self.client.sendServerMessage("You're WorldBanned from '%s'; so you're not allowed in." % world_id)
                return
        self.client.changeToWorld(world_id)

    def commandHome(self, parts, fromloc, overriderank):
        "/home - Guest\nTakes you home, where else?"
        self.client.changeToWorld("default")

    @config("category", "player")
    @config("rank", "mod")
    def commandSetOwner(self, parts, fromloc, overriderank):
        "/setowner [username] - Mod\nAliases: worldowner\nSets the world's owner string, or unsets it."
        if len(parts) == 1:
            self.client.world.owner = "N/A"
            self.client.sendServerMessage("The World Owner has been unset.")
        else:
            self.client.world.owner = str(parts[1].lower())
            self.client.sendServerMessage("The World Owner has been set.")

    @config("category", "info")
    def commandOps(self, parts, fromloc, overriderank):
        "/ops - Guest\nLists this world's ops"
        if not self.client.world.ops:
            self.client.sendServerMessage("This world has no Ops.")
        else:
            self.client.sendServerList(["Ops for %s:" % self.client.world.id] + list(self.client.world.ops))

    @config("category", "info")
    def commandBuilders(self, parts, fromloc, overriderank):
        "/builders - Guest\nAliases: writers\nLists this world's builders."
        if not self.client.world.builders:
            self.client.sendServerMessage("This world has no builders.")
        else:
            self.client.sendServerList(["Builders for %s:" % self.client.world.id] + list(self.client.world.builders))
            
    @config("category", "info")
    def commandWorldStaff(self, parts, byuser, rankoverride):
        "/worldstaff - Guest\nLists this world's builders, ops and the world owner.."
        self.client.sendServerMessage("The Staff of %s:" % (self.client.world.id))
        self.client.sendServerMessage("World Owner: %s" % self.client.world.owner)
        if self.client.world.ops:
            self.client.sendServerList(["Ops:"] + list(self.client.world.ops))
        if self.client.world.writers:
            self.client.sendServerList(["Builders:"] + list(self.client.world.writers))

    @config("category", "info")
    def commandStatus(self, parts, fromloc, overriderank):
        "/status - Guest\nAliases: mapinfo\nReturns info about the current world."
        self.client.sendServerMessage("%s (%sx%sx%s)" % (self.client.world.id, self.client.world.x, self.client.world.y, self.client.world.z))
        if not self.client.world.owner == "n/a":
            self.client.sendServerMessage("Owner: %s" % (self.client.world.owner))
        self.client.sendNormalMessage(\
            (self.client.world.all_write and "&4Unlocked" or "&2Locked")+" "+\
            (self.client.world.zoned and "&2Zones" or "&4Zones")+" "+\
            (self.client.world.private and "&2Private" or "&4Private")+" "+\
            (self.client.world.physics and "&2Physics" or "&4Physics")+" "+\
            (self.client.world.finite_water and "&4FWater" or "&2FWater")
        )
        if self.client.world.ops:
            self.client.sendServerList(["Ops:"] + list(self.client.world.ops))
        if self.client.world.builders:
            self.client.sendServerList(["Builders:"] + list(self.client.world.builders))
  
    @config("category", "world")
    @config("rank", "op")
    def commandSetspawn(self, parts, fromloc, overriderank):
        "/setspawn - Op\nSets this world's spawn point to the current location."
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = int(self.client.h * (360/255.0))
        self.client.world.spawn = (x, y, z, h)
        self.client.sendServerMessage("Set spawn point to %s, %s, %s" % (x, y, z))
    
    @config("category", "info")
    def commandWhere(self, parts, fromloc, overriderank):
        "/where - Guest\nReturns your current coordinates."
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = self.client.h
        p = self.client.p
        self.client.sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))