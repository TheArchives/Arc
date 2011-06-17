import random

from core.constants import *
from core.decorators import *
from core.plugins import ProtocolPlugin

# TODO: Dynamic
survivalworldslist = ["survival"]

class SurvivalPlugin(ProtocolPlugin):
    commands = {
        "smelt": "commandSmelt",
        "craft": "commandCraft",
        "give": "commandGive",
        "inventory": "commandInventory",
        "blocktext": "commandBlocktext",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
        "poschange": "posChanged",
    }

    def gotClient(self):
        self.in_survivalworld = False
        self.delay = 5
        self.var_health = 100
        self.var_air = 100
        self.var_fireticker = 0
        self.var_firetimer = 0
        self.var_firetimerswitch = 0
        self.client.var_blocks = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 36: 0, 37: 0, 38: 0, 39: 0, 40: 0, 41: 0, 42: 0, 43: 0, 44: 0, 45: 0, 46: 0, 47: 0, 48: 0, 49: 0}
        self.fallswitch = False
        self.var_yfallenfrom = 0
        self.var_inwaterswitch = False
        self.var_drowntimer = 30
        self.var_deaths = 0
        self.var_showtext = True

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if fromloc != "user":
            return
        if self.in_survivalworld:
            if block == 0:
                world = self.client.world
                try:
                    blockdel = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)])
                    if blockdel != 0:
                        if blockdel == 2:
                            blockdel = 3
                        elif blockdel == 1:
                            blockdel = 4
                        elif blockdel == 18:
                            if random.randint(1,4) == 1:
                                self.client.var_blocks[6] += 1
                                if self.var_showtext:
                                    self.client.sendServerMessage("Collected some %s, total: %s" % (BlockList[6], self.client.var_blocks[6]))
                        self.client.var_blocks[blockdel] += 1
                        if self.var_showtext:
                            self.client.sendServerMessage("Collected some %s, total: %s" % (BlockList[blockdel], self.client.var_blocks[blockdel]))
                except:
                    pass  
            else:
                if block == 7:
                    return block
                if self.client.var_blocks[block] != 0:
                    self.client.var_blocks[block] -= 1
                    if self.var_showtext:
                        self.client.sendServerMessage("You placed some %s, total: %s" % (BlockList[block], self.client.var_blocks[block]))
                    return block
                else:
                    if self.var_showtext:
                        self.client.sendServerMessage("You don't have any %s blocks, earn some." % BlockList[block])
                    return False
    
    def newWorld(self, world):
        "Hook to reset survival switch in new worlds."
        if not world.id in survivalworldslist:
            if self.in_survivalworld:
                self.delay = 5
                self.var_health = 100
                self.var_air = 100
                self.var_fireticker = 0
                self.var_firetimer = 0
                self.var_firetimerswitch = 0
                self.client.var_blocks = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 36: 0, 37: 0, 38: 0, 39: 0, 40: 0, 41: 0, 42: 0, 43: 0, 44: 0, 45: 0, 46: 0, 47: 0, 48: 0, 49: 0}
                self.fallswitch = False
                self.var_yfallenfrom = world.spawn[1]
                self.var_inwaterswitch = False
                self.var_drowntimer = 30
                self.var_deaths = 0
                self.var_showtext = True
                self.client.sendServerMessage("Survival Game Mode Deactivated.")
            self.in_survivalworld = False
        else:
            self.delay = 5
            self.var_health = 100
            self.var_air = 100
            self.var_fireticker = 0
            self.var_firetimer = 0
            self.var_firetimerswitch = 0
            self.client.var_blocks = self.client.var_blocks = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 36: 0, 37: 0, 38: 0, 39: 0, 40: 0, 41: 0, 42: 0, 43: 0, 44: 0, 45: 0, 46: 0, 47: 0, 48: 0, 49: 0}
            self.fallswitch = False
            self.var_yfallenfrom = world.spawn[1]
            self.var_inwaterswitch = False
            self.var_drowntimer = 30
            self.var_deaths = 0
            self.var_showtext = True
            self.in_survivalworld = True
            self.client.sendServerMessage("Survival Game Mode Activated.")
            
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        if self.in_survivalworld:
            world = self.client.world
            i = x >> 5
            j = y >> 5
            k = z >> 5
            if self.delay <= 0:
                self.delay = 5
                try:
                    blockathead = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
                    if blockathead == 10 or blockathead == 11:
                        self.var_fireticker = 10
                        if self.var_firetimerswitch == 0:
                            self.var_firetimer = 20
                            self.var_firetimerswitch = 1
                    if blockathead == 8 or blockathead == 9:
                        self.var_fireticker = 0
                        self.var_inwaterswitch = True
                    else:
                        self.var_inwaterswitch = False
                        self.var_drowntimer = 30
                        self.var_air = 100
                except:
                    pass
                try:
                    blockatfeet = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j-1, k)])
                    if blockatfeet == 10 or blockatfeet == 11:
                        self.var_fireticker = 10
                        if self.var_firetimerswitch == 0:
                            self.var_firetimer = 20
                            self.var_firetimerswitch = 1
                    if blockatfeet == 8 or blockatfeet == 9:
                        self.var_fireticker = 0
                except:
                    pass
                try:
                    blockbelowfeet1 = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j-2, k)])
                    blockbelowfeet2 = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j-3, k)])
                    if (blockbelowfeet1 == 0 or blockbelowfeet1 == 6 or blockbelowfeet1 == 37 or blockbelowfeet1 == 38 or blockbelowfeet1 == 39 or blockbelowfeet1 == 40) and (blockbelowfeet2 == 0 or blockbelowfeet2 == 6 or blockbelowfeet2 == 37 or blockbelowfeet2 == 38 or blockbelowfeet2 == 39 or blockbelowfeet2 == 40):
                        if not self.fallswitch:
                            self.var_yfallenfrom = j
                        self.fallswitch = True
                    else:
                        if self.fallswitch:
                            if blockbelowfeet1 != 8 and blockbelowfeet2 != 8 and blockatfeet != 8 and blockbelowfeet1 != 9 and blockbelowfeet2 != 9 and blockatfeet != 9 and blockbelowfeet1 != 10 and blockbelowfeet2 != 10 and blockatfeet != 10 and blockbelowfeet1 != 11 and blockbelowfeet2 != 11 and blockatfeet != 11:
                                distancefallen = self.var_yfallenfrom - j
                                if distancefallen>6:
                                    self.var_health -= (distancefallen-6)*5
                                    if self.var_health > 0:
                                        self.client.sendServerMessage("FALL DAMAGE! Health: %s" % self.var_health)
                        self.fallswitch = False
                except:
                    pass
            else:
                self.delay -= 1
            if self.var_inwaterswitch:
                if self.var_drowntimer <= 0:
                    self.var_drowntimer = 30
                    if self.var_air == 0:
                        self.var_health -= 10
                        if self.var_health > 0:
                            self.client.sendServerMessage("DROWNING! Health: %s" % self.var_health)
                    else:
                        self.var_air -= 10
                        if self.var_air < 0:
                            self.var_air = 0
                        self.client.sendServerMessage("Air: %s" % self.var_air)
                else:
                    self.var_drowntimer -= 1
            if self.var_firetimer > 0:
                self.var_firetimer -= 1
            if self.var_fireticker>0 and self.var_firetimer <= 0:
                self.var_fireticker -= 1
                self.var_health -= 5
                self.var_firetimer = 20
                self.var_firetimerswitch = 0
                if self.var_health > 0:
                    self.client.sendServerMessage("ON FIRE! Health: %s" % self.var_health)
            if self.var_health <= 0:
                sx, sy, sz, sh = world.spawn
                self.delay = 5
                self.var_health = 100
                self.var_air = 100
                self.var_fireticker = 0
                self.var_firetimer = 0
                self.var_firetimerswitch = 0
                self.fallswitch = False
                self.var_yfallenfrom = sy
                self.var_inwaterswitch = False
                self.var_drowntimer = 30
                self.var_deaths += 1
                self.client.teleportTo(sx,sy,sz,sh)
                self.client.sendPlainWorldMessage("&c%s has died. Deaths this game: %s" % (self.client.username, self.var_deaths))

    def commandSmelt(self, parts, fromloc, overriderank):
        "/smelt blocktype fuelblocktype numbertomake\nSurvival Game Mode Only\nAllows you to create new blocks with smelting"
        if self.in_survivalworld:
            if len(parts) != 4:
                self.client.sendSplitServerMessage("Please enter a block to smelt, a block to burn and how many blocks to try to create.")
            else:
                block = self.client.GetBlockValue(parts[1])
                fuelblock = self.client.GetBlockValue(parts[2])
                if block == None or fuelblock == None:
                    return
                try:
                    numofblockstomake = int(parts[3])
                except:
                    self.client.sendServerMessage("The number of blocks to make must be an integer.")
                    return
                if numofblockstomake <= 0:
                    self.client.sendServerMessage("The number of products to make must be greater than 0.")
                    return
                if fuelblock == 5:
                    blockstoburn = 8
                elif fuelblock == 16:
                    blockstoburn = 1
                elif fuelblock == 17:
                    blockstoburn = 2
                elif fuelblock == 18:
                    blockstoburn = 16
                blockstoburn = numofblockstomake * blockstoburn
                if block == 4:
                    blockstouse = 1
                    blocktomake = 1
                elif block == 12:
                    blockstouse = 1
                    blocktomake = 20
                elif block == 13:
                    blockstouse = 3
                    blocktomake = 45
                elif block == 14:
                    blockstouse = 4
                    blocktomake = 41
                elif block == 15:
                    blockstouse = 4
                    blocktomake = 42
                blockstouse = numofblockstomake * blockstouse
                numofblock = self.client.var_blocks[block]
                numoffuelblock = self.client.var_blocks[fuelblock]
                if blockstouse > numofblock:
                    self.client.sendServerMessage("You do not have enough %s block(s), you need %s." % (BlockList[block], blockstouse))
                    return
                if blockstoburn > numoffuelblock:
                    self.client.sendServerMessage("You do not have enough %s block(s), you need %s." % (BlockList[fuelblock], blockstoburn))
                    return
                self.client.var_blocks[block] -= blockstouse
                self.client.var_blocks[fuelblock] -= blockstoburn
                self.client.var_blocks[blocktomake] += numofblockstomake
                self.client.sendServerMessage("You have smelted %s %s block(s) into" % (blockstouse, BlockList[block]))
                self.client.sendServerMessage("%s %s block(s) and burned %s %s block(s)" % (numofblockstomake, BlockList[blocktomake], blockstoburn, BlockList[fuelblock]))
        else:
            self.client.sendServerMessage("You are not in a Survival Game Mode World!")
            
    def commandCraft(self, parts, fromloc, overriderank):
        "/craft blocktype numbertomake\nSurvival Game Mode Only\nAllows you to create new blocktypes with crafting."
        if self.in_survivalworld:
            if len(parts) != 3:
                self.client.sendSplitServerMessage("Please enter a block to craft with and how many products to try to create.")
            else:
                block = self.client.GetBlockValue(parts[1])
                if block == None:
                    return
                try:
                    numofblockstomake = int(parts[2])
                except:
                    self.client.sendServerMessage("The number of blocks to make must be an integer.")
                    return
                if numofblockstomake <= 0:
                    self.client.sendServerMessage("The number of products to make must be greater than 0.")
                    return
                if block == 17:
                    blockstouse = 1
                    blocktomake = 5
                elif block == 5:
                    blockstouse = 4
                    blocktomake = 47
                elif block == 4:
                    blockstouse = 1
                    blocktomake = 48
                elif block == 48:
                    blockstouse = 5
                    blocktomake = 49
                elif block == 1:
                    blockstouse = 1
                    blocktomake = 44
                elif block == 44:
                    blockstouse = 2
                    blocktomake = 43
                elif block == 43:
                    blockstouse = 1
                    blocktomake = 44
                elif block == 6:
                    blockstouse = 4
                    blocktomake = 19
                blockstouse = numofblockstomake * blockstouse
                if block == 17:
                    numofblockstomake = numofblockstomake * 4
                elif block == 1:
                    numofblockstomake = numofblockstomake * 2
                elif block == 43:
                    numofblockstomake = numofblockstomake * 2
                numofblock = self.client.var_blocks[block]
                if blockstouse > numofblock:
                    self.client.sendServerMessage("You do not have enough %s block(s), you need %s." % (BlockList[block], blockstouse))
                    return
                self.client.var_blocks[block] -= blockstouse
                self.client.var_blocks[blocktomake] += numofblockstomake
                self.client.sendServerMessage("You have crafted %s %s block(s) into" % (blockstouse, BlockList[block]))
                self.client.sendServerMessage("%s %s block(s)" % (numofblockstomake, BlockList[blocktomake]))
        else:
            self.client.sendServerMessage("You are not in a Survival Game Mode World!")
            
    def commandGive(self, parts, fromloc, overriderank):
        "/give username numberofblocks blocktype\nSurvival Game Mode Only\nAllows you to give people blocks"
        if self.in_survivalworld:
            if len(parts) != 4:
                self.client.sendSplitServerMessage("Please enter the username of the person to give blocks to and the amount and type to give.")
            else:
                
                username = parts[1]
                try:
                    other = self.client.factory.usernames[username]
                except:
                    self.client.sendServerMessage("%s is not online." % username)
                    return
                if other.world != self.client.world:
                    self.client.sendServerMessage("%s is not in the same world." % username)
                    return
                try:
                    numblockstosend = int(parts[2])
                except:
                    self.client.sendServerMessage("The number of blocks must be an integer.")
                    return
                if numblockstosend <= 0:
                    self.client.sendServerMessage("The number of blocks must be greater than 0.")
                    return
                block = self.client.GetBlockValue(parts[1])
                if block == None:
                    return
                numofblock = self.client.var_blocks[block]
                if numblockstosend > numofblock:
                    self.client.sendServerMessage("You do not have that many %s block(s)." % BlockList[block])
                    return
                self.client.var_blocks[block] -= numblockstosend
                other.var_blocks[block] += numblockstosend
                self.client.sendServerMessage("You have sent %s %s block(s) to %s." % (numblockstosend, BlockList[block], username))
                    
        else:
            self.client.sendServerMessage("You are not in a Survival Game Mode World!")
                    
    def commandInventory(self, parts, fromloc, overriderank):
        "/inventory \nSurvival Game Mode Only\nAllows you to check your inventory"
        if self.in_survivalworld:
            inv_list = []
            for key in self.client.var_blocks:
                inv_list.append(BlockList[key] + ": " + str(self.client.var_blocks[key]))
            self.client.sendServerList(inv_list)
        else:
            self.client.sendServerMessage("You are not in a Survival Game Mode World!")
            
    def commandBlocktext(self, parts, fromloc, overriderank):
        "/blocktext \nSurvival Game Mode Only\nAllows you toggle block notifications(collection and setting)."
        if self.in_survivalworld:
            if self.var_showtext:
                self.var_showtext = False
                self.client.sendServerMessage("Block collection and placement notification: ON")
            else:
                self.var_showtext = True
                self.client.sendServerMessage("Block collection and placement notification: ON")
        else:
            self.client.sendServerMessage("You are not in a Survival Game Mode World!")
