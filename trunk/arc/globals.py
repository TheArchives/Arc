# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, os
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
            self.client.world.status["owner"] = (username)
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
            factory.usernames[username].sendServerMessage("You are now %s %s%s." % ((
            "an" if (rank.startswith(tuple("aeiou"))) else "a", rank,
            (" here" if rank in ["builder", "op", "worldowner"] else ""))))
        return ("%s is now %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank,
                                        " here" if rank in ["builder", "op", "worldowner"] else ""))
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
            self.client.world.status["owner"] = ("N/A")
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
                return ("No such admin \"%s\"" % username.lower())
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
            factory.usernames[username].sendServerMessage("You are no longer %s %s%s." % (
            ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank, " here" if rank in ["builder", "op",
                                                                                            "worldowner"] else ""))
        return ("%s is no longer %s %s%s." % (username, ("an" if (rank.startswith(tuple("aeiou"))) else "a"), rank,
                                              " here" if rank in ["builder", "op", "worldowner"] else ""))
    else:
        return ("Unknown rank \"%s\"" % rank)


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


def makefile(filename):
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

def makedatfile(filename):
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
            cPickle.dump("", f)


def makefiles(l):
    for f in l:
        makefile(f)


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
            finalDict[phrase + key] = value
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
        if (int(theVersion[0]) < current[0]) or ((int(theVersion[1]) + 2) < current[1]) or (
        (int(theVersion[2]) + 5) < current[2]):
            return False
        else:
            return True


def sanitizeMessage(message, replacesets):
    def _messageReplace(message, dict):
        for key, value in dict.items():
            message = message.replace(key, value)
        return message

    if isinstance(replacesets, list):
        for replaceset in replacesets:
            if isinstance(replaceset, dict):
                message = _messageReplace(message, replaceset)
            else:
                raise ValueError("Replace set not a list of dicts")
    elif isinstance(replacesets, dict):
        message = _messageReplace(message, replacesets)
    else:
        raise ValueError("Replace set not a dict or a list of dicts")
    return message

def packString(self, string, length=64, packWith=" "):
    return string + (packWith * (length - len(string)))

def splitMessage(message, linelen=63):
    lines = []
    thisline = ""
    words = message.split()
    for x in words:
        if len(thisline + " " + x) < linelen:
            thisline = thisline + " " + x
        else:
            lines.append(thisline)
            thisline = x
    if thisline != "":
        lines.append(thisline)
    return lines

def find_keys(dic, val):
    """Returns a list of keys in a dict with the value val."""
    return [k for k, v in dic.iteritems() if v == val]

class Popxrange(): # There is probably a way to do this without this class but where?
    def __init__(self, start, end):
        self._i = iter(xrange(start, end))

    def pop(self):
        try:
            return self._i.next()
        except StopIteration:
            raise KeyError

    def __len__(self):
        return self._i.__length_hint__()


class Deferred(object):
    """
    A slimed-down version of Deferred. DEPRECATED.
    """

    def __init__(self):
        self.callbacks = []
        self.errbacks = []
        self.called_back = None
        self.erred_back = None

    def addCallback(self, func, *args, **kwargs):
        "Adds a callback for success."
        if self.called_back is None:
            self.callbacks.append((func, args, kwargs))
        else:
            self.merge_call(func, args, self.called_back[0], kwargs, self.called_back[1])

    def addErrback(self, func, *args, **kwargs):
        "Adds a callback for error."
        if self.erred_back is None:
            self.errbacks.append((func, args, kwargs))
        else:
            self.merge_call(func, args, self.erred_back[0], kwargs, self.erred_back[1])

    def merge_call(self, func, args1, args2, kwargs1, kwargs2):
        "Merge two function call definitions together sensibly, and run them."
        kwargs1.update(kwargs2)
        func(*(args1 + args2), **kwargs1)

    def callback(self, *args, **kwargs):
        "Send a successful-callback signal."
        for func, fargs, fkwargs in self.callbacks:
            self.merge_call(func, fargs, args, fkwargs, kwargs)
        self.called_back = (args, kwargs)

    def errback(self, *args, **kwargs):
        "Send an error-callback signal."
        for func, fargs, fkwargs in self.errbacks:
            self.merge_call(func, fargs, args, fkwargs, kwargs)
        self.erred_back = (args, kwargs)