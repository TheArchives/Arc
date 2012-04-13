# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor, threads

from arc.constants import *
from arc.decorators import *

BUILD_POSSIBLES = {
    "op": {
        "air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
        "water": (BLOCK_WATER, BLOCK_INDIGO_CLOTH, "Dark Blue cloth"),
        "watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
        "stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
        "lava": (BLOCK_LAVA, BLOCK_ORANGE_CLOTH, "Orange cloth"),
        "stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
        "lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
        "grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
        "doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
    },
    "guest": {
        "air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
        "water": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
        "watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
        "stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
        "lava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
        "stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
        "lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
        "grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
        "doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
    }
}

class BuildUtilPlugin(object):
    name = "BuildUtilPlugin"
    commands = {
        "bind": "commandBind",
        "build": "commandBuild",
        "paint": "commandPaint",
        "air": "commandAir",

        "copy": "commandCopy",
        "paste": "commandPaste",
        "rotate": "commandRotate",
        "xzrotate": "commandRotateXZ",
        "xyrotate": "commandRotateXY",
        "yzrotate": "commandRotateYZ",

        "binfo": "commandInfo",
        "blockindex": "commandBlockindex",

        "replace": "commandReplace",
        "creplace": "commandCreplace",
        "replacenot": "commandReplaceNot",
        "replacenear": "commandReplaceNear",
        "fill": "commandFill",

        "ruler": "commandRuler",

        "solid": "commandSolid",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "preBlockChange": "preBlockChanged",
        "blockChange": "blockChanged",
        }

    def gotClient(self, data):
        data["client"].block_overrides = {}
        data["client"].saved_blocks = {}
        data["client"].binfo = False
        data["client"].painting = False

    def preBlockChanged(self, data):
        if data["client"].binfo:
            check_offset = data["client"].world.blockstore.get_offset(data["x"], data["y"], data["z"])
            block2 = ord(data["client"].world.blockstore.raw_blocks[check_offset])
            actual_block = data["block"] if block2 == 0 else block2
            data["client"].sendServerMessage("Block Info: %s (%s)" % (BlockList[actual_block], actual_block))
            data["client"].sendServerMessage("x: %s y: %s z: %s" % (x, y, z))
            return block2
        if data["block"] == BLOCK_AIR and data["client"].painting:
            return data["selected_block"]

    def blockChanged(self, data):
        "Hook trigger for block changes."
        # Block override for /bind
        if isinstance(data, list):
            block = data[0]
            if block in data["client"].block_overrides:
                return data["client"].block_overrides[block]

    @config("category", "build")
    @config("usage", "blockA blockB")
    @config("aliases", ["b", "material"])
    @config("disabled-on", ["console", "irc", "irc_query"])
    def commandBind(self, data):
        "Binds blockB to blockA."
        if len(data["parts"]) == 1:
            if data["client"].block_overrides:
                data["client"].block_overrides = tuple()
                data["client"].sendServerMessage("All blocks are back to normal.")
                return
            else:
                data["client"].sendServerMessage("Please enter two block types.")
        elif len(data["parts"]) == 2:
            old = ord(data["client"].allowedToBuild(data["parts"][1]))
            if old == None:
                data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % old)
            if old in self.block_overrides:
                del self.block_overrides[old]
                data["client"].sendServerMessage("%s is back to normal." % data["parts"][1])
            else:
                data["client"].sendServerMessage("Please enter two block types.")
        else:
            old = data["client"].getBlockValue(data["parts"][1])
            if old == None:
                data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % old)
            old = ord(old)
            new = data["client"].getBlockValue(data["parts"][2])
            if new == None:
                data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % new)
            new = ord(new)
            old_name, name = [i.lower() for i in data["parts"][1:2]]
            data["client"].block_overrides[old] = new
            data["client"].sendServerMessage("%s will turn into %s." % (old_name, name))

    @config("category", "build")
    @config("aliases", ["place", "stand"])
    @config("disabled-on", ["console", "irc", "irc_query", "cmdblock"])
    def commandAir(self, data):
        "Puts a block under you for easier building in the air."
        data["client"].sendPacked(TYPE_BLOCKSET, data["client"].x >> 5, (data["client"].y >> 5) - 3, (data["client"].z >> 5), BLOCK_WHITE)

    @config("category", "build")
    @config("usage", "water|watervator|lava|stilllava|grass|doublestep")
    @config("disabled-on", ["console", "irc", "irc_query"])
    def commandBuild(self, data):
        "Lets you build special blocks."
        if data["client"].isOp():
            possibles = BUILD_POSSIBLES["op"]
        else:
            possibles = BUILD_POSSIBLES["guest"]
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Specify a type to toggle.")
            return
        name = data["parts"][1].lower()
        try:
            new, old, old_name = possibles[name]
        except KeyError:
            data["client"].sendServerMessage("'%s' is not a special block type." % name)
        else:
            if old in data["client"].block_overrides:
                del data["client"].block_overrides[old]
                data["client"].sendServerMessage("%s is back to normal." % old_name)
            else:
                data["client"].block_overrides[old] = new
                data["client"].sendServerMessage("%s will turn into %s." % (old_name, name))

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "[x y z world]")
    def commandPaste(self, data):
        "Restore blocks saved earlier using /copy."
        if fromloc == "user":
            if len(data["parts"]) < 4 and len(data["parts"]) != 1:
                data["client"].sendServerMessage("Please click a block (or a coord triple)")
                return
        else:
            if len(data["parts"]) < 5:
                data["client"].sendServerMessage("Please enter a coord triple and a world.")
                return
        if len(data["parts"]) == 1 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not placed a marker yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][1:3]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        # Check whether we have anything saved
        try:
            num_saved = len(data["client"].saved_blocks)
            if fromloc != "cmdblock":
                data["client"].sendServerMessage("Loading %d blocks..." % num_saved)
        except AttributeError:
            data["client"].sendServerMessage("Please /copy something first.")
            return
        # Build the changeset
        changeset = {}
        for i, j, k, block in data["client"].saved_blocks:
            if not (data["client"].getBlockValue (i, j, k) or overriderank):
                continue
            rx, ry, rz = x + i, y + j, z + k
            changeset[rx, ry, rz] = block
        # Now, apply it.
        def pasteCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Paste finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(pasteCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "[x y z x2 y2 z2 world]")
    def commandCopy(self, data):
        "Copy blocks using specified offsets."
        if fromloc == "user":
            if len(data["parts"]) < 4 and len(data["parts"]) != 1:
                data["client"].sendServerMessage("Please click 2 blocks (or enter 2 coord triples)")
                return
        else:
            if len(data["parts"]) < 5:
                data["client"].sendServerMessage("Please enter 2 coord triples and a world.")
                return
        if len(data["parts"]) == 1 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][1:6]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        if fromloc != "user" and len(data["parts"]) >= 7:
            w = data["parts"][7]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
            else:
                world = w
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if ((x2 - x) * (y2 - y) * (z2 - z) > limit):
                data["client"].sendServerMessage("Copy limit exceeded. (Limit is %s)" % limit)
                return
        def doBlocks():
            # Clear the blocks, if some blocks have been copied
            data["client"].saved_blocks = {}
            try:
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                                continue
                            check_offset = self.factory.worlds[world].blockstore.get_offset(i, j, k)
                            block = self.factory.worlds[world].blockstore.raw_blocks[check_offset]
                            data["client"].saved_blocks[i - x, j - y, k - z] = block
            except AssertionError:
                data["client"].sendServerMessage("Out of bounds copy error.")
                return

        def copyDoneCallback(r):
            data["client"].sendServerMessage("Copy completed.")

        data["client"].sendServerMessage("Copying... This may take a while.")
        threads.deferToThread(doBlocks).addCallback(copyDoneCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "angle")
    def commandRotate(self, data):
        "Allows you to rotate what you copied."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must give an angle to rotate.")
            return
        try:
            angle = int(data["parts"][1])
        except ValueError:
            data["client"].sendServerMessage("Angle must be an integer.")
            return
        if angle % 90 != 0:
            data["client"].sendServerMessage("Angle must be divisible by 90.")
            return
        if data["client"].saved_blocks == {}:
            data["client"].sendServerMessage("You haven't used /copy yet.")
            return
        rotations = angle / 90
        data["client"].sendServerMessage("Rotating %s degrees..." % angle)
        for rotation in range(rotations):
            tempblocks = {}
            xmax = zmax = 0
            for k in data["client"].saved_blocks.keys():
                x, y, z = k
                if x > xmax: xmax = x
                if z > zmax: zmax = z
            for k, v in data["client"].saved_blocks.items():
                x, y, z = k
                tempx, tempz = x, z
                x, z = zmax - tempz, tempx
                tempblocks[x, y, z] = v
            data["client"].saved_blocks = tempblocks
        if fromloc == "user":
            data["client"].sendServerMessage("Rotate completed.")

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "angle")
    def commandRotateXZ(self, data):
        "Allows you to rotate what you copied along the X/Z axis."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must give an angle to rotate.")
            return
        try:
            angle = int(data["parts"][1])
        except ValueError:
            data["client"].sendServerMessage("Angle must be an integer.")
            return
        if angle % 90 != 0:
            data["client"].sendServerMessage("Angle must be divisible by 90.")
            return
        if data["client"].saved_blocks == {}:
            data["client"].sendServerMessage("You haven't used /copy yet.")
            return
        rotations = angle / 90
        data["client"].sendServerMessage("Rotating %s degrees..." % angle)
        for rotation in range(rotations):
            tempblocks = {}
            xmax = zmax = 0
            for k in data["client"].saved_blocks.keys():
                x, y, z = k
                if x > xmax: xmax = x
                if z > zmax: zmax = z
            for k, v in data["client"].saved_blocks.items():
                x, y, z = k
                tempx, tempz = x, z
                x, z = zmax - tempz, tempx
                tempblocks[x, y, z] = v
            data["client"].saved_blocks = tempblocks
        if fromloc == "user":
            data["client"].sendServerMessage("Rotate completed.")

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "angle")
    def commandRotateXY(self, data):
        "Allows you to rotate what you copied along the X/Y axis."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must give an angle to rotate.")
            return
        try:
            angle = int(data["parts"][1])
        except ValueError:
            data["client"].sendServerMessage("Angle must be an integer.")
            return
        if angle % 90 != 0:
            data["client"].sendServerMessage("Angle must be divisible by 90.")
            return
        if data["client"].saved_blocks == {}:
            data["client"].sendServerMessage("You haven't used /copy yet.")
            return
        rotations = angle / 90
        data["client"].sendServerMessage("Rotating %s degrees..." % angle)
        for rotation in range(rotations):
            tempblocks = {}
            xmax = ymax = 0
            for k in data["client"].saved_blocks.keys():
                x, y, z = k
                if x > xmax: xmax = x
                if y > ymax: ymax = y
            for k, v in data["client"].saved_blocks.items():
                x, y, z = k
                tempx, tempy = x, y
                x, y = ymax - tempy, tempx
                tempblocks[x, y, z] = v
            data["client"].saved_blocks = tempblocks
        if fromloc == "user":
            data["client"].sendServerMessage("Rotate completed.")

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "angle")
    def commandRotateYZ(self, data):
        "Allows you to rotate what you copied along the Y/Z axis."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must give an angle to rotate.")
            return
        try:
            angle = int(data["parts"][1])
        except ValueError:
            data["client"].sendServerMessage("Angle must be an integer.")
            return
        if angle % 90 != 0:
            data["client"].sendServerMessage("Angle must be divisible by 90.")
            return
        if data["client"].saved_blocks == {}:
            data["client"].sendServerMessage("You haven't used /copy yet.")
            return
        rotations = angle / 90
        data["client"].sendServerMessage("Rotating %s degrees..." % angle)
        for rotation in range(rotations):
            tempblocks = {}
            ymax = zmax = 0
            for k in data["client"].saved_blocks.items():
                x, y, z = k
                if y > ymax: ymax = y
                if z > zmax: zmax = z
            for k, v in data["client"].saved_blocks.items():
                x, y, z = k
                tempy, tempz = y, z
                y, z = zmax - tempz, tempy
                tempblocks[x, y, z] = v
            data["client"].saved_blocks = tempblocks
        if fromloc == "user":
            data["client"].sendServerMessage("Rotate completed.")

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "factor")
    def commandScaleUp(self, data):
        "Scales your /copy up by a given factor."
        if len(data["parts"]) < 2:
            self.client.sendServerMessage("You must enter a factor.")
            return
        try:
            factor = int(data["parts"][1])
        except ValueError:
            self.client.sendServerMessage("Factor must be an integer.")
        if (factor < 2):
            self.client.sendServerMessage("Factor must be bigger than 1.")
            return
        if data["client"].saved_blocks == {}:
            data["client"].sendServerMessage("You haven't used /copy yet.")
            return
        tempblocks = set()
        ymax = zmax = 0
        try:
            for x, y, z, block in self.client.bsaved_blocks:
                if y > ymax:
                    ymax = y
                if z > zmax:
                    zmax = z
        except:
            self.client.sendServerMessage("You haven't used /copy yet.")
            return
        for x, y, z, block in self.client.bsaved_blocks:
            for x2 in range(0, factor):
                for y2 in range(0, factor):
                    for z2 in range(0, factor):
                        tempblocks.add((((x*factor)-(x2-(factor-1))),((y*factor)-(y2-(factor-1))),((z*factor)-(z2-(factor-1))),block))
        self.client.bsaved_blocks = tempblocks
        if fromloc == "user":
            self.client.sendServerMessage("Your scaleup just completed.")

    @config("category", "build")
    @config("usage", "[x y z world]")
    @config("aliases", ["bget", "rget", "pget"])
    def commandInfo(self, data):
        "Starts getting information on blocks. Toggle. (If used with a coord triplet, it will instead show the block info of that block.)"
        if len(data["parts"]) > 1:
            try:
                x, y, z = [int(i) for i in data["parts"][1:3]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
            check_offset = data["client"].world.blockstore.get_offset(x, y, z)
            block = ord(data["client"].world.blockstore.raw_blocks[check_offset])
            data["client"].sendServerMessage("Block Info: %s (%s)" % (BlockList[block], block))
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("Usage: /binfo x y z world")
                return
            if not data["client"].binfo:
                data["client"].binfo = True
                data["client"].sendServerMessage("You are now getting info about blocks.")
            else:
                data["client"].binfo = False
                data["client"].sendServerMessage("You are no longer getting info about blocks.")

    @config("category", "build")
    @config("aliases", ["bindex"])
    def commandBlockindex(self, data):
        "Gives you the index of the block."
        if len(data["parts"]) != 2:
            data["client"].sendServerMessage("Please enter a block to check the index of.")
        else:
            try:
                block = globals()['BLOCK_%s' % data["parts"][1].upper()]
            except KeyError:
                data["client"].sendServerMessage("'%s' is not a valid block type." % data["parts"][1])
                return
            data["client"].sendServerMessage("%s is represented by %s" % (data["parts"][1], block))

    @config("category", "build")
    def commandPaint(self, data):
        "/paint - Guest\nLets you break-and-build in one move. Toggle."
        if self.painting:
            self.painting = False
            data["client"].sendServerMessage("Painting mode is now off.")
        else:
            self.painting = True
            data["client"].sendServerMessage("Painting mode is now on.")

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockA blockB [x y z x2 y2 z2 world]")
    @config("aliases", ["brep"])
    def commandReplace(self, data):
        "Replaces all blocks of blockA in this area to blockB."
        if fromloc == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter 2 types (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter 2 types, 2 coord triples and a world.")
                return
        blockA = data["client"].getBlockValue(data["parts"][1])
        blockB = data["client"].getBlockValue(data["parts"][2])
        if blockA == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if blockB == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][2])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 3 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][3:8]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 10:
            w = data["parts"][9]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    check_offset = self.factory.worlds[w].blockstore.get_offset(i, j, k)
                    block = self.factory.worlds[w].blockstore.raw_blocks[check_offset]
                    if block == blockA: changeset[i, j, k] = blockB
        # Stop them doing silly things
        total = len(changeset.keys())
        limit = data["client"].getBlbLimit(3)
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Replace limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def replaceCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Replace finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(replaceCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockA blockB [x y z x2 y2 z2 world]")
    @config("aliases", ["nrep"])
    def commandReplaceNot(self, data):
        "Replaces all blocks of in this area to blockA, except for blockB."
        if fromloc == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter 2 types (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter 2 types, 2 coord triples and a world.")
                return
        blockA = data["client"].getBlockValue(data["parts"][1])
        blockB = data["client"].getBlockValue(data["parts"][2])
        if blockA == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if blockB == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][2])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 3 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][3:8]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 10:
            w = data["parts"][9]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    check_offset = self.factory.worlds[w].blockstore.get_offset(i, j, k)
                    block = self.factory.worlds[w].blockstore.raw_blocks[check_offset]
                    if block != blockB: changeset[i, j, k] = blockA
        # Stop them doing silly things
        total = len(changeset.keys())
        limit = data["client"].getBlbLimit()
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("ReplaceNot limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def replaceNotCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("ReplaceNot finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(replaceNotCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("aliases", ["crep"])
    @config("usage", "typeA typeB typeC [x y z x2 y2 z2 world]")
    def commandCreplace(self, data):
        "Replaces all blocks of typeA in this cuboid to typeB and typeC."
        if fromloc == "user":
            if len(data["parts"]) < 11 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter 3 types (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 12:
                data["client"].sendServerMessage("Please enter 3 types, 2 coord triples and a world.")
                return
        blockA = data["client"].getBlockValue(data["parts"][1])
        blockB = data["client"].getBlockValue(data["parts"][2])
        blockC = data["client"].getBlockValue(data["parts"][3])
        if blockA == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if blockB == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][2])
            return
        if blockC == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][3])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][4:9]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 11:
            w = data["parts"][10]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    blockcheck = world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)]
                    if blockcheck == blockA:
                        changeset[i, j, k] = blockB if (i + j + k) % 2 == 0 else blockC
        # Stop them doing silly things
        total = len(changeset.keys())
        limit = data["client"].getBlbLimit()
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("CReplace limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def creplaceCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("CReplace finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(creplaceCallback)

    @config("rank", "builder")
    @config("aliases", ["rnear"])
    @config("usage", "radius blockA blockB [x y z world]")
    def commandReplaceNear(self, data):
        "Replaces all blockAs near you to blockB."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 3:
                data["client"].sendSplitServerMessage("Please enter the radius, the block to find and the block to replace (and possibly a coord triplet)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter 3 types, 2 coord triples and a world.")
                return
        try:
            radius = int(data["parts"][1])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a number.")
            return
        blockA = data["client"].getBlockValue(data["parts"][2])
        blockB = data["client"].getBlockValue(data["parts"][3])
        if blockA == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if blockB == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][2])
            return
        if len(data["parts"]) == 4 and data["fromloc"] == "user":
            # If they only provided the type argument, use the current player position
            x, y, z = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][4:6]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 8:
            w = data["parts"][7]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        # Build the changeset
        changeset = {}
        try:
            for i in range(x - radius, x + radius):
                for j in range(y - radius, y + radius):
                    for k in range(z - radius, z + radius):
                        if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                            continue
                        check_offset = world.blockstore.get_offset(i, j, k)
                        block = world.blockstore.raw_blocks[check_offset]
                        if block == blockA: changeset[i, j, k] = blockB
        except AssertionError:
            data["client"].sendErrorMessage("Out of bounds replacenear error.")
            return
        limit = data["client"].getBlbLimit()
        total = len(changeset.keys())
        if limit != -1:
            # Stop them doing silly things
            if ((radius * 2) ** 3 > limit):
                data["client"].sendSplitServerMessage("ReplaceNear limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def replaceNearCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("ReplaceNear finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(replaceNearCallback)
          
    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname repblock [x y z x2 y2 z2 world]")
    def commandFill(self, data):
        "/fill  - Op\nFills the area with the block."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendSplitServerMessage("Please enter a type and a type to replace (and possibly two coord triples)")
                data["client"].sendSplitServerMessage("""Note that you must place two blocks to use it.
                                                    The first block sets where to spread from,
                                                    and the second block sets which directions to spread.""")
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter a type, a type to replace, two coord triples and a world.")
                data["client"].sendServerMessage("The first coord triplet sets where to spread from, and the second triplet sets which directions to spread.")
        blockA = data["client"].getBlockValue(data["parts"][1])
        blockB = data["client"].getBlockValue(data["parts"][2])
        if blockA == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if blockB == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][2])
            return
            # If they only provided the type argument, use the last block place
        if len(data["parts"]) == 3 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[1]
                x2, y2, z2 = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two points yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][3:8]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
        locx, locy, locz = [(1, 0, 0), (-1, 0, 0)], [(0, 1, 0), (0, -1, 0)], [(0, 0, 1), (0, 0, -1)]
        loc_check = []
        if x != x2: loc_check = loc_check + locx
        if y != y2: loc_check = loc_check + locy
        if z != z2: loc_check = loc_check + locz
        if loc_check == []:
            data["client"].sendServerMessage("Repeated points error.")
            return
        var_blocklist = [(x, y, z, (-20, -20, -20))]
        if fromloc != "user" and len(data["parts"]) >= 10:
            w = data["parts"][9]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
            else:
                world = w
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
                return
            else:
                w = str(data["client"].world.id)
        changeset = {(x, y, z): block}
        var_blockchanges = 0
        limit = data["client"].getBlbLimit()
        while var_blocklist != []:
            if limit > -1:
                if var_blockchanges > limit:
                    data["client"].sendServerMessage("You have exceeded the fill limit for your rank. (Limit is %s)" % limit)
                    return
            i, j, k, positionprevious = var_blocklist[0]
            var_blockchanges += 1
            for offsettuple in loc_check:
                ia, ja, ka = offsettuple
                ri, rj, rk = i + ia, j + ja, k + ka
                if (ri, rj, rk) != positionprevious:
                    try:
                        if not data["client"].allowedToBuild(ri, rj, rk) and not overriderank:
                            data["client"].sendServerMessage("You do not have permission to build here.")
                            return
                        checkblock = world.blockstore.raw_blocks[world.blockstore.get_offset(ri, rj, rk)]
                        if checkblock == blockB:
                            changeset[ri, rj, rk] = blockA
                            var_blocklist.append((ri, rj, rk, (i, j, k)))
                    except AssertionError:
                        pass
            del var_blocklist[0]
        # Now, apply it.
        def fillCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Fill finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(fillCallback)

    @config("category", "world")
    @config("aliases", ["measure"])
    @config("usage", "[x y z x2 y2 z2]")
    def commandRuler(self, data):
        "Counts the amount of blocks between two clicks."
        # Use the last two block places
        if data["fromloc"] == "user" and data["parts"] < 7:
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two blocks yet.")
                return
        else:
            if data["parts"] < 7:
                data["client"].sendServerMessage("Please specify 2 coord triplets.")
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][1:6]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        xRange, yRange, zRange = abs(x - x2) + 1, abs(y - y2) + 1, abs(z - z2) + 1
        data["client"].sendServerMessage("X = %d, Y = %d, Z = %d" % (xRange, yRange, zRange))

    @config("category", "build")
    @config("rank", "op")
    @config("aliases", ["adminblock", "bedrock"])
    def commandSolid(self, data):
        "Toggles admincrete creation."
        if 1 in data["client"].block_overrides.keys():
            del data["client"].block_overrides[1]
            data["client"].sendServerMessage("You are now placing normal rock.")
        else:
            data["client"].block_overrides[1] = 7
            data["client"].sendServerMessage("You are now placing admin rock.")

serverPlugin = BuildUtilPlugin