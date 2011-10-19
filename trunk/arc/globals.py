# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from collections import defaultdict

def Rank(self, parts, fromloc, overriderank, server=None):
    username = parts[1].lower()
    if server:
        factory = server
    else:
        factory = self.client.factory
    rank = parts[2].lower()
    if rank in ["builder", "op", "worldowner", "helper", "mod", "admin", "director"]:
        if rank in ["builder", "op", "worldowner"]:
            # World check
            if len(parts) > 3:
                try:
                    world = factory.worlds[parts[3]]
                except KeyError:
                    return ("Unknown world %s." % parts[3])
            else:
                if not server:
                    world = self.client.world
                else:
                    return "You must provide a world."
        # Do the ranks
        if rank == "builder":
            if not server:
                if not overriderank:
                    if not (self.client.username.lower() in world.ops or self.client.isWorldOwner()):
                        return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not ((parts[-1]) in world.ops) and not factory.isMod(parts[-1]):
                        return ("You are not high enough rank!")
            world.builders.add(username)
        elif rank == "op":
            if not server:
                if not overriderank:
                    if not self.client.isWorldOwner():
                        return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isMod(parts[-1]):
                        return ("You are not high enough rank!")
            world.ops.add(username)
        elif rank == "worldowner":
            if not server:
                if not self.client.isWorldOwner() and not overriderank:
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    return ("You are not high enough rank!")
            self.client.world.owner = (username)
        elif rank == "helper":
            if not server:
                if not self.client.isMod():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isMod(parts[-1]):
                        return ("You are not high enough rank!")
            factory.helpers.add(username)
        elif rank == "mod":
            if not server:
                if not self.client.isDirector():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isDirector(parts[-1]):
                        return ("You are not high enough rank!")
            factory.mods.add(username)
        elif rank == "admin":
            if not server:
                if not self.client.isDirector():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isDirector(parts[-1]):
                        return ("You are not high enough rank!")
            factory.admins.add(username)
        elif rank == "director":
            if not server:
                if not self.client.isOwner():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isOwner(parts[-1]):
                        return ("You are not high enough rank!")
            factory.directors.add(username)
        # Final cleanup
        if username in factory.usernames:
            if rank in ["builder", "op", "worldowner"]:
                if factory.usernames[username].world == world:
                    factory.usernames[username].sendRankUpdate()
            else:
                factory.usernames[username].sendRankUpdate()
            factory.usernames[username].sendServerMessage("You are now %s %s%s." % (("an" if (rank.startswith(tuple("aeiou"))) else "a", rank, (" here" if rank in ["builder", "op", "worldowner"] else ""))))
        return ("%s is now %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " here" if rank in ["builder", "op", "worldowner"] else ""))
    else:
        return ("Unknown rank \"%s\"" % rank)

def DeRank(self, parts, fromloc, overriderank, server=None):
    username = parts[1].lower()
    if server:
        factory = server
    else:
        factory = self.client.factory
    rank = parts[2].lower()
    if rank in ["builder", "op", "worldowner", "helper", "mod", "admin", "director"]:
        if rank in ["builder", "op", "worldowner"]:
            # World check
            if len(parts) > 3:
                try:
                    world = factory.worlds[parts[3]]
                except KeyError:
                    return ("Unknown world %s." % parts[3])
            else:
                if not server:
                    world = self.client.world
                else:
                    return "You must provide a world."
        if rank == "builder":
            if not server:
                if not ((self.client.username in world.ops) or self.client.isWorldOwner()) and overriderank:
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not ((parts[-1]) in world.ops) or factory.isMod(parts[-1]):
                        return ("You are not high enough rank!")
            try:
                world.builders.remove(username)
            except KeyError:
                return ("%s is not a Builder." % username)
        elif rank == "op":
            if not server:
                if not self.client.isWorldOwner() and world != self.client.world:
                    return ("You are not a World Owner!")
            else:
                if fromloc != "console":
                    if not factory.isWorldOwner(parts[-1]):
                        return ("You are not high enough rank!")
            try:
                world.ops.remove(username)
            except KeyError:
                return ("%s is not an op." % username)
        elif rank == "worldowner":
            if not server:
                if not self.client.isMod():
                    return ("You are not a mod!")
            else:
                if fromloc != "console":
                    if not factory.isWorldOwner(parts[-1]):
                        return ("You are not high enough rank!")
            try:
                self.client.world.owner = ("")
            except KeyError:
                return ("%s is not a world owner." % username)
        elif rank == "helper":
            if not server:
                if not self.client.isMod():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isMod(parts[-1]):
                        return ("You are not high enough rank!")
            if username in factory.helpers:
                factory.helpers.remove(username)
            else:
                return ("No such helper \"%s\"" % username.lower())
        elif rank == "mod":
            if not server:
                if not self.client.isDirector():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isDirector(parts[-1]):
                        return ("You are not high enough rank!")
            if username in factory.mods:
                factory.mods.remove(username)
            else:
                return ("No such mod \"%s\"" % username.lower())
        elif rank == "admin":
            if not server:
                if not self.client.isDirector():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isDirector(parts[-1]):
                        return ("You are not high enough rank!")
            if username in factory.admins:
                factory.admins.remove(username)
            else:
                return ("No such admin \"%s\""% username.lower())
        elif rank == "director":
            if not server:
                if not self.client.isOwner():
                    return ("You are not high enough rank!")
            else:
                if fromloc != "console":
                    if not factory.isOwner(parts[-1]):
                        return ("You are not high enough rank!")
            if username in factory.directors:
                factory.directors.remove(username)
            else:
                return ("No such director \"%s\"" % username.lower())
        # Final cleanup
        if username in factory.usernames:
            if rank in ["builder", "op", "worldowner"]:
                if factory.usernames[username].world == world:
                    factory.usernames[username].sendRankUpdate()
            else:
                factory.usernames[username].sendRankUpdate()
            factory.usernames[username].sendServerMessage("You are no longer %s %s%s." % (("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " here" if rank in ["builder", "op", "worldowner"] else ""))
        return ("%s is no longer %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " here" if rank in ["builder", "op", "worldowner"] else ""))
    else:
        return ("Unknown rank \"%s\""%rank)

def Spec(self, username, fromloc, overriderank, server=None):
    if server:
        factory = server
    else:
        factory = self.client.factory
    if username in factory.mods:
        return ("You cannot make staff a spec!")
    factory.spectators.add(username)
    if username in factory.usernames:
        factory.usernames[username].sendRankUpdate()
    return ("%s is now a spec." % username)

def DeSpec(self, username, fromloc, overriderank, server=None):
    if server:
        factory = server
    else:
        factory = self.client.factory
    if username not in factory.spectators:
        return ("User %s is not specced." % username)
    factory.spectators.remove(username)
    if username in factory.usernames:
        factory.usernames[username].sendRankUpdate()
    return ("%s is no longer a spec." % username)
    
def Staff(self, server=None):
    Temp = []
    if server:
        factory = server
    else:
        factory = self.client.factory
    if len(factory.owners): # This doesn't make much sense but okay
        Temp.append(["Owners:"] + list(factory.owners))
    if len(factory.directors):
        Temp.append(["Directors:"] + list(factory.directors))
    if len(factory.admins):
        Temp.append(["Admins:"] + list(factory.admins))
    if len(factory.mods):
        Temp.append(["Mods:"] + list(factory.mods))
    if len(factory.helpers):
        Temp.append(["Helpers:"] + list(factory.helpers))
    return Temp

def Credits():
    Temp = []
    Temp.append("Thanks to the following people for making Arc possible...")
    Temp.append("Mojang Specifications (Minecraft): Notch, c418, ez, jeb, kappe, mollstam...")
    Temp.append("Creators: aera (Myne and The Archives), PixelEater (MyneCraft and blockBox), gdude2002/arbot (Maintainer of The Archives)")
    Temp.append("Devs (Arc): Adam01, AndrewPH, destroyerx1, Dwarfy, erronjason, eugo (Knossus), goober, gothfox, NotMeh, ntfwc, revenant, Saanix, sk8rjwd, tehcid, Varriount, willempiee")
    Temp.append("Devs (blockBox): fizyplankton, tyteen4a03, UberFoX")
    Temp.append("Others: 099, 2k10, Akai, Antoligy, Aquaskys, Bidoof_King, Bioniclegenius (Red_Link), blahblahbal, BlueProtoman, CDRom, fragmer, GLaDOS (Cortana), iMak, Kelraider, MAup, MystX, PyroPyro, Rils, Roadcrosser, Roujo, setveen, TkTech, Uninspired")
    return Temp

def makefile(filename):
    import os
    dir = os.path.dirname(filename)
    try:
        os.stat(dir)
    except:
        try:
            os.mkdir(dir)
        except OSError:
            pass
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")
    del os

def makedatfile(filename):
    import os
    dir = os.path.dirname(filename)
    try:
        os.stat(dir)
    except:
        try:
            os.mkdir(dir)
        except OSError:
            pass
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            import cPickle
            cPickle.dump("", f)
            del cPickle
    del os

def invertDict(OldDict):
    NewDict = dict()
    for key in OldDict.iterkeys():
        if OldDict[key] not in NewDict:
            NewDict[OldDict[key]] = key
    return NewDict

def appendToKeys(theDict, phrase):
    finalDict = dict()
    for key in theDict.keys():
        for value in theDict.values():
            finalDict[phrase+key] = value
    return finalDict

def recursive_default():
    return defaultdict(recursive_default)

def checkConfigVersion(version, current):
    theVersion = tuple()
    try:
        theVersion = version.split(".")
    except ValueError as e:
        return False
    else:
        # Check version
        if (int(theVersion[0]) < current[0]) or ((int(theVersion[1]) + 2) < current[1]) or ((int(theVersion[2]) + 5) < current[2]):
            return False
        else:
            return True