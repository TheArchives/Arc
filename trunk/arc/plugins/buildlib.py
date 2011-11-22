# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cmath, random

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class BuildLibPlugin(ProtocolPlugin):

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
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }

    TRUNK_HEIGHT = 5, 9
    FANOUT = 3, 5

    def gotClient(self):
        self.build_trees = False

    def newWorld(self, world):
        "Hook to reset dynamiting abilities in new worlds if not op."
        if not self.client.isBuilder():
            self.build_trees = False

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if self.build_trees:
            tobuild = []
            # Randomise the variables
            trunk_height = random.randint(*self.TRUNK_HEIGHT)
            fanout = random.randint(*self.FANOUT)
            if self.build_trees and block == BLOCK_PLANT:
                # Build the main tree bit
                for i in range(-fanout-1, fanout):
                    for j in range(-fanout-1, fanout):
                        for k in range(-fanout-1, fanout):
                            if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                return
                            if (i ** 2 + j ** 2 + k ** 2)**0.5 < fanout:
                                tobuild.append((i, j + trunk_height, k, BLOCK_LEAVES))
                # Build the trunk
                for i in range(trunk_height):
                    tobuild.append((0, i, 0, BLOCK_LOG))
                # OK, send the build changes
                for dx, dy, dz, block in tobuild:
                    try:
                        self.client.world[x+dx, y+dy, z+dz] = chr(block)
                        self.client.sendBlock(x+dx, y+dy, z+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                    except AssertionError:
                        pass
                return True

    @config("category", "build")
    @config("rank", "builder")
    def commandSphere(self, parts, fromloc, overriderank):
        "/sphere blocktype radius [x y z] - Builder\nPlace/delete a block and /sphere block radius"
        if len(parts) < 6 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((radius * 2) ** 3 > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to sphere (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(-radius-1, radius):
                        for j in range(-radius-1, radius):
                            for k in range(-radius-1, radius):
                                if (i ** 2 + j ** 2 + k ** 2) ** 0.5 < radius:
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                        return
                                    world[x+i, y+j, z+k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                    yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds sphere error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your sphere just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandHSphere(self, parts, fromloc, overriderank):
        "/hsphere blocktype radius [x y z] - Builder\nPlace/delete a block, makes a hollow /sphere"
        if len(parts) < 6 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            # TODO: Fix the formula
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if (((radius * 2) ** 3) - (((radius - 1) * 2) ** 3) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to hsphere (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(-radius-1, radius):
                        for j in range(-radius-1, radius):
                            for k in range(-radius-1, radius):
                                if (i ** 2 + j ** 2 + k ** 2) ** 0.5 < radius and (i ** 2 + j ** 2 + k ** 2) ** 0.5 > (radius - 1.49):
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                        return
                                    world[x+i, y+j, z+k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                    yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds sphere error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your hsphere just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandCurve(self, parts, fromloc, overriderank):
        "/curve blockname [x y z x2 y2 z2 x3 y3 z3] - Builder\nSets a line of blocks along three points to block."
        if len(parts) < 11 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly three coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                    x3, y3, z3 = self.client.last_block_changes[2]
                except:
                    self.client.sendServerMessage("You have not clicked 3 points yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                    x3 = int(parts[8])
                    y3 = int(parts[9])
                    z3 = int(parts[10])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                estimatedBlocks = (2 * ((x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2) ** 0.5 + 2 * ((x2 - x3) ** 2 + (y2 - y3) ** 2 + (z2 - z3) ** 2) ** 0.5)
                if (estimatedBlocks > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to curve (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    # curve list
                    steps1 = float(2 * ((x3 - x) ** 2 + (y3 - y) ** 2 + (z3 - z) ** 2) ** 0.5)
                    steps2 = float(2 * ((x2 - x3) ** 2 + (y2 - y3) ** 2+ (z2 - z3) ** 2) ** 0.5) + steps1
                    coordinatelist = []
                    def calcCoord(x, x2, t, steps1, steps2):
                        return (x2 - x) * ((t) / (steps1) * (t - steps2) / (steps1 - steps2)) + (x2 - x) * ((t) / (steps2) * (t - steps1) / (steps2 - steps1))
                    for i in range(steps2+1):
                        t = float(i)
                        var_x = calcCoord(x, x2, t, steps1, steps2)
                        var_y = calcCoord(y, y2, t, steps1, steps2)
                        var_z = calcCoord(z, z2, t, steps1, steps2)
                        coordinatelist.append((int(var_x) + x, int(var_y) + y, int(var_z) + z))
                    finalcoordinatelist = [coordtuple for coordtuple in coordinatelist if coordtuple not in finalcoordinatelist]
                    for coordtuple in finalcoordinatelist:
                        i = coordtuple[0]
                        j = coordtuple[1]
                        k = coordtuple[2]
                        if not self.client.AllowedToBuild(i, j, k):
                            return
                        world[i, j, k] = block
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds curve error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your curve just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandPyramid(self, parts, fromloc, overriderank):
        "/pyramid blockname height fill [x y z] - Op\nSets all blocks in this area to be a pyramid."
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a block type height and fill?")
        else:
            # Try getting the fill
            fill = parts[3]
            if fill in ["true", "false"]:
                pass
            else:
                self.client.sendServerMessage("Fill must be true or false.")
                return
            # Try getting the height
            try:
                height = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Height must be a number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            # Stop them doing silly things
            if limit != -1:
                if int(((x * y) * (z)) / 3 > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to pyramid. (Limit is %s)" % limit)
                    return
            pointlist = []
            for i in range(abs(height)):
                they = y + ((height - i - 1) if height > 0 else (height + i + 1))
                if height > 0:
                    point1 = [x - i, they, z - i]
                    point2 = [x + i, they, z + i]
                else:
                    point1 = [x - i, they, z - i]
                    point2 = [x + i, they, z + i]
                pointlist = pointlist + [(point1, point2)]
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for pointtouple in pointlist:
                        x, y, z = pointtouple[0]
                        x2, y2, z2 = pointtouple[1]
                        for i in range(x, x2+1):
                            for j in range(y, y2+1):
                                for k in range(z, z2+1):
                                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                        return
                                    if fill == "true" or (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or \
                                    (i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or (i == x and k == z2) or \
                                    (j == y and k == z2) or (i == x2 and k == z) or (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                                        world[i, j, k] = block
                                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                        self.client.sendBlock(i, j, k, block)
                                        yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds pyramid error.")
                    return

            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your pyramid just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandLine(self, parts, fromloc, overriderank):
        "/line blockname [x y z x2 y2 z2] - Op\nSets all blocks between two points to be a line."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            steps = int(((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5)
            if steps == 0:
                self.client.sendServerMessage("Your line need to be longer.")
                return
            mx = float(x2 - x) / steps
            my = float(y2 - y) / steps
            mz = float(z2 - z) / steps
            coordinatelist1 = []
            for t in range(steps+1):
                coordinatelist1.append((int(round(mx * t + x)), int(round(my * t + y)), int(round(mz * t + z))))
            coordinatelist2 = [coordtuple for coordtuple in coordinatelist1 if coordtuple not in coordinatelist2]
            limit = self.client.getBlbLimit()
            if limit != -1:
            # Stop them doing silly things
                if len(coordinatelist2) > limit or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to line (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for coordtuple in coordinatelist2:
                        i = coordtuple[0]
                        j = coordtuple[1]
                        k = coordtuple[2]
                        if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                            return
                        world[i, j, k] = block
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds line error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your line just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandCsphere(self, parts, fromloc, overriderank):
        "/csphere blocktype blocktype radius [x y z] - Op\nPlace/delete a block and /csphere block radius"
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter two types a radius (and possibly a coord triple)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[3])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            block2 = self.client.GetBlockValue(parts[2])
            if block == None or block2 == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            # TODO: Fix the formula
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((radius * 2) ** 3 > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to csphere (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                ticker = 0
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < radius:
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                    self.client.sendServerMessage("You do not have permision to build here.")
                                    return
                                try:
                                    if (i + j + k) % 2 == 0:
                                        ticker = 1
                                    else:
                                        ticker = 0
                                    if ticker == 0:
                                        world[x+i, y+j, z+k] = block
                                    else:
                                        world[x+i, y+j, z+k] = block2
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds sphere error.")
                                    return
                                if ticker == 0:
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block2), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block2)
                                else:
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your csphere just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandCircle(self, parts, fromloc, overriderank):
        "/circle blocktype radius axis [x y z] - Op\nPlace/delete a block and /circle block radius axis"
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a type, radius, axis (and possibly a coord triple)")
        else:
            # Try getting the normal axis
            normalAxis = parts[3].lower()
            if normalAxis not in ["x", "y", "z"]:
                self.client.sendServerMessage("Normal axis must be x, y, or z.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if (int(2 * cmath.pi * (radius) ** 2) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to circle (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(-radius-1, radius):
                        for j in range(-radius-1, radius):
                            for k in range(-radius-1, radius):
                                if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.604 < radius:
                                    # Test for axis
                                    if not ((i != 0 and normalAxis == 'x') or (j != 0 and normalAxis == 'y') or (k != 0 and normalAxis == 'z')):
                                        if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                            self.client.sendServerMessage("You do not have permission to build here.")
                                            return
                                        world[x+i, y+j, z+k] = block
                                        self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                        self.client.sendBlock(x+i, y+j, z+k, block)
                                        yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds circle error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your circle just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandDome(self, parts, fromloc, overriderank):
        "/dome blocktype radius fill [x y z] - Op\nPlace/delete a block and /sphere block radius"
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a type radius and fill?(and possibly a coord triple)")
        else:
            # Try getting the fill
            fill = parts[3]
            if fill in ["true", "false"]:
                pass
            else:
                self.client.sendServerMessage("Fill must be true or false.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            absradius = abs(radius)
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((radius * 2) ** 3 / 2 > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to dome (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-absradius-1, absradius):
                    for j in range(-absradius-1, absradius):
                        for k in range(-absradius-1, absradius):
                            if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < absradius and ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill == "true") or \
                            (absradius - 1 < (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.691 < absradius and ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill== "false"):
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                    self.client.sendServerMessage("You do not have permision to build here.")
                                    return
                                try:
                                    world[x+i, y+j, z+k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds dome error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your dome just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandEllipsoid(self, parts, fromloc, overriderank):
        "/ellipsoid blocktype endradius [x y z x2 y2 z2] - Op\nAliases: ell\nPlace/delete two blocks and block endradius"
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type endradius (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                endradius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Endradius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two points yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            radius = int(round(endradius * 2 + ((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5) / 2 + 1)
            var_x = int(round(float(x + x2) / 2))
            var_y = int(round(float(y + y2) / 2))
            var_z = int(round(float(z + z2) / 2))
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if (int(4/3 * cmath.pi * radius ** 2 * endradius) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to ellipsoid (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(-radius-2, radius+1):
                        for j in range(-radius-2, radius+1):
                            for k in range(-radius-2, radius+1):
                                if (((i+ var_x - x) ** 2 + (j + var_y - y) ** 2 + (k + var_z - z) ** 2) ** 0.5 + ((i + var_x - x2) ** 2 + (j + var_y - y2) ** 2 + (k + var_z - z2) ** 2) ** 0.5) / 2 + 0.691 < radius:
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                        self.client.sendServerMessage("You do not have permision to build here.")
                                        return
                                    world[var_x+i, var_y+j, var_z+k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (var_x+i, var_y+j, var_z+k, block), world=world)
                                    self.client.sendBlock(var_x+i, var_y+j, var_z+k, block)
                                    yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds ellipsoid error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your ellipsoid just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandPolytri(self, parts, fromloc, overriderank):
        "/polytri blockname [x y z x2 y2 z2 x3 y3 z3] - Op\nSets all blocks between three points to block."
        if len(parts) < 11 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly three coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                    x3, y3, z3 = self.client.last_block_changes[2]
                except:
                    self.client.sendServerMessage("You have not clicked 3 points yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                    x3 = int(parts[8])
                    y3 = int(parts[9])
                    z3 = int(parts[10])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((((x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2) ** 0.5 * ((x - x3) ** 2 + (y - y3) ** 2 + (z - z3) ** 2) ** 0.5) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to polytri (Limit is %s)" % limit)
                    return
            def calcStep(x, x2, y, y2, z, z2):
                return int(((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2) ** 0.5 / 0.75)
            # line 1 list
            steps = []
            steps[0] = calcStep(x, x2, y, y2, z, z2)
            mx = float(x2 - x) / steps
            my = float(y2 - y) / steps
            mz = float(z2 - z) / steps
            coordinatelist2 = []
            for t in range(steps[0]+1):
                coordinatelist2.append((mx * t + x, my * t + y, mz * t + z))
            # line 2 list
            steps[1] = calcStep(x, x3, y, y3, z, z3)
            mx = float(x3 - x) / steps
            my = float(y3 - y) / steps
            mz = float(z3 - z) / steps
            coordinatelist3 = []
            for t in range(steps[1]+1):
                coordinatelist3.append((mx * t + x, my * t + y, mz * t + z))
            # final coordinate list
            if len(coordinatelist2) > len(coordinatelist3):
                coordinatelistA = coordinatelist2
                coordinatelistB = coordinatelist3
            else:
                coordinatelistA = coordinatelist3
                coordinatelistB = coordinatelist2
            lenofA = len(coordinatelistA)
            listlenRatio = float(len(coordinatelistB)) / lenofA
            finalcoordinatelist = []
            for i in range(lenofA):
                point1 = coordinatelistA[i]
                point2 = coordinatelistB[int(i * listlenRatio)]
                var_x = point1[0]
                var_y = point1[1]
                var_z = point1[2]
                var_x2 = point2[0]
                var_y2 = point2[1]
                var_z2 = point2[2]
                steps = calcStep(var_x, var_x2, var_y, var_y2, var_z, var_z2)
                if steps != 0:
                    mx = float(var_x2 - var_x) / steps
                    my = float(var_y2 - var_y) / steps
                    mz = float(var_z2 - var_z) / steps
                    coordinatelist = []
                    for t in range(steps+1):
                        coordinatelist.append((int(round(mx * t + var_x)), int(round(my * t + var_y)), int(round(mz * t + var_z))))
                    for coordtuple in coordinatelist:
                        if coordtuple not in finalcoordinatelist:
                            finalcoordinatelist.append(coordtuple)
                elif point1 not in finalcoordinatelist:
                    finalcoordinatelist.append(point1)
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for coordtuple in finalcoordinatelist:
                    i = int(coordtuple[0])
                    j = int(coordtuple[1])
                    k = int(coordtuple[2])
                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                        self.client.sendServerMessage("You do not have permision to build here.")
                        return
                    try:
                        world[i, j, k] = block
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds polytri error.")
                        return
                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                    self.client.sendBlock(i, j, k, block)
                    yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your polytri just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandStairs(self, parts, fromloc, overriderank):
        "/stairs blockname height [orientation] [x y z x2 y2 z2] - Builder\nBuilds a spiral staircase.\nOrientation: a = anti-clockwise, c = clockwise"
        if len(parts) < 9 and len(parts) != 3 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a blocktype height (c (for counter-clockwise)")
            self.client.sendServerMessage("(and possibly two coord triples)")
            self.client.sendServerMessage("If the two points are on the 'ground' adjacent to each other, then")
            self.client.sendServerMessage("the second point will spawn the staircase and the first will")
            self.client.sendServerMessage("be used for the initial orientation")
        else:
            # Try getting the counter-clockwise flag
            if parts[3].lower() == "a":
                counterflag = 1
            elif parts[3].lower() == "c":
                counterflag = -1
            else:
                self.client.sendServerMessage("The third entry must be a for anti-clockwise or c for clockwise.")
                return
            try:
                height = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("The height must be an integer")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                    x2 = int(parts[7])
                    y2 = int(parts[8])
                    z2 = int(parts[9])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if (height * 4 > limit) or limit == 0:
                    self.client.sendSplitServerMessage("Sorry, that area is too big for you to make stairs (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                if abs(x - x2) + abs(z - z2) == 1:
                    if x - x2 == -1:
                        orientation = 1
                    elif z - z2 == -1:
                        orientation = 2
                    elif x - x2 == 1:
                        orientation = 3
                    else:
                        orientation = 4
                else:
                    orientation = 1
                if height >= 0:
                    heightsign = 1
                else:
                    heightsign = -1
                stepblock = chr(BLOCK_STEP)
                for h in range(abs(height)):
                    locy = y + h * heightsign
                    combo = [(x, locy, z), (x + 1, locy, z + 1), (x + 1, locy, z), (x + 1, locy, z - 1), \
                        (x - 1, locy, z + 1), (x, locy, z + 1), (x - 1, locy, z - 1), (x - 1, locy, z), (x, locy, z - 1)]
                    if orientation == 1:
                        c1 = [combo[1], combo[2], combo[3]]
                    elif orientation == 2:
                        c1 = [combo[4], combo[5], combo[2]]
                    elif orientation == 3:
                        c1 = [combo[6], combo[7], combo[3]]
                    elif orientation == 4:
                        c1 = [combo[3], combo[8], combo[6]]
                    if counterflag == 1:
                        c1.reverse()
                    blocklist = [combo[0]] + c1
                    orientation = orientation - heightsign * counterflag
                    if orientation > 4:
                        orientation = 1
                    if orientation < 1:
                        orientation = 4
                    for entry in blocklist:
                        i, j, k = entry
                        if not self.client.AllowedToBuild(i, j, k):
                            return
                    for entry in blocklist[:3]:
                        i, j, k = entry
                        try:
                            world[i, j, k] = block
                        except AssertionError:
                            self.client.sendServerMessage("Out of bounds stairs error.")
                            return
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
                        i, j, k = blocklist[3]
                        try:
                            world[i, j, k] = stepblock
                        except AssertionError:
                            self.client.sendServerMessage("Out of bounds stairs error.")
                            return
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, stepblock), world=world)
                        self.client.sendBlock(i, j, k, stepblock)
                        yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long (in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your stairs just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    @on_off_command
    def commandTree(self, onoff, fromloc, overriderank):
        "/tree on|off - Builder\nBuilds trees, save the earth!"
        if onoff == "on":
            self.build_trees = True
            self.client.sendServerMessage("You are now building trees; place a plant!")
        else:
            self.build_trees = False
            self.client.sendServerMessage("You are no longer building trees.")

    @config("category", "build")
    @config("rank", "op")
    def commandDune(self, parts, fromloc, overriderank):
        "/dune - Op\nCreates a sand dune between the two blocks you touched last."
        # Use the last two block places
        try:
            x, y, z = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet.")
            return
        if x > x2:
            x, x2 = x2, x
        if y > y2:
            y, y2 = y2, y
        if z > z2:
            z, z2 = z2, z
        x_range = x2 - x
        z_range = z2 - z
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        # Draw all the blocks on, I guess
        # We use a generator so we can slowly release the blocks
        # We also keep world as a local so they can't change worlds and affect the new one
        world = self.client.world
        def generate_changes():
            for i in range(x, x2+1):
                for k in range(z, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                    dy = int((dx ** 2 * dz ** 2) ** 0.2)
                    for j in range(y, y+dy+1):
                        if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                            return
                        block = BLOCK_SAND
                        try:
                            world[i, j, k] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your dune just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandHill(self, parts, fromloc, overriderank):
        "/hill - Op\nCreates a hill between the two blocks you touched last."
        # Use the last two block places
        try:
            x, y, z = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet.")
            return
        if x > x2:
            x, x2 = x2, x
        if y > y2:
            y, y2 = y2, y
        if z > z2:
            z, z2 = z2, z
        x_range = x2 - x
        z_range = z2 - z
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        # Draw all the blocks on, I guess
        # We use a generator so we can slowly release the blocks
        # We also keep world as a local so they can't change worlds and affect the new one
        world = self.client.world
        def generate_changes():
            for i in range(x, x2+1):
                for k in range(z, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                    dy = int((dx ** 2 * dz ** 2) ** 0.2)
                    for j in range(y, y+dy+1):
                        if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                            return
                        block = BLOCK_GRASS if j == y+dy else BLOCK_DIRT
                        try:
                            world[i, j, k] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your hill just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandHole(self, parts, fromloc, overriderank):
        "/hole - Op\nCreates a hole between two blocks."
        # Use the last two block places
        try:
            x1, y1, z1 = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet.")
            return
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if z1 > z2:
            z1, z2 = z2, z1
        x_range = x2 - x1
        z_range = z2 - z1
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        block = BLOCK_AIR
        world = self.client.world
        def generate_changes():
            for x in range(x1, x2+1):
                for z in range(z1, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                    dy = int((dx ** 2 * dz ** 2) ** 0.3)
                    for y in range(y1-dy-1, y1+1):
                        if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                            return
                        if y < 0:
                            continue
                        try:
                            world[x, y, z] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                        self.client.sendBlock(x, y, z, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your hole just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandLake(self, parts, fromloc, overriderank):
        "/lake - Op\ncreates a lake between two blocks"
        # Use the last two block places
        try:
            x1, y1, z1 = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet")
            return
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if z1 > z2:
            z1, z2 = z2, z1
        x_range = x2 - x1
        z_range = z2 - z1
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        block = BLOCK_WATER
        world = self.client.world
        def generate_changes():
            for x in range(x1, x2+1):
                for z in range(z1, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                    dy = int((dx ** 2 * dz ** 2) ** 0.3)
                    for y in range(y1-dy-1, y1):
                        if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                            return
                        try:
                            world[x, y, z] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world = world)
                        self.client.sendBlock(x, y, z, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your lake just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandMountain(self, parts, fromloc, overriderank):
        "/mountain blockname - Op\nCreates a mountain between the two blocks you touched last."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type.")
            return
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
        if x > x2:
            x, x2 = x2, x
        if y > y2:
            y, y2 = y2, y
        if z > z2:
            z, z2 = z2, z
        x_range = x2 - x
        z_range = z2 - z
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        # Draw all the blocks on, I guess
        # We use a generator so we can slowly release the blocks
        # We also keep world as a local so they can't change worlds and affect the new one
        world = self.client.world
        def generate_changes():
            for i in range(x, x2+1):
                for k in range(z, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
                    dy = int((dx ** 2 * dz ** 2) ** 0.3)
                    for j in range(y, y+dy+1):
                        if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                            return
                        try:
                            world[i, j, k] = block
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                        self.client.sendBlock(i, j, k, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your mountain just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandPit(self, parts, fromloc, overriderank):
        "/pit - Op\nCreates a lava pit between two blocks."
        # Use the last two block places
        try:
            x1, y1, z1 = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two corners yet.")
            return
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if z1 > z2:
            z1, z2 = z2, z1
        x_range = x2 - x1
        z_range = z2 - z1
        if self.client.getBlbLimit() == 0:
            self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
            return
        block = BLOCK_LAVA
        world = self.client.world
        def generate_changes():
            for x in range(x1, x2+1):
                for z in range(z1, z2+1):
                    # Work out the height at this place
                    dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
                    dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
                    dy = int((dx ** 2 * dz ** 2) ** 0.3)
                    for y in range(y1-dy-1, y1):
                        if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                            return
                        try:
                            world[x, y, z] = chr(block)
                        except AssertionError:
                            pass
                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world = world)
                        self.client.sendBlock(x, y, z, block)
                        yield
        # Now, set up a loop delayed by the reactor
        block_iter = iter(generate_changes())
        def do_step():
            # Do 10 blocks
            try:
                for x in range(10):
                    block_iter.next()
                reactor.callLater(0.01, do_step)
            except StopIteration:
                if fromloc == "user":
                    self.client.sendServerMessage("Your pit just completed.")
                pass
        do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandFungus(self, parts, fromloc, overriderank):
        "/fungus blockname repblock [x y z x2 y2 z2] - Op\nFunguses the area with the block."
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendSplitServerMessage("Please enter a type and a type to replace (and possibly two coord triples)")
            self.client.sendSplitServerMessage("Note that you must place two blocks to use it. The first block sets where to spread from and the second block sets which directions to spread.")
        else:
            var_repblock = chr(0)
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last block place
            if len(parts) == 3:
                try:
                    x = self.client.world.x / 2
                    y = self.client.world.y / 2
                    z = self.client.world.z / 2
                    x, y, z = x, y, z
                    x2, y2, z2 = 0, 0, 0
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two points yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit == 0:
                self.client.sendServerMessage("Your BLB limit is zero, therefore you cannot use this command.")
                return
            var_locxchecklist = [(1, 0, 0), (-1, 0, 0)]
            var_locychecklist = [(0, 1, 0), (0, -1, 0)]
            var_loczchecklist = [(0, 0, 1), (0, 0, -1)]
            var_locchecklist = []
            if x != x2:
                var_locchecklist = var_locchecklist + var_locxchecklist
            if y != y2:
                var_locchecklist = var_locchecklist + var_locychecklist
            if z != z2:
                var_locchecklist = var_locchecklist + var_loczchecklist
            if var_locchecklist == []:
                self.client.sendServerMessage("Repeated points error.")
                return
            self.var_blocklist = [(x, y, z, (-20, -20, -20))]
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            try:
                if not self.client.AllowedToBuild(x, y, z):
                    self.client.sendServerMessage("You do not have permission to build here.")
                    return
                world[x, y, z] = block
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                self.client.sendBlock(x, y, z, block)
            except:
                pass
            def generate_changes():
                var_blockchanges = 0
                while self.var_blocklist != []:
                    if var_blockchanges > limit:
                        self.client.sendServerMessage("You have exceeded the fungus limit for your rank.")
                        return
                    i, j, k, positionprevious = self.var_blocklist[0]
                    var_blockchanges += 1
                    for offsettuple in var_locchecklist:
                        ia, ja, ka = offsettuple
                        ri, rj, rk = i + ia, j + ja, k + ka
                        if (ri,rj,rk) != positionprevious:
                            try:
                                if not self.client.AllowedToBuild(ri, rj, rk):
                                    self.client.sendServerMessage("You do not have permission to build here.")
                                    return
                                checkblock = world.blockstore.raw_blocks[world.blockstore.get_offset(ri, rj, rk)]
                                if checkblock == var_repblock:
                                    world[ri, rj, rk] = block
                                    self.client.queueTask(TASK_BLOCKSET, (ri, rj, rk, block), world=world)
                                    self.client.sendBlock(ri, rj, rk, block)
                                    self.var_blocklist.append((ri, rj, rk, (i, j, k)))
                            except AssertionError:
                                pass
                            yield
                    del self.var_blocklist[0]
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(7): # 70 blocks per tenths of a second, 700 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  # This is how long (in seconds) it waits to run another 0.7 blocks
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your fungus just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandHCircle(self, parts, fromloc, overriderank):
        "/hcircle blocktype radius axis [x y z] - Op\nCreates a hollow circle."
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a type, radius, axis (and possibly a coord triple)")
        else:
            # Try getting the normal axis
            normalAxis = parts[3].lower()
            if normalAxis not in ["x", "y", "z"]:
                self.client.sendServerMessage("Normal axis must be x, y or z.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be an integer.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                if (int((2 * cmath.pi * (radius ** 2)) - (2 * cmath.pi * ((radius - 1) ** 2))) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to hcircle.")
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 < radius) and ((i**2 + j**2 + k**2)**0.5 + .604 > radius - 1.208):
                                if not ((i != 0 and normalAxis == "x") or (j != 0 and normalAxis == "y") or (k != 0 and normalAxis == "z")):
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                        self.client.sendServerMessage("You do not have permission to build here.")
                                        return
                                    try:
                                        world[x+i, y+j, z+k] = block
                                    except AssertionError:
                                        self.client.sendServerMessage("Out of bounds hcircle error.")
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                    yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your hcircle just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandHCylinder(self, parts, fromloc, overriderank):
        "/hcyl blocktype radius height axis [x y z] - Op\nCreates a hollow cylinder."
        if len(parts) < 8 and len(parts) != 5:
            self.client.sendServerMessage("Please enter a type, radius, height, axis (and possibly a coord triple)")
        else:
            # Try getting the normal axis
            normalAxis = parts[4].lower()
            if normalAxis not in ["x", "y", "z"]:
                self.client.sendServerMessage("Normal axis must be x, y, or z.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be an integer.")
                return
            # Try getting the height
            try:
                height = int(parts[3])
            except ValueError:
                self.client.sendServerMessage("Height must be an integer.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last block places
            if len(parts) == 5:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[5])
                    y = int(parts[6])
                    z = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                if (int((cmath.pi * (radius ** 2) * height) - (cmath.pi * ((radius - 1) ** 2) * height)) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to hcyl.")
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes(theX, axis):
                a = theX
                while theX < (height + a):
                    for i in range(-radius-1, radius):
                        for j in range(-radius-1, radius):
                            for k in range(-radius-1, radius):
                                if ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 < radius) and ((i ** 2 + j ** 2 + k ** 2) ** 0.5 + .604 > (radius - 1.208)):
                                    if not ((i != 0 and axis == "x") or (j != 0 and axis == "y") or (k != 0 and axis == "z")):
                                        if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                            self.client.sendServerMessage("You do not have permission to build here.")
                                            return
                                        try:
                                            world[x+i, y+j, z+k] = block
                                        except AssertionError:
                                            self.client.sendServerMessage("Out of bounds hcyl error.")
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                        self.client.sendBlock(x+i, y+j, z+k, block)
                                        yield
                    theX += 1
            if normalAxis == "x":
                block_iter = iter(generate_changes(x, "x"))
            elif normalAxis == "y":
                block_iter = iter(generate_changes(y, "y"))
            elif normalAxis == "z":
                block_iter = iter(generate_changes(z, "z"))
            else:
                self.client.sendServerMessage("Unknown axis error.")
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your hcyl just completed.")
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandCylinder(self, parts, fromloc, overriderank):
        "/cyl blocktype radius height axis [x y z] - Op\nAliases: cylinder\nCreates a cylinder."
        if len(parts) < 8 and len(parts) != 5:
            self.client.sendServerMessage("Please enter a type, radius, height, axis (and possibly a coord triple)")
        else:
            # Try getting the normal axis
            normalAxis = parts[4].lower()
            if normalAxis not in ["x", "y", "z"]:
                self.client.sendServerMessage("Normal axis must be x, y, or z.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be an integer.")
                return
            # Try getting the height
            try:
                height = int(parts[3])
            except ValueError:
                self.client.sendServerMessage("Height must be an integer.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last block places
            if len(parts) == 5:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[5])
                    y = int(parts[6])
                    z = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit != -1:
                if (cmath.pi * (radius ** 2) * height > limit) or limit == 0:
                    self.client.sendSplitServerMessage("Sorry, that area is too big for you to make a cylinder. (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes(theX, axis):
                a = theX
                while theX < (height + a):
                    for i in range(-radius-1, radius):
                        for j in range(-radius-1, radius):
                            for k in range(-radius-1, radius):
                                if (i ** 2 + j ** 2 + k ** 2) ** 0.5 + 0.604 < radius:
                                    if not ((i != 0 and axis == "x") or (j != 0 and axis == "y") or (k != 0 and axis == "z")):
                                        if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                            self.client.sendServerMessage("You do not have permission to build here.")
                                            return
                                        try:
                                            world[x+i, y+j, z+k] = block
                                        except AssertionError:
                                            self.client.sendServerMessage("Out of bounds hcyl error.")
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                        self.client.sendBlock(x+i, y+j, z+k, block)
                                        yield
                    theX += 1
            if normalAxis == "x":
                block_iter = iter(generate_changes(x, "x"))
            elif normalAxis == "y":
                block_iter = iter(generate_changes(y, "y"))
            elif normalAxis == "z":
                block_iter = iter(generate_changes(z, "z"))
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("Your cylinder just completed.")
                    pass
            do_step()