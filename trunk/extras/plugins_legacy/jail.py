# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle

from arc.constants import *
from arc.decorators import *

# jail constants for jail.dat
J_USERS = 0
J_ZONE = 1
J_WORLD = 2

class JailPlugin(object):
    def loadJail(self):
        file = open('config/data/jail.dat', 'r')
        dic = cPickle.load(file)
        file.close()
        return dic

    def dumpJail(self, dic):
        file = open('config/data/jail.dat', 'w')
        cPickle.dump(dic, file)
        file.close()

    commands = {
        "jail": "commandJail",
        "free": "commandFree",
        "setjail": "commandSetJail",
        "prisoners": "commandPrisoners",
        }

    hooks = {
        "posChange": "posChanged",
        "onPlayerConnect": "playerConnected",
        "newWorld": "newWorld",
        }

    def playerConnected(self, data):
        data["client"].jailed = False
        data["client"].jailed_until = -1
        data["client"].jail_zone = ""
        data["client"].jail_world = ""
        self.prepJail(data["client"])

    def prepJail(self, client):
        jail = self.loadJail()
        user = client.username.lower()
        changed = False
        if J_USERS not in jail:
            jail[J_USERS] = {}
            changed = True
        if J_ZONE not in jail:
            jail[J_ZONE] = ""
            changed = True
        if J_WORLD not in jail:
            jail[J_WORLD] = ""
            changed = True
        if user in jail[J_USERS]:
            client.jailed = True
            client.jailed_until = jail[J_USERS][user]
        else:
            client.jailed = False
            client.jailed_until = -1
        client.jail_world = jail[J_WORLD]
        client.jail_zone = jail[J_ZONE]
        if changed:
            client.dumpJail(jail)

    def playerJoined(self, user):
        self.prepJail()

    def newWorld(self, world):
        self.prepJail()

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        if self.jailed:
            user = data["client"].username.lower()
            injail = False
            if self.jail_world == "" or self.jail_zone == "":
                return
            if clock() >= self.jailed_until and self.jailed_until > 0:
                data["client"].sendWorldMessage("%s has served their sentence and is free." % user)
                self.jailed = False
                self.jailed_until = -1
                jail = self.loadJail()
                jail[J_USERS].pop(user)
                self.dumpJail(jail)
                data["client"].changeToWorld(self.jail_world)
                return
            if data["client"].world.id != self.jail_world:
                if data["client"].world.id not in self.factory.worlds:
                    try:
                        self.factory.loadWorld("worlds/%s" % self.jail_world, self.jail_world)
                    except AssertionError:
                        data["client"].sendServerMessage("It's your lucky day, world %s is broken!" % self.jail_world)
                        return
                data["client"].changeToWorld(self.jail_world)
            for id, zone in data["client"].world.userzones.items():
                if zone[0] == self.jail_zone:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    found = True
                    break
            for id, zone in data["client"].world.rankzones.items():
                if zone[0] == self.jail_zone:
                    x1, y1, z1, x2, y2, z2 = zone[1:7]
                    found = True
                    break
            if not found:
                jail = self.loadJail()
                jail[J_USERS][J_ZONE] = ""
                self.dumpJail(jail)
                return
            if x1 < rx < x2:
                if y1 < ry < y2:
                    if z1 < rz < z2:
                        injail = True
            if not injail:
                jx = int((x1 + x2) / 2)
                jy = int((y1 + y2) / 2)
                jz = int((z1 + z2) / 2)
                data["client"].teleportTo(jx, jy, jz)

    @config("rank", "mod")
    def commandSetJail(self, data):
        "/setjail zonename - Mod\nSpecifies the jails zone name"
        if len(parts) != 2:
            data["client"].sendServerMessage("Usage: /setjail zonename")
            return
        zonename = parts[1]
        exists = False
        for id, zone in data["client"].world.userzones.items():
            if zone[0] == zonename:
                exists = True
        for id, zone in data["client"].world.rankzones.items():
            if zone[0] == zonename:
                exists = True
        if not exists:
            data["client"].sendServerMessage("Zone '%s' doesn't exist in this world!" % zonename)
            return
        self.prepJail()
        jail = self.loadJail()
        jail[J_ZONE] = zonename
        jail[J_WORLD] = data["client"].world.id
        data["client"].sendServerMessage("Set jail zone as '%s' in %s!" % (zonename, data["client"].world.id))
        self.dumpJail(jail)

    @config("rank", "mod")
    def commandJail(self, data):
        "/jail user [minutes] - Mod\nPuts a user in jail.\nYou can specify a time limit, or leave blank for permajail!"
        if len(parts) == 3:
            if not parts[2].isdigit():
                data["client"].sendServerMessage("You must specify a positive numerical value for minutes!")
                return
            time = int(parts[2])
            seconds = int(parts[2]) * 60
        elif len(parts) == 2:
            seconds = 0
            time = 0
        else:
            data["client"].sendServerMessage("Usage: /jail user [minutes]")
            return
        if self.factory.isHelper(parts[1]) or parts[1].lower() == data["client"].username.lower():
            data["client"].sendServerMessage("You cannot jail yourself or a staff!")
            return
        self.prepJail()
        jail = self.loadJail()
        found = False
        if jail[J_ZONE] == "":
            data["client"].sendServerMessage("You must set a jail zone up first with /znew!")
            data["client"].sendServerMessage("Use /setjail zone_name to set one up!")
            return
        names = []
        name = parts[1].lower()
        for id, zone in self.factory.worlds[self.jail_world].userzones.items():
            if zone[0] == self.jail_zone:
                x1, y1, z1, x2, y2, z2 = zone[1:7]
                found = True
                break
        for id, zone in self.factory.worlds[self.jail_world].rankzones.items():
            if zone[0] == self.jail_zone:
                x1, y1, z1, x2, y2, z2 = zone[1:7]
                found = True
                break
        if not found:
            data["client"].sendServerMessage("Jail zone '%s' has been removed!" % jail[J_ZONE])
            data["client"].sendServerMessage("Use /znew and /setjail zonename to set one up!")
            jail[J_ZONE] = ""
            self.dumpJail(jail)
            return
        if seconds == 0:
            jail[J_USERS][name] = 0
        else:
            jail[J_USERS][name] = int(clock() + seconds)
        self.dumpJail(jail)
        for username in self.factory.usernames:
            if name in username:
                names.append(username)
        if len(names) == 1:
            user = self.factory.usernames[names[0]]
            user.jailed = True
            jx = int((x1 + x2) / 2)
            jy = int((y1 + y2) / 2)
            jz = int((z1 + z2) / 2)
            user.changeToWorld(self.jail_world, position=(jx, jy, jz))
        if time == 1:
            jailtime = "for " + str(time) + " minute"
        elif time > 1:
            jailtime = "for " + str(time) + " minutes"
        else:
            jailtime = "indefinitely"
        data["client"].sendWorldMessage("%s has been jailed %s." % (name, jailtime))

    @config("rank", "mod")
    def commandFree(self, data):
        "/free username - Mod\nLets a user out of jail"
        self.prepJail()
        jail = self.loadJail()
        names = []
        try:
            name = parts[1].lower()
        except:
            data["client"].sendServerMessage("You need to specify a username.")
        if name in jail[J_USERS]:
            jail[J_USERS].pop(name)
            self.dumpJail(jail)
        else:
            data["client"].sendServerMessage("%s isn't jailed!" % name)
            return
        for username in self.factory.usernames:
            if name in username:
                names.append(username)
        if len(names) == 1:
            user = self.factory.usernames[names[0]]
            user.changeToWorld(jail[J_WORLD])
        data["client"].sendWorldMessage("%s has been set free." % name)

    @config("rank", "mod")
    def commandPrisoners(self, data):
        "/prisoners - Mod\nLists prisoners and their sentences."
        self.prepJail()
        jail = self.loadJail()
        found = False
        data["client"].sendServerMessage("Listing prisoners:")
        for name in jail[J_USERS]:
            if jail[J_USERS][name] > 1:
                remaining = int(jail[J_USERS][name] - clock())
                data["client"].sendServerMessage("%s - %d seconds remaining" % (name, remaining))
            else:
                data["client"].sendServerMessage("%s - Life" % name)
            found = True
        if not found:
            data["client"].sendServerMessage("Currently no prisoners in jail.")
