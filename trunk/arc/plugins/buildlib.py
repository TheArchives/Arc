# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cmath, random

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

class BuildLibPlugin(object):
    name = "BuildLibPlugin"
    commands = {
        "sphere": "commandSphere",
        "hsphere": "commandHSphere",
        "curve": "commandCurve",
        "line": "commandLine",
        "pyramid": "commandPyramid",
        "csphere": "commandCsphere",
        "circle": "commandCircle",
        "hcircle": "commandHCircle",
        "hcyl": "commandHCylinder",
        "cylinder": "commandCylinder",
        "cyl": "commandCylinder",
        "dome": "commandDome",
        "ellipsoid": "commandEllipsoid",
        "ell": "commandEllipsoid",
        "polytri": "commandPolytri",
        "stairs": "commandStairs",

        "dune": "commandDune",
        "hill": "commandHill",
        "hole": "commandHole",
        "lake": "commandLake",
        "mountain": "commandMountain",
        "pit": "commandPit",
        "tree": "commandTree",

        "fungus": "commandFungus",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "blockChanged": "blockChanged",
        }

    TRUNK_HEIGHT = 5, 9
    FANOUT = 3, 5

    def gotClient(self, data):
        data["client"].build_trees = False

    def newWorld(self, data):
        "Hook to reset dynamiting abilities in new worlds if not builder."
        if not data["client"].isBuilder():
            data["client"].build_trees = False

    def blockChanged(self, data):
        "Hook trigger for block changes."
        if data["client"].build_trees:
            tobuild = {}
            # Randomise the variables
            trunk_height = random.randint(*self.TRUNK_HEIGHT)
            fanout = random.randint(*self.FANOUT)
            if block == BLOCK_PLANT:
                # Build the main tree bit
                for i in range(-fanout - 1, fanout):
                    for j in range(-fanout - 1, fanout):
                        for k in range(-fanout - 1, fanout):
                            if not data["client"].allowedToBuild(data["x"] + i, data["y"] + j, data["z"] + k):
                                return
                            if (i ** 2 + j ** 2 + k ** 2) ** 0.5 < fanout:
                                tobuild[i, j + trunk_height, k] = BLOCK_LEAVES
                # Build the trunk
                for i in range(trunk_height):
                    tobuild[0, i, 0] = BLOCK_LOG
                # OK, send the build changes
                self.factory.applyBlockChanges(tobuild, data["client"].world)
                return -1 # We will handle the changes ourselves

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blocktype radius [x y z world]")
    def commandSphere(self, data):
        "Generates a sphere."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type and a radius (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter a type, radius, a coord triple and a world.")
                return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a number.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last block place
        if len(data["parts"]) == 3 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked a block yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][3:5]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 7:
            w = data["parts"][6]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if ((radius * 2) ** 3 > limit):
                data["client"].sendServerMessage("Sphere limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-radius - 1, radius):
            for j in range(-radius - 1, radius):
                for k in range(-radius - 1, radius):
                    if (i ** 2 + j ** 2 + k ** 2) ** 0.5 < radius:
                        if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                            continue
                        changeset[x + i, y + j, z + k] = block
        # Now, apply it.
        def sphereCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Sphere finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(sphereCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blocktype radius [x y z world]")
    def commandHSphere(self, data):
        "Generates a hollow sphere."
        if fromloc == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter a type and a radius (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, radius, a coord triple and a world.")
                return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a number.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last block place
        if len(data["parts"]) == 3 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked a block yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][3:5]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 7:
            w = data["parts"][6]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (((radius * 2) ** 3) - (((radius - 1) * 2) ** 3) > limit):
                data["client"].sendServerMessage("HSphere limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-radius - 1, radius):
            for j in range(-radius - 1, radius):
                for k in range(-radius - 1, radius):
                    if (i ** 2 + j ** 2 + k ** 2) ** 0.5 < radius and \
                        (i ** 2 + j ** 2 + k ** 2) ** 0.5 > (radius - 1.49):
                        if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                            continue
                        changeset[x + i, y + j, z + k] = block
        # Now, apply it.
        def hsphereCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("HSphere finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(hsphereCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockname [x y z x2 y2 z2 x3 y3 z3 world]")
    def commandCurve(self, data):
        "Sets a line of blocks along three points to block."
        if fromloc == "user":
            if len(data["parts"]) < 11 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 12:
                data["client"].sendServerMessage("Please enter a type, radius, a coord triple and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
                x3, y3, z3 = data["client"].last_block_changes[2]
            except:
                data["client"].sendServerMessage("You have not clicked 3 points yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2, x3, y3, z3 = [int(i) for i in data["parts"][2:10]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 12:
            w = data["parts"][11]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        estimatedBlocks = (2 * ((x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2) ** 0.5 + 2 * ((x2 - x3) ** 2 + (y2 - y3) ** 2 + (z2 - z3) ** 2) ** 0.5)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (estimatedBlocks > limit):
                data["client"].sendServerMessage("Sorry, that area is too big for you to curve (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        # curve list
        steps1 = float(2 * ((x3 - x) ** 2 + (y3 - y) ** 2 + (z3 - z) ** 2) ** 0.5)
        steps2 = float(2 * ((x2 - x3) ** 2 + (y2 - y3) ** 2 + (z2 - z3) ** 2) ** 0.5) + steps1
        coordinatelist = []

        def calcCoord(x, x2, t, steps1, steps2):
            return (x2 - x) * ((t) / (steps1) * (t - steps2) / (steps1 - steps2)) + (x2 - x) * (
            (t) / (steps2) * (t - steps1) / (steps2 - steps1))

        for i in range(steps2 + 1):
            t = float(i)
            var_x, var_y, var_z = calcCoord(x, x2, t, steps1, steps2), calcCoord(y, y2, t, steps1, steps2), calcCoord(z, z2, t, steps1, steps2)
            coordinatelist.append((int(var_x) + x, int(var_y) + y, int(var_z) + z))
        finalcoordinatelist = [coordtuple for coordtuple in coordinatelist if \
                               coordtuple not in finalcoordinatelist]
        for coordtuple in finalcoordinatelist:
            i, j, k = coordtuple
            if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                continue
            world[i, j, k] = block
        # Now, apply it.
        def curveCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Curve finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(curveCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname height fill [x y z world]")
    def commandPyramid(self, data):
        "Sets all blocks in this area to be a pyramid."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter a type, pyramid height and whether to fill (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter a type, pyramid height, whether to fill, a coord triple and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # Try getting the height
        try:
            height = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Height must be a number.")
            return
        # Try getting the fill
        fill = data["parts"][3]
        if fill not in ["true", "false"]:
            data["client"].sendServerMessage("Fill must be true or false.")
            return
        # If they only provided the type argument, use the last block place
        if len(data["parts"]) == 4 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked a block yet.")
                return
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
        limit = data["client"].getBlbLimit()
        # Stop them doing silly things
        if limit != -1:
            if (((x * y) * (z)) / 3 > limit):
                data["client"].sendServerMessage("Pyramid limit exceeded. (Limit is %s)" % limit)
                return
        pointlist = []
        for i in range(abs(height)):
            they = y + ((height - i - 1) if height > 0 else (height + i + 1))
            if height > 0:
                point1, point2 = [x - i, they, z - i], [x + i, they, z + i]
            else:
                point1, point2 = [x - i, they, z - i], [x + i, they, z + i]
            pointlist = pointlist + [(point1, point2)]
        changeset = {}
        for pointtouple in pointlist:
            x, y, z = pointtouple[0]
            x2, y2, z2 = pointtouple[1]
            for i in range(x, x2 + 1):
                for j in range(y, y2 + 1):
                    for k in range(z, z2 + 1):
                        if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                            continue
                        if fill == "true" or \
                            (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or \
                           (i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or \
                           (i == x and k == z2) or (j == y and k == z2) or (i == x2 and k == z) or \
                           (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                            changeset[i, j, k] = block
        # Now, apply it.
        def pyramidCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Pyramid finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(pyramidCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    def commandLine(self, data):
        "Sets all blocks between two points to be a line."
        if fromloc == "user":
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
        if len(data["parts"]) == 2 and fromloc == "user":
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
        if fromloc != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        steps = int(((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5)
        if steps == 0:
            data["client"].sendServerMessage("Your line need to be longer.")
            return
        changeset = {}
        mx, my, mz = float(x2 - x) / steps, float(y2 - y) / steps, float(z2 - z) / steps
        # Build the changeset
        for t in range(steps + 1):
            x, y, z = int(round(mx * t + x)), int(round(my * t + y)), int(round(mz * t + z))
            if not data["client"].allowedToBuild(x, y, z) and not data["overriderank"]:
                continue
            changeset[x, y, z] = block
        limit = data["client"].getBlbLimit()
        if limit != -1:
        # Stop them doing silly things
            if blocks > limit:
                data["client"].sendServerMessage("Line limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def lineCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Line finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(lineCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype blocktype radius [x y z world]")
    def commandCsphere(self, data):
        "Creates a sphere, checkered."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter two types and the raduis (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter two types, radius, a coord triple and a world.")
                return
        # Try getting the radius
        try:
            radius = int(data["parts"][3])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a number.")
            return
        if None in [block, block2]:
            data["client"].sendSplitServerMessage("'%s' or '%s' is either not a valid block type, or is not available to you." % (data["parts"][1], data["parts"][2]))
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][3:5]]
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
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if ((radius * 2) ** 3 > limit):
                data["client"].sendServerMessage("Csphere limit exceeded.(Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-radius - 1, radius):
            for j in range(-radius - 1, radius):
                for k in range(-radius - 1, radius):
                    if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < radius:
                        if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                            continue
                        changeset[x + i, y + j, z + k] = block2 if (i + j + k) % 2 == 0 else block
        # Now, apply it.
        def csphereCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Csphere finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(csphereCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype radius axis [x y z world]")
    def commandCircle(self, data):
        "Creates a circle."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter a type, the raduis and the axis (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter two types, radius, a coord triple and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # Try getting the normal axis
        normalAxis = data["parts"][3].lower()
        if normalAxis not in ["x", "y", "z"]:
            data["client"].sendServerMessage("Normal axis must be x, y, or z.")
            return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a Number.")
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 or fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
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
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (int(2 * cmath.pi * (radius) ** 2) > limit):
                data["client"].sendServerMessage("Circle limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-radius - 1, radius):
            for j in range(-radius - 1, radius):
                for k in range(-radius - 1, radius):
                    if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.604 < radius:
                        # Test for axis
                        if not ((i != 0 and normalAxis == 'x') or (j != 0 and normalAxis == 'y') or \
                            (k != 0 and normalAxis == 'z')):
                            if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                                continue
                            world[x + i, y + j, z + k] = block
        # Now, apply it.
        def circleCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Circle finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(circleCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype radius fill [x y z world]")
    def commandDome(self, data):
        "Creates a dome."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter a type, the raduis and whether to fill (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter a type, the raduis, whether to fill, a coord triple and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be a number.")
            return
        # Try getting the fill
        fill = data["parts"][3]
        if fill not in ["true", "false"]:
            data["client"].sendServerMessage("Fill must be true or false.")
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 or fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
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
        absradius = abs(radius)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if ((radius * 2) ** 3 / 2 > limit):
                data["client"].sendServerMessage("Sorry, that area is too big for you to dome (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-absradius - 1, absradius):
            for j in range(-absradius - 1, absradius):
                for k in range(-absradius - 1, absradius):
                    if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < absradius and \
                        ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill == "true") or\
                       (absradius - 1 < (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < absradius and \
                       ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill == "false"):
                        if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                            continue
                        changeset[x + i, y + j, z + k] = block
        # Now, apply it.
        def domeCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Dome finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(domeCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype endradius [x y z x2 y2 z2 world]")
    def commandEllipsoid(self, data):
        "Creates an Ellipsoid."
        if fromloc == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendServerMessage("Please enter a type, the raduis (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter a type, the raduis, whether to fill, a coord triple and a world.")
                return
        # Try getting the radius
        try:
            endradius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("End radius must be a Number.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
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
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][2:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        radius = int(round(endradius * 2 + ((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5) / 2 + 1)
        var_x, var_y, var_z = int(round(float(x + x2) / 2)), int(round(float(y + y2) / 2)), int(round(float(z + z2) / 2))
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if (int(4 / 3 * cmath.pi * radius ** 2 * endradius) > limit):
                data["client"].sendServerMessage("Ellipsoid limit exceeded (Limit is %s)" % limit)
                return
        # Build the changeset
        for i in range(-radius - 2, radius + 1):
            for j in range(-radius - 2, radius + 1):
                for k in range(-radius - 2, radius + 1):
                    if (((i + var_x - x) ** 2 + (j + var_y - y) ** 2 + (k + var_z - z) ** 2) ** 0.5 + \
                        ((i + var_x - x2) ** 2 + (j + var_y - y2) ** 2 + (k + var_z - z2) ** 2) ** 0.5) / 2 + 0.691 < radius:
                        if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                            continue
                        changeset[var_x + i, var_y + j, var_z + k] = block
        # Now, apply it.
        def ellipsoidCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Ellipsoid finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(ellipsoidCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname [x y z x2 y2 z2 x3 y3 z3 world]")
    def commandPolytri(self, data):
        "/polytri  - Op\nSets all blocks between three points to block."
        if fromloc == "user":
            if len(data["parts"]) < 11 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly three coord triples)")
                return
        else:
            if len(data["parts"]) < 12:
                data["client"].sendServerMessage("Please enter a type, the raduis, whether to fill, a coord triple and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 3 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
                x3, y3, z3 = data["client"].last_block_changes[2]
            except:
                data["client"].sendServerMessage("You have not clicked 3 points yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2, x3, y3, z3 = [int(i) for i in data["parts"][2:10]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 12:
            w = data["parts"][11]
            # Check if world is booted
            if w not in self.factory.worlds.keys():
                data["client"].sendServerMessage("That world is currently not booted.")
                return
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
            else:
                w = str(data["client"].world.id)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            # Stop them doing silly things
            if ((((x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2) ** 0.5 * ((x - x3) ** 2 + (y - y3) ** 2 + (z - z3) ** 2) ** 0.5) > limit):
                data["client"].sendServerMessage("Polytri limit exceeded. (Limit is %s)" % limit)
                return

        def calcStep(x, x2, y, y2, z, z2):
            return int(((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5 / 0.75)

        # line 1 list
        steps = []
        steps[0] = calcStep(x, x2, y, y2, z, z2)
        mx, my, mz = float(x2 - x) / steps, float(y2 - y) / steps, float(z2 - z) / steps
        coordinatelist2 = []
        for t in range(steps[0] + 1):
            coordinatelist2.append((mx * t + x, my * t + y, mz * t + z))
        # line 2 list
        steps[1] = calcStep(x, x3, y, y3, z, z3)
        mx, my, mz = float(x3 - x) / steps, float(y3 - y) / steps, float(z3 - z) / steps
        coordinatelist3 = []
        for t in range(steps[1] + 1):
            coordinatelist3.append((mx * t + x, my * t + y, mz * t + z))
        # final coordinate list
        if len(coordinatelist2) > len(coordinatelist3):
            coordinatelistA, coordinatelistB = coordinatelist2, coordinatelist3
        else:
            coordinatelistA, coordinatelistB = coordinatelist3, coordinatelist2
        lenofA = len(coordinatelistA)
        listlenRatio = float(len(coordinatelistB)) / lenofA
        finalcoordinatelist = []
        for i in range(lenofA):
            point1 = coordinatelistA[i]
            point2 = coordinatelistB[int(i * listlenRatio)]
            var_x, var_y, var_z = point1
            var_x2, var_y2, var_z2 = point2
            steps = calcStep(var_x, var_x2, var_y, var_y2, var_z, var_z2)
            if steps != 0:
                mx, my, mz = float(var_x2 - var_x) / steps, float(var_y2 - var_y) / steps, float(var_z2 - var_z) / steps
                coordinatelist = []
                for t in range(steps + 1):
                    coordinatelist.append((int(round(mx * t + var_x)), int(round(my * t + var_y)), int(round(mz * t + var_z))))
                for coordtuple in coordinatelist:
                    if coordtuple not in finalcoordinatelist:
                        finalcoordinatelist.append(coordtuple)
            elif point1 not in finalcoordinatelist:
                finalcoordinatelist.append(point1)
        # Build the changeset
        changeset = {}
        for coordtuple in finalcoordinatelist:
            i, j, k = coordtuple
            if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                continue
            changeset[i, j, k] = block
        total = len(changeset.keys())
        # Now, apply it.
        def polytriCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Polytri finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(polytriCallback)

    @config("category", "build")
    @config("rank", "builder")
    @config("usage", "blockname height orientation [x y z x2 y2 z2 world]")
    def commandStairs(self, data):
        "Builds a spiral staircase.\nOrientation: a = anti-clockwise, c = clockwise"
        if fromloc == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter a blocktype, height and the orientation")
                data["client"].sendServerMessage("(and possibly two coord triples)")
                data["client"].sendServerMessage("If the two points are on the 'ground' adjacent to each other, then")
                data["client"].sendServerMessage("the second point will spawn the staircase and the first will")
                data["client"].sendServerMessage("be used for the initial orientation")
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter a blocktype, height, orientation, two coord triples and a world.")
                data["client"].sendServerMessage("""If the two points are on the 'ground' adjacent to each other, then the second 
                                                point will spawn the staircase and the first will
                                                be used for the initial orientation.""")
        # Try getting the counter-clockwise flag
        if data["parts"][3].lower() == "a": counterflag = 1
        elif data["parts"][3].lower() == "c": counterflag = -1
        else:
            data["client"].sendServerMessage("The third entry must be a for anti-clockwise or c for clockwise.")
            return
        try:
            height = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("The height must be an integer.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
                x2, y2, z2 = data["client"].last_block_changes[1]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked two corners yet.")
                return
        else:
            try:
                x, y, z, x2, y2, z2 = [int(i) for i in data["parts"][4:8]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 10:
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
        limit = data["client"].getBlbLimit()
        total = height * 4
        if limit != -1:
            # Stop them doing silly things
            if (total > limit):
                data["client"].sendServerMessage("Stairs limit exceeded. (Limit is %s)" % limit)
                return
        # Determine orientation
        if abs(x - x2) + abs(z - z2) == 1:
            if x - x2 == -1: orientation = 1
            elif z - z2 == -1: orientation = 2
            elif x - x2 == 1: orientation = 3
            else: orientation = 4
        else:
            orientation = 1
        # Determine height sign
        heightsign = 1 if height >= 0 else -1
        stepblock = chr(BLOCK_STEP)
        # Build the changeset
        changeset = {}
        for h in range(abs(height)):
            locy = y + h * heightsign
            combo = [(x, locy, z), (x + 1, locy, z + 1), (x + 1, locy, z), (x + 1, locy, z - 1),\
                (x - 1, locy, z + 1), (x, locy, z + 1), (x - 1, locy, z - 1), (x - 1, locy, z),
                (x, locy, z - 1)]
            if orientation == 1: c1 = [combo[1], combo[2], combo[3]]
            elif orientation == 2: c1 = [combo[4], combo[5], combo[2]]
            elif orientation == 3: c1 = [combo[6], combo[7], combo[3]]
            elif orientation == 4: c1 = [combo[3], combo[8], combo[6]]
            if counterflag == 1: c1.reverse()
            blocklist = [combo[0]] + c1
            orientation = orientation - heightsign * counterflag
            if orientation > 4: orientation = 1
            if orientation < 1: orientation = 4
            for entry in blocklist[:3]:
                i, j, k = entry
                if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                    continue
                changeset[i, j, k] = block
            i, j, k = blocklist[3]
            if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                continue
            changeset[i, j, k] = stepblock
        # Now, apply it.
        def stairsCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Stairs finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(stairsCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "on|off")
    def commandTree(self, data):
        "Builds trees, save the earth!"
        if data["parts"][1] == "on":
            data["client"].build_trees = True
            data["client"].sendServerMessage("You are now building trees; place a plant!")
        else:
            data["client"].build_trees = False
            data["client"].sendServerMessage("You are no longer building trees.")

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "[x y z world]")
    def commandDune(self, data):
        "Creates a sand dune."
        # If they only provided the type argument, use the last two block places
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
        if fromloc != "user" and len(data["parts"]) >= 7:
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
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x_range, z_range = x2 - x, z2 - z
        limit = data["client"].getBlbLimit()
        block = chr(BLOCK_SAND)
        # Build the changeset
        chanegeset = {}
        for i in range(x, x2 + 1):
            for k in range(z, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                dy = int((dx ** 2 * dz ** 2) ** 0.2)
                for j in range(y, y + dy + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    changeset[i, j, k] = block
        total = len(changeset.keys())
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Dune limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def duneCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Dune finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(duneCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "[x y z world]")
    def commandHill(self, data):
        "Creates a hill between the two blocks you touched last."
        # If they only provided the type argument, use the last two block places
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
        if fromloc != "user" and len(data["parts"]) >= 7:
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
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x_range, z_range = x2 - x, z2 - z
        limit = data["client"].getBlbLimit()
        chrblocks = [chr(BLOCK_GRASS), chr(BLOCK_DIRT)]
        # Build the changeset
        chanegeset = {}
        for i in range(x, x2 + 1):
            for k in range(z, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                dy = int((dx ** 2 * dz ** 2) ** 0.2)
                for j in range(y, y + dy + 1):
                    if not (data["client"].allowedToBuild(x, y, z) or data["overriderank"]):
                        continue
                    changeset[i, j, k] = chrblocks[0] if j == y + dy else chrblocks[1]
        total = len(changeset.keys())
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Dune limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def hillCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Hill finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(hillCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "[x y z world]")
    def commandHole(self, data):
        "Creates a hole between two blocks."
        # If they only provided the type argument, use the last two block places
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
        if fromloc != "user" and len(data["parts"]) >= 7:
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
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x_range = x2 - x
        z_range = z2 - z
        limit = data["client"].getBlbLimit()
        block = chr(BLOCK_AIR)
        # Build the changeset
        chanegeset = {}
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                dy = int((dx ** 2 * dz ** 2) ** 0.3)
                for y in range(y1 - dy - 1, y1 + 1):
                    if (not (data["client"].allowedToBuild(x, y, z) or data["overriderank"])) or (y < 0):
                        continue
                    changeset[x, y, z] = block
        total = len(changeset.keys())
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Dune limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def holeCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Hole finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(holeCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "[x y z world]")
    def commandLake(self, data):
        "Creates a lake between two blocks."
        # If they only provided the type argument, use the last two block places
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
        if fromloc != "user" and len(data["parts"]) >= 7:
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
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x_range = x2 - x
        z_range = z2 - z
        limit = data["client"].getBlbLimit()
        block = chr(BLOCK_WATER)
        # Build the changeset
        chanegeset = {}
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                dy = int((dx ** 2 * dz ** 2) ** 0.3)
                for y in range(y1 - dy - 1, y1):
                    if not data["client"].allowedToBuild(x, y, z) and not data["overriderank"]:
                        continue
                    changeset[x, y, z] = block
        total = len(changeset.keys())
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Lake limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def lakeCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Lake finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(lakeCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname [x y z x2 y2 z2 world]")
    def commandMountain(self, data):
        "Creates a mountain between the two blocks you touched last."
        if fromloc == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 2:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, two coord triples and a world.")
                return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        if len(data["parts"]) == 2 and fromloc == "user":
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
        if fromloc != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
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
        x_range, z_range = x2 - x, z2 - z
        limit = data["client"].getBlbLimit()
        # Build the changeset
        chanegeset = {}
        for i in range(x, x2 + 1):
            for k in range(z, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                dy = int((dx ** 2 * dz ** 2) ** 0.3)
                for j in range(y, y + dy + 1):
                    if not (data["client"].allowedToBuild(i, j, k) or data["overriderank"]):
                        continue
                    changeset[i, j, k] = block
        total = len(changeset.keys())
        if limit != -1:
            if blocks > limit:
                data["client"].sendServerMessage("Mountain limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def mountainCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Mountain finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(mountainCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "[x y z x2 y2 z2 world]")
    def commandPit(self, data):
        "Creates a lava pit between two blocks."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 1:
                data["client"].sendServerMessage("Please enter a type (and possibly two coord triples)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter a type, two coord triples and a world.")
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
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x_range, z_range = x2 - x, z2 - z
        limit = data["client"].getBlbLimit()
        block = chr(BLOCK_LAVA)
        # Build the changeset
        chanegeset = {}
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                # Work out the height at this place
                dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                dy = int((dx ** 2 * dz ** 2) ** 0.3)
                for y in range(y1 - dy - 1, y1):
                    if not (data["client"].allowedToBuild(x, y, z) or data["overriderank"]):
                        continue
                    changeset[x, y, z] = block
        total = len(changeset.keys())
        if limit != -1:
            if total > limit:
                data["client"].sendServerMessage("Pit limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def pitCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Pit finished, with %s blocks changed." % total)
        self.factory.applyBlockChanges(changeset, w).addBoth(pitCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blockname repblock [x y z x2 y2 z2 world]")
    def commandFungus(self, data):
        "Funguses the area with the block."
        if data["fromloc"] == "user":
            if len(data["parts"]) < 9 and len(data["parts"]) != 3:
                data["client"].sendSplitServerMessage("Please enter a type and a type to replace (and possibly two coord triples)")
                data["client"].sendSplitServerMessage("""Note that you must place two blocks to use it. The first block sets where 
                to spread from and the second block sets which directions to spread.""")
                return
        else:
            if len(data["parts"]) < 10:
                data["client"].sendServerMessage("Please enter a type, a type to replace, two coord triples and a world.")
                data["client"].sendServerMessage("The first block sets where to spread from and the second block sets which directions to spread.")
                return
        repblock = chr(BLOCK_AIR)
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 2 and fromloc == "user":
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
                world = w
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
                return
            else:
                w = str(data["client"].world.id)
        xcheck, ycheck, zcheck = [(1, 0, 0), (-1, 0, 0)], [(0, 1, 0), (0, -1, 0)], [(0, 0, 1), (0, 0, -1)]
        checklist = []
        if x != x2: checklist += xcheck
        if y != y2: checklist += ycheck
        if z != z2: checklist += zcheck
        if checklist == []:
            data["client"].sendServerMessage("Repeated points error.")
            return
        var_blocklist = [(x, y, z, (x, y, z))]
        # Build the changeset
        changeset = {(x, y, z): block}
        blockchange = 0
        while var_blocklist != []:
            if blockchange > limit:
                data["client"].sendServerMessage("You have exceeded the fungus limit for your rank.")
                break
            i, j, k, positionprevious = var_blocklist[0]
            blockchange += 1
            for offsettuple in checklist:
                ia, ja, ka = offsettuple
                ri, rj, rk = i + ia, j + ja, k + ka
                if (ri, rj, rk) != positionprevious or (ri, rj, rk) == (x, y, z):
                    if not (data["client"].allowedToBuild(ri, rj, rk) or data["overriderank"]):
                        continue
                    checkblock = world.blockstore.raw_blocks[world.blockstore.get_offset(ri, rj, rk)]
                    if checkblock == repblock:
                        changeset[ri, rj, rk] = block
                        var_blocklist.append((ri, rj, rk, (i, j, k)))
            del var_blocklist[0]
        if limit != -1:
            if len(blockchange + 1) > limit:
                data["client"].sendServerMessage("Fungus limit exceeded. (Limit is %s)" % limit)
                return
        # Now, apply it.
        def fungusCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Fungus finished, with %s blocks changed." % blockchange + 1)
        self.factory.applyBlockChanges(changeset, w).addBoth(fungusCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype radius axis [x y z world]")
    def commandHCircle(self, data):
        "Creates a hollow circle."
        if fromloc == "user":
            if len(data["parts"]) < 7 and len(data["parts"]) != 4:
                data["client"].sendServerMessage("Please enter a type, a radius and an axis (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 8:
                data["client"].sendServerMessage("Please enter a type, a radius, an axis, a coord triples and a world.")
                return
        # Try getting the normal axis
        normalAxis = data["parts"][3].lower()
        if normalAxis not in ["x", "y", "z"]:
            data["client"].sendServerMessage("Normal axis must be x, y or z.")
            return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be an integer.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last two block places
        if len(data["parts"]) == 4 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
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
                world = w
        else:
            if fromloc != "user":
                data["client"].sendServerMessage("You must supply a world.")
                return
            else:
                w = str(data["client"].world.id)
        limit = data["client"].getBlbLimit()
        if limit != -1:
            if ((2 * cmath.pi * (radius ** 2)) - (2 * cmath.pi * ((radius - 1) ** 2)) > limit):
                data["client"].sendServerMessage("HCircle limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        changeset = {}
        for i in range(-radius - 1, radius):
            for j in range(-radius - 1, radius):
                for k in range(-radius - 1, radius):
                    if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 < radius) and ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 > radius - 1.208):
                        if not ((i != 0 and normalAxis == "x") or (j != 0 and normalAxis == "y") or (k != 0 and normalAxis == "z")):
                            if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                                continue
                            changeset[x + i, y + j, z + k] = block
        # Now, apply it.
        def hcircleCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("HCircle finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(hcircleCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype radius height axis [x y z world]")
    def commandHCylinder(self, data):
        "Creates a hollow cylinder."
        if fromloc == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 5:
                data["client"].sendServerMessage("Please enter a type, a radius, a height an axis (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, a radius, an axis, a coord triples and a world.")
                return
        # Try getting the normal axis
        normalAxis = data["parts"][4].lower()
        if normalAxis not in ["x", "y", "z"]:
            data["client"].sendServerMessage("Normal axis must be x, y, or z.")
            return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be an integer.")
            return
        # Try getting the height
        try:
            height = int(data["parts"][3])
        except ValueError:
            data["client"].sendServerMessage("Height must be an integer.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last block places
        if len(data["parts"]) == 5 and fromloc == "user":
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][5:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        if fromloc != "user" and len(data["parts"]) >= 9:
            w = data["parts"][8]
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
        limit = data["client"].getBlbLimit()
        if limit != -1:
            if (int((cmath.pi * (radius ** 2) * height) - (cmath.pi * ((radius - 1) ** 2) * height)) > limit):
                data["client"].sendServerMessage("HCylinder limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        def generate_changes(theX, axis):
            a = theX
            c = {}
            while theX < (height + a):
                for i in range(-radius - 1, radius):
                    for j in range(-radius - 1, radius):
                        for k in range(-radius - 1, radius):
                            if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 < radius) and ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 > (radius - 1.208)):
                                if not ((i != 0 and axis == "x") or (j != 0 and axis == "y") or (k != 0 and axis == "z")):
                                    if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                                        continue
                                    c[x + i, y + j, z + k] = block
                theX += 1
            return c

        if normalAxis == "x":
            changeset = generate_changes(x, "x")
        elif normalAxis == "y":
            changeset = generate_changes(y, "y")
        elif normalAxis == "z":
            changeset = generate_changes(z, "z")
        else:
            data["client"].sendServerMessage("Unknown axis error.")
        # Now, apply it.
        def hcylinderCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("HCylinder finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(hcylinderCallback)

    @config("category", "build")
    @config("rank", "op")
    @config("usage", "blocktype radius height axis [x y z world]")
    def commandCylinder(self, data):
        "Creates a cylinder."
        if fromloc == "user":
            if len(data["parts"]) < 8 and len(data["parts"]) != 5:
                data["client"].sendServerMessage("Please enter a type, a radius, a height an axis (and possibly a coord triple)")
                return
        else:
            if len(data["parts"]) < 9:
                data["client"].sendServerMessage("Please enter a type, a radius, an axis, a coord triples and a world.")
                return
        # Try getting the normal axis
        normalAxis = data["parts"][4].lower()
        if normalAxis not in ["x", "y", "z"]:
            data["client"].sendServerMessage("Normal axis must be x, y, or z.")
            return
        # Try getting the radius
        try:
            radius = int(data["parts"][2])
        except ValueError:
            data["client"].sendServerMessage("Radius must be an integer.")
            return
            # Try getting the height
        try:
            height = int(data["parts"][3])
        except ValueError:
            data["client"].sendServerMessage("Height must be an integer.")
            return
        block = data["client"].getBlockValue(data["parts"][1])
        if block == None:
            data["client"].sendServerMessage("'%s' is either not a valid block type, or is not available to you." % data["parts"][1])
            return
        # If they only provided the type argument, use the last block places
        if len(data["parts"]) == 5:
            try:
                x, y, z = data["client"].last_block_changes[0]
            except IndexError:
                data["client"].sendServerMessage("You have not clicked for a center yet.")
                return
        else:
            try:
                x, y, z = [int(i) for i in data["parts"][5:7]]
            except ValueError:
                data["client"].sendServerMessage("All coordinate parameters must be integers.")
                return
        limit = data["client"].getBlbLimit()
        if limit != -1:
            if (cmath.pi * (radius ** 2) * height > limit):
                data["client"].sendSplitServerMessage("Cylinder limit exceeded. (Limit is %s)" % limit)
                return
        # Build the changeset
        def generate_changes(theX, axis):
            a = theX
            c = {}
            while theX < (height + a):
                for i in range(-radius - 1, radius):
                    for j in range(-radius - 1, radius):
                        for k in range(-radius - 1, radius):
                            if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.604 < radius:
                                if not ((i != 0 and axis == "x") or (j != 0 and axis == "y") or (k != 0 and axis == "z")):
                                    if not (data["client"].allowedToBuild(x + i, y + j, z + k) or data["overriderank"]):
                                        continue
                                    c[x + i, y + j, z + k] = block
                theX += 1
            return c

        if normalAxis == "x":
            changeset = generate_changes(x, "x")
        elif normalAxis == "y":
            changeset = generate_changes(y, "y")
        elif normalAxis == "z":
            changeset = generate_changes(z, "z")
        else:
            data["client"].sendServerMessage("Unknown axis error.")
        # Now, apply it.
        def cylinderCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Cylinder finished, with %s blocks changed." % len(changeset.keys()))
        self.factory.applyBlockChanges(changeset, w).addBoth(cylinderCallback)

serverPlugin = BuildLibPlugin