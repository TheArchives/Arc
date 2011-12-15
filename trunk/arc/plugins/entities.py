# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os, traceback, math
from time import time
from random import randint

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

initfile = open("arc/entities/__init__.py")
exec initfile
initfile.close()
initfile = None
entitycodedict = {}
entityselectdict = {}
entitycreatedict = {}
validentities = []
maxentitiesperworld = 40

def loadentities():
    global validentities
    datafilelist = os.listdir("arc/entities/")
    del datafilelist[datafilelist.index("__init__.py")]
    listofentityfiles = []
    for entry in datafilelist:
        if entry.find('_') == -1 and entry.endswith('.py'):
            listofentityfiles.append(entry)
    for entry in listofentityfiles:
        entitycodedict[entry[:-3]] = open("arc/entities/%s" % entry)
    validentities = entitycodedict.keys()
    for entry in validentities:
        possibeAliasFile = entry + "_aliases.txt"
        if possibeAliasFile in datafilelist:
            for alias in open("arc/entities/%s" % possibeAliasFile):
                alias = alias.rstrip()
                if alias != '':
                    entitycodedict[alias] = entitycodedict[entry]
    validentities = []
    for entityname in entitycodedict:
        if entityname not in unselectableentities:
            validentities.append(entityname)
    for entry in validentities:
        possibeSelectFile = entry + "_select.py"
        if possibeSelectFile in datafilelist:
            entityselectdict[entry] = open("arc/entities/%s" % possibeSelectFile)

        possibeCreateFile = entry + "_create.py"
        if possibeCreateFile in datafilelist:
            entitycreatedict[entry] = open("arc/entities/%s" % possibeCreateFile)

loadentities()
for validentity in validentities:
    if validentity not in entityblocklist:
        entityblocklist[validentity] = [(0, 0, 0)]

