# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, os
from collections import defaultdict

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

def packString(string, length=64, packWith=" "):
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