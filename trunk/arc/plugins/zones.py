# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

class ZonesPlugin(object):
    commands = {
        "znew": "commandNewZone",
        "zone": "commandZone",
        "zones": "commandZones",
        "zlist": "commandListZones",
        "zshow": "commandZshow",
        "zremove": "commandZoneRemove",
        "zclear": "commandClearZone",
        "zdelall": "commandZDelAll",
        "zwho": "commandZoneWho",
        "zrename": "commandZRename",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "consoleLoaded": "gotConsole"
    }

    def gotClient(self, data):
        # Register this check
        def inZone(self, zone):
            x, y, z = self.last_block_changes[0]
            x1, y1, z1, x2, y2, z2 = zone[1:]
            if x1 < x < x2:
                if y1 < y < y2:
                    if z1 < z < z2:
                        return True
            return False
        data["client"].inZone = inZone

    def gotConsole(self):
        def inZone(self, zone):
            return False
        self.factory.console.inZone = inZone

    @config("rank", "op")
    @config("usage", "on|off")
    @on_off_command
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandZones(self, data):
        "Enables or disables building zones in this world."
        if data["onoff"] == "on":
            data["client"].world.status["zoned"] = True
            data["client"].sendWorldMessage("This world now has building zones enabled.")
        else:
            data["client"].world.status["zoned"] = False
            data["client"].sendWorldMessage("This world now has building zones disabled.")
        data["client"].world.status["modified"] = True

    @config("rank", "op")
    @config("usage", "zonename user|rank [owner/rankname]")
    @config("aliases", ["rbox"])
    @config("disabled-on", ["irc", "irc_query", "console"])
    def commandNewZone(self, data):
        "Creates a new zone with the name.\nUsers are added with /zone name user1 user2 ...\nRank Example: '/znew GuestArea rank all'\nUser Example: '/znew hotel user'. then '/zone hotel add user1 [user2]'"
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("Info missing. Usage - /znew name user|rank [rank]")
            return
        try:
            if not data["client"].world.status["zoned"] and not data["parts"][3].lower() == "all":
                data["client"].sendServerMessage("Zones must be turned on to use except for an 'all' ranked zone.")
                return
        except IndexError:
            if not data["client"].world.status["zoned"]:
                data["client"].sendServerMessage("Zones must be turned on to use except for an 'all' ranked zone.")
                return
        for id, zone in data["client"].world.userzones.items():
            if zone[0] == data["parts"][1]:
                data["client"].sendServerMessage("Zone %s already exists. Pick a new name." % data["parts"][1])
                return
        for id, zone in data["client"].world.rankzones.items():
            if zone[0] == data["parts"][1]:
                data["client"].sendServerMessage("Zone %s already exists. Pick a new name." % data["parts"][1])
                return
        try:
            x, y, z = data["client"].last_block_changes[0]
            x2, y2, z2 = data["client"].last_block_changes[1]
        except IndexError:
            data["client"].sendServerMessage("You have not clicked two corners yet.")
            return
        world = data["client"].world
        if x > x2: x, x2 = x2, x
        if y > y2: y, y2 = y2, y
        if z > z2: z, z2 = z2, z
        x -= 1
        y -= 1
        z -= 1
        x2 += 1
        y2 += 1
        z2 += 1
        if data["parts"][2].lower() == "rank":
            if len(data["parts"]) < 4:
                data["client"].sendServerMessage("Info missing. Usage - /znew name rank [rank]")
                return
            if data["parts"][3].lower() in ["all", "builder", "op", "worldowner", "helper", "mod", "admin", "director", "owner"]:
                i = 1
                while True:
                    if not i in data["client"].world.rankzones:
                        data["client"].world.rankzones[i] = data["parts"][1].lower(), x, y, z, x2, y2, z2, data["parts"][3].lower()
                        break
                    else:
                        i += 1
                data["client"].sendServerMessage("Zone %s for rank %s has been created." % (data["parts"][1].lower(), data["parts"][3].lower()))
            else:
                data["client"].sendServerMessage("You must provide a proper rank.")
                data["client"].sendSplitServerMessage("all | builder | op | worldowner | helper |mod | admin | director | owner")
                return
        elif data["parts"][2].lower() == "user":
            i = 1
            while True:
                if len(data["parts"]) == 4:
                    owner = data["parts"][3]
                else:
                    owner = data["client"].username
                if not i in data["client"].world.userzones:
                    data["client"].world.userzones[i] = [data["parts"][1].lower(), x, y, z, x2, y2, z2, owner]
                    break
                else:
                    i += 1
            data["client"].sendServerMessage("User zone %s has been created." % data["parts"][1].lower())
            data["client"].sendServerMessage("Now use /zone name add|remove [user1 user2 ...]")
        else:
            data["client"].sendServerMessage("You need to provide a zone type. (i.e: user or rank)")

    @config("rank", "op")
    @config("usage", "name [add|remove] [user1 user2]")
    def commandZone(self, data):
        "Shows users assigned to this zone\n'/zone name add|remove [user1 user2 ...]' to edit users."
        if len(data["parts"]) == 2:
            for id, zone in data["client"].world.userzones.items():
                if zone[0] == data["parts"][1]:
                    try:
                        data["client"].sendSplitServerMessage(
                            "Zone %s users: %s" % (zone[0], ", ".join(map(str, zone[7:]))))
                    except:
                        data["client"].sendServerMessage("There are no users assigned to zone %s." % (zone[0]))
                    return
            data["client"].sendServerMessage("There is no zone with that name.")
        elif len(data["parts"]) > 3:
            if data["parts"][2] == "add":
                for id, zone in data["client"].world.userzones.items():
                    if zone[0] == data["parts"][1]:
                        if data["client"].username in zone[6:] or data["client"].isWorldOwner():
                            for user in data["parts"][3:]:
                                if not user.lower() in zone[6:]:
                                    data["client"].world.userzones[id] += [user.lower()]
                                else:
                                    data["client"].sendServerMessage("%s is already assigned to zone %s." % (user.lower(), zone[0]))
                                    return
                            data["client"].sendServerMessage("User %s added to zone %s." % (", ".join(map(str, data["parts"][3:])), zone[0]))
                            return
                        else:
                            data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to add users." % zone[0])
                            return
            elif data["parts"][2] == "remove":
                for id, zone in data["client"].world.userzones.items():
                    if zone[0] == data["parts"][1]:
                        if data["client"].username in zone[6:] or data["client"].isWorldOwner():
                            for user in data["parts"][3:]:
                                try:
                                    data["client"].world.userzones[id].remove(user.lower())
                                except:
                                    data["client"].sendServerMessage("User %s is not assigned to zone %s." % (user.lower(), zone[0]))
                                    return
                            data["client"].sendServerMessage("Removed %s from zone %s." % (", ".join(map(str, data["parts"][3:])), zone[0]))
                            return
                        else:
                            data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to remove users." % zone[0])
                            return
            else:
                data["client"].sendServerMessage("Invalid action %s." % data["parts"][2])
        else:
            data["client"].sendServerMessage("You must provide a zone name.")

    @config("rank", "op")
    @config("usage", "name")
    def commandZoneRemove(self, data):
        "Removes a zone."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You must provide a zone name.")
            return
        match = False
        for id, zone in data["client"].world.userzones.items():
            if zone[0] == data["parts"][1]:
                if data["client"].username in zone[6:] or data["client"].isWorldOwner():
                    match = True
                    del data["client"].world.userzones[id]
                    data["client"].sendServerMessage("Zone %s has been removed." % zone[0])
                    return
                else:
                    data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to remove it." % zone[0])
                    return
        for id, zone in data["client"].world.rankzones.items():
            if zone[0] == data["parts"][1]:
                for rank in ["WorldOwner", "Mod", "Admin", "Director", "Owner"]:
                    # TODO: Implement a rank checking system that doesn't suck.
                    if zone[7] == rank.lower() and not getattr(data["client"], "is%s" % rank)():
                        data["client"].sendSplitServerMessage("You cannot remove a rank zone in which the rank is higher than your current rank.")
                    return
                match = True
                del data["client"].world.rankzones[id]
                data["client"].sendServerMessage("%s has been removed." % zone[0])
                return
        if not match:
            data["client"].sendServerMessage("There is no zone with that name.")

    def commandListZones(self, data):
        "Lists all the zones on this world."
        data["client"].sendServerList(["User Zones:"] + [zone[0] for id, zone in data["client"].world.userzones.items()])
        data["client"].sendServerList(["Rank Zones:"] + [zone[0] for id, zone in data["client"].world.rankzones.items()])

    @config("usage", "all|name")
    def commandZshow(self, data):
        "Outlnes the zone in water temporary."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Please provide a zone to show.")
            data["client"].sendServerMessage("[or 'all' to show all zones]")
            return
        # Build the changeset
        changeset = {}
        block = chr(globals()['BLOCK_STILLWATER'])
        match = False
        if data["parts"][1].lower() == "all":
            for id, zone in (data["client"].world.userzones.items() + data["client"].world.rankzones.items()):
                x, y, z, x2, y2, z2 = zone[1:7]
                if x > x2: x, x2 = x2, x
                if y > y2: y, y2 = y2, y
                if z > z2: z, z2 = z2, z
                x += 1
                y += 1
                z += 1
                x2 -= 1
                y2 -= 1
                z2 -= 1
                for i in range(x, x2 + 1):
                    for j in range(y, y2 + 1):
                        for k in range(z, z2 + 1):
                            if (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or \
                            (i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or \
                            (i == x and k == z2) or (j == y and k == z2) or (i == x2 and k == z) or \
                            (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                                changeset[i, j, k] = block
            # Now, apply it.
            def zshowCallback(result):
                if isinstance(result, AssertionError):
                    data["client"].sendServerMessage("Out of bounds, please report to a server staff.")
                    return
                else:
                    data["client"].sendServerMessage("All zones in this world are shown temporarily by a water border.")
            self.factory.applyBlockChanges(changeset, w, save=False).addBoth(zshowCallback)
        else:
            user = data["parts"][1].lower()
            for id, zone in (data["client"].world.userzones.items() + data["client"].world.rankzones.items()):
                if user == zone[0]:
                    match = True
                    x, y, z, x2, y2, z2 = zone[1:7]
                    if x > x2: x, x2 = x2, x
                    if y > y2: y, y2 = y2, y
                    if z > z2: z, z2 = z2, z
                    x += 1
                    y += 1
                    z += 1
                    x2 -= 1
                    y2 -= 1
                    z2 -= 1
            if not match:
                data["client"].sendServerMessage("That zone does not exist.")
                return
            for i in range(x, x2 + 1):
                for j in range(y, y2 + 1):
                    for k in range(z, z2 + 1):
                        if (i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or \
                        (i == x2 and k == z2) or (j == y and k == z) or (i == x and k == z) or \
                        (i == x and k == z2) or (j == y and k == z2) or (i == x2 and k == z) or \
                        (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y):
                            changeset[i, j, k] = block
            # Now, apply it.
            def zshowCallback(result):
                if isinstance(result, AssertionError):
                    data["client"].sendServerMessage("Out of bounds, please report to a server staff.")
                    return
                else:
                    data["client"].sendServerMessage("All zones in this world are shown temporarily by a water border.")

    @config("rank", "op")
    @config("usage", "name")
    def commandClearZone(self, data):
        "Clears everything within the zone."
        if not len(data["parts"]) == 2:
            data["client"].sendServerMessage("Please provide a zone to clear.")
            return
        match = False
        user = data["parts"][1].lower()
        block = chr(globals()['BLOCK_AIR'])
        for id, zone in data["client"].world.userzones.items():
            if user == zone[0]:
                if not (data["client"].username in zone[6:] or data["client"].isWorldOwner()):
                    data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to clear it." % zone[0])
                    return
                match = True
                x, y, z, x2, y2, z2 = zone[1:7]
                if x > x2: x, x2 = x2, x
                if y > y2: y, y2 = y2, y
                if z > z2: z, z2 = z2, z
                x += 1
                y += 1
                z += 1
                x2 -= 1
                y2 -= 1
                z2 -= 1
        for id, zone in data["client"].world.rankzones.items():
            if user == zone[0]:
                for rank in ["WorldOwner", "Mod", "Admin", "Director", "Owner"]:
                    # TODO: Implement a rank checking system that doesn't suck.
                    if zone[7] == rank.lower() and not getattr(data["client"], "is%s" % rank)():
                        data["client"].sendSplitServerMessage("You cannot remove a rank zone in which the rank is higher than your current rank.")
                        return
                match = True
                x, y, z, x2, y2, z2 = zone[1:7]
                if x > x2: x, x2 = x2, x
                if y > y2: y, y2 = y2, y
                if z > z2: z, z2 = z2, z
                x += 1
                y += 1
                z += 1
                x2 -= 1
                y2 -= 1
                z2 -= 1
        if not match:
            data["client"].sendServerMessage("That zone does not exist.")
            return
        # Build the changeset
        changeset = {}
        for i in range(x, x2 + 1):
            for j in range(y, y2 + 1):
                for k in range(z, z2 + 1):
                    changeset[i, j, k] = block
        # Now, apply it.
        def zclearCallback(result):
            if isinstance(result, AssertionError):
                data["client"].sendServerMessage("Out of bounds.")
                return
            else:
                data["client"].sendServerMessage("Zone clear finished, with %s blocks changed." % (x2 - x) * (y2 - y) * (z2 - z))
        self.factory.applyBlockChanges(changeset, w).addBoth(zclearCallback)

    @config("rank", "op")
    def commandZDelAll(self, data):
        "Removes all zones in a world (if you can delete them)"
        match = False
        for id, zone in data["client"].world.userzones.items():
            if data["client"].username in zone[6:] or data["client"].isWorldOwner():
                del data["client"].world.userzones[id]
            else:
                data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to delete this zone." % zone[0])
                return
        for id, zone in data["client"].world.rankzones.items():
            for rank in ["WorldOwner", "Mod", "Admin", "Director", "Owner"]:
                # TODO: Implement a rank checking system that doesn't suck.
                if zone[7] == rank.lower() and not getattr(data["client"], "is%s" % rank)():
                    data["client"].sendSplitServerMessage("You cannot remove a rank zone in which the rank is higher than your current rank.")
                    return
            del data["client"].world.rankzones[id]
        data["client"].sendServerMessage("All Rank Zones have been deleted.")

    @config("category", "info")
    @config("rank", "op")
    def commandZoneWho(self, data):
        "Tells you whose zone you're currently in, if any."
        x, y, z = data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5
        found = False
        for id, zone in data["client"].world.userzones.items():
            x1, y1, z1, x2, y2, z2 = zone[1:7]
            if x1 < x < x2:
                if y1 < y < y2:
                    if z1 < z < z2:
                        data["client"].sendServerMessage("User Zone: %s [%d]" % (zone[0], id))
                        found = True
        for id, zone in data["client"].world.rankzones.items():
            x1, y1, z1, x2, y2, z2 = zone[1:7]
            if x1 < x < x2:
                if y1 < y < y2:
                    if z1 < z < z2:
                        data["client"].sendServerMessage("Rank Zone: %s [%d]" % (zone[0], id))
                        found = True
        if not found:
            data["client"].sendServerMessage("Zone is unclaimed!")

    @config("rank", "op")
    @config("usage", "oldname newname")
    def commandZRename(self, data):
        "Renames a zone."
        if not len(data["parts"]) == 3:
            data["client"].sendServerMessage("Please provide an old and a new zone name.")
            return
        oldname = data["parts"][1].lower()
        newname = data["parts"][2].lower()
        if oldname == newname:
            data["client"].sendServerMessage("Old and new names are the same.")
        for id, zone in data["client"].world.userzones.items():
            if zone[0] == newname:
                data["client"].sendServerMessage("Zone %s already exists. Pick a new name." % newname)
                return
        for id, zone in data["client"].world.rankzones.items():
            if zone[0] == newname:
                data["client"].sendServerMessage("Zone %s already exists. Pick a new name." % newname)
                return
        for id, zone in data["client"].world.userzones.items():
            if oldname == zone[0]:
                if data["client"].username in zone[6:] or data["client"].isWorldOwner():
                    zone[0] = newname
                    data["client"].sendServerMessage("Zone %s has been renamed to %s." % (oldname, newname))
                    return
                else:
                    data["client"].sendSplitServerMessage("You are not a member of %s. You must be one of its users to rename it." % zone[0])
                    return
        for id, zone in data["client"].world.rankzones.items():
            if oldname == zone[0]:
                for rank in ["WorldOwner", "Helper", "Mod", "Admin", "Director", "Owner"]:
                    # TODO: Implement a rank checking system that doesn't suck.
                    if zone[7] == rank.lower() and not getattr(data["client"], "is%s" % rank)(): 
                        data["client"].sendSplitServerMessage("You can not rename a ranked zone in which the rank is higher than your current rank.")
                        return
                zone[0] = newname
                data["client"].sendServerMessage("Zone %s has been renamed to %s" % (oldname, newname))
                return
        data["client"].sendServerMessage("Zone %s doesn't exist." % oldname)

serverPlugin = ZonesPlugin