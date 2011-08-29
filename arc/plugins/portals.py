# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class PortalPlugin(ProtocolPlugin):
    
    commands = {
        "p": "commandPortal",
        "tpbox": "commandPortal",
        "phere": "commandPortalhere",
        "pend": "commandPortalend",
        "pshow": "commandShowportals",
        "tpshow": "commandShowportals",
        "pdel": "commandPortaldel",
        "pclear": "commandPortaldel",
        "deltp": "commandPortaldel",
        "pdelend": "commandPortaldelend",
        "puse": "commandUseportals",
        "useportals": "commandUseportals",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.portal_dest = None
        self.portal_remove = False
        self.portals_on = True
        self.last_block_position = None
    
    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if self.client.world.has_teleport(x, y, z):
            if self.portal_remove:
                self.client.world.delete_teleport(x, y, z)
                self.client.sendServerMessage("You deleted a Portal block.")
            else:
                self.client.sendServerMessage("That is a Portal block, you cannot change it. (/pdel?)")
                return False # False = they weren't allowed to build
        if self.portal_dest:
            self.client.sendServerMessage("You placed a Portal block.")
            self.client.world.add_teleport(x, y, z, self.portal_dest)
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        try:
            world, tx, ty, tz, th = self.client.world.get_teleport(rx, ry, rz)
        except (KeyError, AssertionError):
            pass
        else:
            # Yes there is! do it.
            if self.portals_on:
                world_id = world
                if world_id not in self.client.factory.worlds:
                    self.client.sendServerMessage("Attempting to boot and join '%s'" % world_id)
                    try:
                        self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
                    except AssertionError:
                        self.client.sendServerMessage("There is no world by that name.")
                        return
                    except IOError as e:
                        self.client.sendServerMessage("This world is broken. Please report!")
                        self.client.logger.error("World %s is broken!" % world_id)
                        self.client.logger.error("Error: %s" % e)
                    return
                world = self.client.factory.worlds[world_id]
                if not self.client.canEnter(world):
                    if world.private:
                        if (rx, ry, rz) != self.last_block_position:
                            self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                    else:
                        if (rx, ry, rz) != self.last_block_position:
                            self.client.sendServerMessage("You're WorldBanned from '%s'; you're not allowed in." % world_id)
                else:
                    if world == self.client.world:
                        self.client.teleportTo(tx, ty, tz, th)
                    else:
                        self.client.changeToWorld(world.id, position=(tx, ty, tz, th))
        self.last_block_position = (rx, ry, rz)
    
    def newWorld(self, world):
        "Hook to reset Portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.portal_dest = None
            self.portal_remove = False
            self.portals_on = True
    
    @config("rank", "op")
    def commandPortal(self, parts, fromloc, overriderank):
        "/p worldname x y z [r] - Op\nAliases: tpbox\nMakes the next block you place a Portal."
        if len(parts) < 5:
            self.client.sendServerMessage("Please enter a worldname and a coord triplet.")
        else:
            try:
                x = int(parts[2])
                y = int(parts[3])
                z = int(parts[4])
            except ValueError:
                self.client.sendServerMessage("All coordinate parameter must be integers.")
            else:
                try:
                    h = int(parts[5])
                except IndexError:
                    h = 0
                except ValueError:
                    self.client.sendServerMessage("r must be an integer.")
                    return
                if not (0 <= h <= 255):
                    self.client.sendServerMessage("r must be between 0 and 255.")
                    return
                self.portal_dest = parts[1], x, y, z, h
                self.client.sendServerMessage("You are now placing portal blocks. /pend to stop")
    
    @config("rank", "op")
    def commandPortalhere(self, parts, fromloc, overriderank):
        "/phere - Op\nEnables Portal creation mode, to here."
        self.portal_dest = self.client.world.id, self.client.x>>5, self.client.y>>5, self.client.z>>5, self.client.h
        self.client.sendServerMessage("You are now placing portal blocks to here. /pend to stop")
    
    @config("rank", "op")
    def commandPortalend(self, parts, fromloc, overriderank):
        "/pend - Op\nDisables portal creation mode."
        self.portal_dest = None
        self.portal_remove = False
        self.client.sendServerMessage("You are no longer placing Portal blocks.")
    
    @config("rank", "op")
    def commandShowportals(self, parts, fromloc, overriderank):
        "/pshow - Op\nAliases: tpshow\nShows all Portal blocks as blue, only to you."
        for offset in self.client.world.teleports.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_BLUE)
        self.client.sendServerMessage("All Portals appearing blue temporarily.")

    @config("rank", "op")
    def commandPortaldel(self, parts, fromloc, overriderank):
        "/pdel [all] - Op\nAliases: deltp, pclear\nEnables Portal deletion mode"
        if len(parts) > 1:
            if parts[1].lower() == "all":
                self.client.world.clear_teleports()
                self.client.sendServerMessage("All Portals in this world removed.")
            else:
                self.client.sendServerMessage("To delete all portals please specify 'all'.")
        else:
            self.client.sendServerMessage("You are now able to delete Portals. /pdelend to stop")
            self.portal_remove = True

    @config("rank", "op")
    def commandPortaldelend(self, parts, fromloc, overriderank):
        "/pdelend - Op\nHere for people that need it, as we're Still Alive."
        self.portal_remove = False
        self.client.sendServerMessage("Portal deletion mode ended.")

    @on_off_command
    def commandUseportals(self, onoff, fromloc, overriderank):
        "/puse on|off - Guest\nAliases: useportals\nAllows you to enable or disable Portal usage."
        if onoff == "on":
            self.portals_on = True
            self.client.sendServerMessage("Portals will now work for you again.")
        else:
            self.portals_on = False
            self.client.sendServerMessage("Portals will no longer work for you.")
