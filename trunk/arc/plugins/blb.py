# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import math

from twisted.internet import reactor, threads

from arc.constants import *
from arc.decorators import *

class BlbPlugin(object):
    name = "BlbPlugin"
    commands = {
        "blb": "commandBlb",
        "bhb": "commandBHB",
        "bwb": "commandBWB",
        "bcb": "commandBCB",
        "bhcb": "commandBHCB",
        "bfb": "commandBFB",
        "bob": "commandOneBlb",
        }

    @config("category", "build")
    @config("rank", "builder")
    @config("aliases", ["oblb"])
    @config("usage", "blocktype [x y z world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandOneBlb(self, data):
        "Sets block to blocktype.\nClick 1 block then do the command."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 5 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 6:
                data["client"].sendServerMessage("Please enter a type, a coord triple and a world.")
                return
        block = self.allowedToBuild(parts[1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last block place
        if len(parts) == 2 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked a block yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][2:4]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if data["fromloc"] != "user" and len(data["parts"]) >= 6:
            w = data["parts"][5]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
            else:
                world = str(self.factory.worlds[w].id)
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        try:
            if not data["client"].getBlockValue (x, y, z) and not data["overriderank"]:
                return
            world[x, y, z] = block
            data["client"].world.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
            data["client"].world.sendBlock(x, y, z, block)
        except AssertionError:
            data["client"].sendServerMessage("Out of bounds bob error.")
            return
        else:
            if data["fromloc"] == "user":
                data["client"].sendServerMessage("BOB Completed.")

    @config("category", "build")
    @config("rank", "builder")
    @config("aliases", ["box", "cub", "cuboid", "draw", "z"])
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    def commandBlb(self, data):
        "Sets all blocks in this area to block.\nClick 2 corners then do the command."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][2:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if data["fromloc"] != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
            else:
                world = w
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = (x2 - x) * (y2 - y) * (z2 - z)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("BLB Area Limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    changeset[(i, j, k)] = block
        # Now, apply it.
        def blbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BLB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(blbCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandBHB(self, data):
        "Sets all blocks in this area to block, hollow."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][2:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if data["fromloc"] != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = ((x2 - x) * (y2 - y) * (z2 - z) - (((x2 - 1) - (x - 1)) * ((y2 - 1) - (y - 1)) * ((z2 - 1) - (z - 1))))
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("BHB Area Limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
                        changeset[(i, j, k)] = block
        # Now, apply it.
        def bhbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BHB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(bhbCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandBWB(self, data):
        "Builds four walls between the two areas.\nHollow, with no roof or floor."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][2:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if data["fromloc"] != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = ((x2 - x) * (y2 - y) * (z2 - z) - (((x2 - 1) - (x - 1)) * (y2 - y) * ((z2 - 1) - (z - 1))))
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("BWB Area Limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    if i == x or i == x2 or k == z or k == z2: changeset[i, j, k] = block
        # Now, apply it.
        def bwbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BWB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w, count=False).addBoth(bwbCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "block block2 [x y z x2 y2 z2 world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandBCB(self, data):
        "Sets all blocks in this area to block, checkered."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter a type, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        block2 = data["client"].getBlockValue(data["parts"][2])
        if None in [block, block2]:
            data["client"].sendSplitServerMessage("'%s' or '%s' is either not a valid block type, or is not available to you." % (data["parts"][1], data["parts"][2]))
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 3:
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
        if data["fromloc"] != "user" and len(data["parts"]) >= 10:
            w = data["parts"][9]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = (x2 - x) * (y2 - y) * (z2 - z)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("BCB Area Limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        return
                    changeset[(i, j, k)] = block if (i + j + k) % 2 == 0 else block2
        # Now, apply it.
        def bcbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BCB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(bcbCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "block block2 [x y z x2 y2 z2 world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandBHCB(self, data):
        "Sets all blocks in this area to blocks, checkered hollow."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter 2 types (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter 2 types, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        block2 = data["client"].getBlockValue(data["parts"][2])
        if None in [block, block2]:
            data["client"].sendSplitServerMessage("'%s' or '%s' is either not a valid block type, or is not available to you." % (data["parts"][1], data["parts"][2]))
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 3:
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
        if data["fromloc"] != "user" and len(data["parts"]) >= 10:
            w = data["parts"][9]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = ((x2 - x) * (y2 - y) * (z2 - z) - (((x2 - 1) - (x - 1)) * ((y2 - 1) - (y - 1)) * ((z2 - 1) - (z - 1))))
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("BFB Limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changes
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        return
                    if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
                        if (i + j + k) % 2 == 0:
                            changeset[(i, j, k)] = block
                        else:
                            changeset[(i, j, k)] = block2
        # Now, apply it.
        def bhcbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BCB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(bhcbCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    @config("disabled-on", ["irc", "irc_query"])
    def commandBFB(self, data):
        "Sets all blocks in this area to block, wireframe."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, 2 coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and data["fromloc"] == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][2:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if data["fromloc"] != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        total = ((x2 - x) * (y2 - y) * (z2 - z) - ((((x2 - 1) - (x - 1)) * ((y2 - 1) - (y - 1)) * ((z2 - 1) - (z - 1))) + (((x2 - 1) - (x - 1)) * ((y2 - 1) - (y - 1)) * 2) + (((y2 - 1) - (y - 1)) * ((z2 - 1) - (z - 1)) * 2) + (((x2 - 1) - (x - 1)) * ((z2 - 1) - (z - 1)) * 2)))
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("Sorry, that area is too big for you to bfb (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        return
                    if (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or \
                    (i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or \
                    (i == x and k == z2) or (j == y and k == z2) or (i == x2 and k == z) or \
                    (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                        changeset[(i, j, k)] = block
        # Now, apply it.
        def bfbCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("BFB finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(bfbCallback)

serverPlugin = BlbPlugin
serverPlugin = BlbPlugin