class EntityPlugin(ProtocolPlugin):
    commands = {
        "entity": "commandEntity",
        "entityclear": "commandEntityclear",
        "numentities": "commandNumentities",
        "entities": "commandEntities",
        "mob": "commandEntity",
        "mobclear": "commandEntityclear",
        "nummobs": "commandNumentities",
        "mobs": "commandEntities",
        "item": "commandEntity",
        "itemclear": "commandEntityclear",
        "numitems": "commandNumentities",
        "items": "commandEntities",
        }

    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
        }

    def gotClient(self):
        self.var_entityselected = "None"
        self.var_entityparts = []

    def newWorld(self, world):
        "Hook to reset entity making in new worlds."
        self.var_entityselected = "None"

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if fromloc != "user":
            # People shouldn't be blbing mobs
            return
        world = self.client.world
        try:
            px, py, pz, ph, pp = self.client.x >> 5, self.client.y >> 5, self.client.z >> 5, self.client.h, self.client.p
        except:
            pass
        world.entities_worldblockchangesdict[self.client] = (
        (x, y, z, time(), selected_block, block), (px, py, pz, ph, pp))
        entitylist = world.entitylist
        dellist = []
        for index in range(len(entitylist)):
            entity = entitylist[index]
            identity = entity[0]
            i, j, k = entity[1]
            if (i, j, k) == (x, y, z) or (identity in twoblockhighentities and (i, j + 1, k) == (x, y, z)):
                dellist.append(index)
        dellist.reverse()
        for index in dellist:
            del entitylist[index]
            self.client.sendServerMessage("The entity is now deleted.")
        if block != 0:
            if self.var_entityselected != "None":
                if len(entitylist) >= maxentitiesperworld:
                    self.client.sendServerMessage("Max entities per world exceeded.")
                    return
                if self.var_entityselected in entitycreatedict:
                    exec entitycreatedict[self.var_entityselected]
                    entitycreatedict[self.var_entityselected].seek(0)
                else:
                    entitylist.append([self.var_entityselected, (x, y, z), 8, 8])
                    self.client.sendServerMessage("The entity was created.")

    def posChanged(self, x, y, z, h, p):
        username = self.client.username
        world = self.client.world
        try:
            keyuser = world.var_entities_keyuser
        except:
            world.var_entities_keyuser = username
            keyuser = username
        clients = world.clients
        worldusernamelist = []
        for client in clients:
            worldusernamelist.append(client.username)
        if not keyuser in worldusernamelist:
            world.var_entities_keyuser = username
            keyuser = username
        if username == keyuser:
            entitylist = world.entitylist
            worldblockchangesdict = world.entities_worldblockchangesdict
            entities_childerenlist = world.entities_childerenlist
            worldblockchangedellist = []
            var_dellist = []
            var_abstime = time()
            userpositionlist = []
            for user in clients:
                userpositionlist.append((user, (self.client.x >> 5, self.client.y >> 5, self.client.z >> 5)))
            var_num = len(entitylist)
            if var_num > maxentitiystepsatonetime:
                var_num = maxentitiystepsatonetime
            for index in range(var_num):
                entity = entitylist[index]
                var_type = entity[0]
                var_position = entity[1]
                entity[2] -= 1
                if entity[2] < 0:
                    try:
                        entity[2] = entity[3]
                        x, y, z = var_position
                        if not (0 <= x < world.x and 0 <= y < world.y and 0 <= z < world.z):
                            var_dellist.append(index)
                            if var_type in var_childrenentities:
                                del entities_childerenlist[entities_childerenlist.index(entity[5])]
                        elif (
                             var_type in twoblockhighentities or var_type == "spawner" or var_type in twoblockhighshootingentities) and not (
                        0 <= x < world.x and 0 <= y + 1 < world.y and 0 <= z < world.z):
                            var_dellist.append(index)
                        elif var_type == "cannon":
                            # these variables also used later
                            var_orientation = entity[5]
                            x, y, z = var_position
                            if var_orientation == 0:
                                var_sensorblocksoffsets = ((0, 1, -2), (0, 2, -2))
                                var_loadblockoffset = (0, 0, -1)
                            elif var_orientation == 1:
                                var_sensorblocksoffsets = ((2, 1, 0), (2, 2, 0))
                                var_loadblockoffset = (1, 0, 0)
                            elif var_orientation == 2:
                                var_sensorblocksoffsets = ((0, 1, 2), (0, 2, 2))
                                var_loadblockoffset = (0, 0, 1)
                            elif var_orientation == 3:
                                var_sensorblocksoffsets = ((-2, 1, 0), (-2, 2, 0))
                                var_loadblockoffset = (-1, 0, 0)
                            n, m, o = var_loadblockoffset
                            if not (0 <= x + n < world.x and 0 <= y + m < world.y and 0 <= z + o < world.z):
                                var_dellist.append(index)
                            else:
                                for q, r, s in var_sensorblocksoffsets:
                                    if not (0 <= x + q < world.x and 0 <= y + r < world.y and 0 <= z + s < world.z):
                                        var_dellist.append(index)
                        if index not in var_dellist:
                            if var_type in entitycodedict:
                                exec entitycodedict[var_type]
                                entitycodedict[var_type].seek(0)
                            else:
                                self.client.sendWorldMessage("UNKOWN ENTITY IN WORLD - FIX THIS!")
                    except:
                        self.client.sendPlainWorldMessage(
                            traceback.format_exc().replace("Traceback (most recent call last):", ""))
                        self.client.sendPlainWorldMessage(
                            "Internal Server Error - Traceback (Please report this to the Server Staff or the Arc Team, see /about for contact info)")
                        self.client.logger.error(traceback.format_exc())
                        world.entitylist = []
                        return
                entity[1] = var_position
            var_dellist2 = []
            for index in var_dellist:
                if index not in var_dellist2:
                    var_dellist2.append(index)
            var_dellist2.sort()
            var_dellist2.reverse()
            for index in var_dellist2:
                del entitylist[index]
            worldblockchangedellist2 = []
            for index in worldblockchangedellist:
                if index not in worldblockchangedellist2:
                    worldblockchangedellist2.append(index)
            for index in worldblockchangedellist2:
                del worldblockchangesdict[index]
            if len(entitylist) > maxentitiystepsatonetime:
                for i in range(maxentitiystepsatonetime):
                    entitylist.append(entitylist.pop(0))

    @config("rank", "op")
    def commandEntity(self, parts, fromloc, overriderank):
        "/entity entityname - Op\nAliases: item, mob\nCreates the specified entity."
        if len(parts) < 2:
            if self.var_entityselected == "None":
                self.client.sendServerMessage("Please enter an entity name (type /entities for a list)")
            else:
                self.var_entityselected = "None"
                self.client.sendServerMessage("The entity has been deselected.")
        else:
            world = self.client.world
            entity = parts[1]
            var_continue = True
            if entity in validentities:
                if entity in entityselectdict:
                    exec entityselectdict[entity]
                    entityselectdict[entity].seek(0)
                else:
                    self.var_entityselected = entity
            else:
                self.client.sendServerMessage("%s is not a valid entity." % entity)
                return
            if var_continue:
                self.client.sendServerMessage("The entity %s has been selected." % entity)
                self.client.sendServerMessage("To deselect just type /entity")

    @config("rank", "op")
    def commandNumentities(self, parts, fromloc, overriderank):
        "/numentities - Op\nAliases: numitems, nummobs\nTells you the number of entities in the world."
        world = self.client.world
        entitylist = world.entitylist
        self.client.sendServerMessage(str(len(entitylist)))

    @config("rank", "op")
    def commandEntityclear(self, parts, fromloc, overriderank):
        "/entityclear - Op\nAliases: itemclear, mobclear\nClears the entities from the world."
        world = self.client.world
        for entity in self.client.world.entitylist:
            var_id = entity[0]
            x, y, z = entity[1]
            if var_id in entityblocklist:
                for offset in entityblocklist[var_id]:
                    ox, oy, oz = offset
                    rx, ry, rz = x + ox, y + oy, z + oz
                    block = '\x00'
                    world[rx, ry, rz] = block
                    self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
                    self.client.sendBlock(rx, ry, rz, block)
            elif var_id == "cannon":
                var_orientation = entity[5]
                if var_orientation == 0:
                    var_sensorblocksoffsets = ((0, 1, -2), (0, 2, -2))
                    var_loadblockoffset = (0, 0, -1)
                elif var_orientation == 1:
                    var_sensorblocksoffsets = ((2, 1, 0), (2, 2, 0))
                    var_loadblockoffset = (1, 0, 0)
                elif var_orientation == 2:
                    var_sensorblocksoffsets = ((0, 1, 2), (0, 2, 2))
                    var_loadblockoffset = (0, 0, 1)
                elif var_orientation == 3:
                    var_sensorblocksoffsets = ((-2, 1, 0), (-2, 2, 0))
                    var_loadblockoffset = (-1, 0, 0)
                block = '\x00'
                world[x, y, z] = block
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                self.client.sendBlock(x, y, z, block)
                i, j, k = var_loadblockoffset
                rx, ry, rz = x + i, y + j, z + k
                world[rx, ry, rz] = block
                self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
                self.client.sendBlock(rx, ry, rz, block)
                for i, j, k in var_sensorblocksoffsets:
                    rx, ry, rz = x + i, y + j, z + k
                    world[rx, ry, rz] = block
                    self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
                    self.client.sendBlock(rx, ry, rz, block)
            else:
                self.client.sendServerMessage("Entity not registered in the entityblocklist.")
        self.client.world.entitylist = []
        self.client.sendWorldMessage("The entities have been cleared.")

    @config("rank", "op")
    def commandEntities(self, parts, fromloc, overriderank):
        "/entities - Op\nAliases: items, mobs\nDisplays available entities."
        varsorted_validentities = validentities[:]
        varsorted_validentities.sort()
        self.client.sendServerList(["Available entities:"] + varsorted_validentities)
