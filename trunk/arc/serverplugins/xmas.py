# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import random

from arc.constants import *
from arc.decorators import *

class XMasPlugin():
    name = "XMasPlugin"

    hooks = {
        "onPlayerConnect": "playerConnected",
        "chatUsername": "changeUsername"
    }

    commands = {
        "xmas": "commandXmas"
    }

    specialendings = [" &cClause", " &fSnowman", " &4Reindeer", " &bYeti", " &2Tree", " &dFairy", " &aElf", " &8Pudding"]

    def playerConnected(self, data):
        data["client"].specialending = self.specialendings[random.randint(0, len(self.specialendings) - 1)]

    def changeUsername(self, data):
        if data["client"].specialending != "":
            return data["client"].username + data["client"].specialending
        else:
            return data["client"].username

    @config("disabled-on", ["console", "irc"])
    def commandXmas(self, data):
        "Toggles XMas Special Endings in your chat messages."
        if data["client"].specialending != "":
            data["client"].specialending == ""
            data["client"].sendServerMessage("XMas Special Ending has been disabled.")
        else:
            data["client"].specialending = self.specialendings[random.randint(0, len(self.specialendings) - 1)]
            data["client"].sendServerMessage("XMas Special Ending has been enabled.")

serverPlugin = XMasPlugin