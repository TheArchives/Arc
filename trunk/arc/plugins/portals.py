# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *

class PortalPlugin(object):
    commands = {
        "p": "commandPortal",
        "phere": "commandPortalhere",
        "pend": "commandPortalend",
        "pshow": "commandShowportals",
        "pdel": "commandPortaldel",
        "pdelend": "commandPortaldelend",
        "puse": "commandUseportals",
        }

    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
        }

    def gotClient(self, data):
        data["client"].portal_dest = None
        data["client"].portal_remove = False
        data["client"].portals_on = True
        data["client"].last_block_position = None

    def blockChanged(self, data):
        "Hook trigger for block changes."
        if data["client"].world.has_portal(data["x"], data["y"], data["z"]):
            if data["client"].portal_remove:
                data["client"].world.delete_portal(data["x"], data["y"], data["z"])
                data["client"].sendServerMessage("You deleted a Portal block.")
            else:
                data["client"].sendServerMessage("That is a Portal block, you cannot change it. (/pdel?)")
                return False # False = they weren't allowed to build
        if data["client"].portal_dest:
            data["client"].sendServerMessage("You placed a Portal block.")
            data["client"].world.add_portal(data["x"], data["y"], data["z"], data["client"].portal_dest)

    def posChanged(self, data):
        "Hook trigger for when the user moves"
        rx, ry, rz = data["x"] >> 5, data["y"] >> 5, data["z"] >> 5
        try:
            world, tx, ty, tz, th = data["client"].world.get_portal(rx, ry, rz)
        except (KeyError, AssertionError):
            return
        # Yes there is! do it.
        if data["client"].portals_on:
            world_id = world
            if world_id not in self.factory.worlds:
                data["client"].sendServerMessage("Attempting to boot and join '%s'" % world_id)
                try:
                    self.factory.loadWorld("worlds/%s" % world_id, world_id)
                except AssertionError:
                    if (rx, ry, rz) != data["client"].last_block_position:
                        data["client"].sendServerMessage("World %s does not exist or is broken." % world_id)
                    return
            world = self.factory.worlds[world_id]
            if not data["client"].canEnter(world):
                if world.status["private"]:
                    if (rx, ry, rz) != data["client"].last_block_position:
                        data["client"].sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                else:
                    if (rx, ry, rz) != data["client"].last_block_position:
                        data["client"].sendServerMessage("You're WorldBanned from '%s'; you're not allowed in." % world_id)
            else:
                if world == data["client"].world:
                    data["client"].teleportTo(tx, ty, tz, th)
                else:
                    data["client"].changeToWorld(world.id, position=(tx, ty, tz, th))
        data["client"].last_block_position = (rx, ry, rz)

    def newWorld(self, data):
        "Hook to reset Portal abilities in new worlds if not op."
        if not data["client"].isOp():
            data["client"].portal_dest = None
            data["client"].portal_remove = False
            data["client"].portals_on = True

    @config("rank", "op")
    @config("usage", "worldname x y z [r]")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandPortal(self, data):
        "Makes the next block you place a Portal."
        if len(data["parts"]) < 5:
            data["client"].sendServerMessage("Please enter a worldname and a coord triplet.")
            return
        try:
            x, y, z = [int(i) for i in data["parts"][2:4]]
        except ValueError:
            data["client"].sendServerMessage("All coordinate parameter must be integers.")
        else:
            try:
                h = int(data["parts"][5])
            except IndexError:
                h = 0
            except ValueError:
                data["client"].sendServerMessage("r must be an integer.")
                return
            if not (0 <= h <= 255):
                data["client"].sendServerMessage("r must be between 0 and 255.")
                return
            data["parts"].portal_dest = data["parts"][1], x, y, z, h
            data["client"].sendServerMessage("You are now placing portal blocks. /pend to stop")

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandPortalhere(self, data):
        "Enables Portal creation mode, to here."
        data["parts"].portal_dest = data["client"].world.id, data["client"].x >> 5, data["client"].y >> 5, data["client"].z >> 5, data["client"].h
        data["client"].sendServerMessage("You are now placing portal blocks to here. /pend to stop")

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandPortalend(self, data):
        "Disables portal creation mode."
        data["client"].portal_dest = None
        data["client"].portal_remove = False
        data["client"].sendServerMessage("You are no longer placing Portal blocks.")

    @config("rank", "op")
    @config("aliases", ["tpshow"])
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandShowportals(self, data):
        "Shows all Portal blocks as blue, only to you."
        for offset in data["client"].world.portals.keys():
            x, y, z = data["client"].world.get_coords(offset)
            data["client"].sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_BLUE)
        data["client"].sendServerMessage("All Portals appearing blue temporarily.")

    @config("rank", "op")
    @config("aliases", ["deltp", "pclear"])
    @config("usage", "[all world]")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandPortaldel(self, data):
        "Enables portal deletion mode. Toggle."
        if len(data["parts"]) > 1:
            if data["fromloc"] != "user" and data["parts"][1].lower() != "all":
                data["client"].sendServerMessage("To delete all portals please specify 'all'.")
                return
            if data["fromloc"] != "user":
                world_id = data["parts"][2]
                # Check if world is booted
                if world_id not in self.factory.worlds.keys():
                    data["client"].sendServerMessage("That world is currently not booted.")
                    return
            if len(data["parts"] > 2):
                self.factory.worlds[world_id].clear_portals()
                data["client"].sendServerMessage("All Portals in this world removed.")
            else:
                data["client"].world.clear_portals()
                data["client"].sendServerMessage("All Portals in this world removed.")
        else:
            if data["fromloc"] != "user":
                data["client"].sendServerMessage("To delete all portals please specify 'all' and a world.")
                return
            data["client"].sendServerMessage("You are now able to delete Portals. /pdelend to stop")
            data["client"].portal_remove = True

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandPortaldelend(self, data):
        "Disables portal deletion mode."
        data["client"].portal_remove = False
        data["client"].sendServerMessage("Portal deletion mode ended.")

    @on_off_command
    @config("usage", "on|off")
    @config("aliases", ["useportals"])
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandUseportals(self, data):
        "Allows you to enable or disable Portal usage."
        if data["onoff"] == "on":
            data["client"].portals_on = True
            data["client"].sendServerMessage("Portals will now work for you again.")
        else:
            data["client"].portals_on = False
            data["client"].sendServerMessage("Portals will no longer work for you.")

serverPlugin = PortalPlugin