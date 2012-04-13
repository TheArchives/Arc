# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os, sys

from arc.constants import *
from arc.decorators import *

class CorePlugin(object):
    properties = {
        "allow-reload": False,
        "allow-unload": False,
    }
    commands = {
        "pll": "commandPluginLoad",
        "plu": "commandPluginUnload",
        "plr": "commandPluginReload",
        "pllist": "commandPluginList",
        }

    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled-on", ["cmdblock"])
    def commandPluginReload(self, data):
        if not (data["parts"][1].lower() in self.factory.plugins.keys()): # Check if we have imported it
            data["client"].sendServerMessage("Plugin %s is not loaded." % data["parts"][1].lower())
            return
        self.factory.unloadPlugin(data["parts"][1].lower(), client=data["client"])
        self.factory.loadPlugin(data["parts"][1].lower(), client=data["client"])

    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled-on", ["cmdblock"])
    def commandPluginLoad(self, data):
        self.factory.loadPlugin(data["parts"][1].lower(), client=data["client"])

    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled-on", ["cmdblock"])
    def commandPluginUnload(self, data):
        self.factory.unloadPlugin(data["parts"][1].lower(), client=data["client"])

    @config("rank", "admin")
    def commandPluginList(self, data):
        "Shows all plugins."
        pluginlist = os.listdir("arc/plugins")
        newpluginlist = []
        for plugin in pluginlist:
            if not plugin.endswith(".pyc"):
                plugin = plugin.replace(".py", "")
                newpluginlist.append(plugin)
        data["client"].sendServerList(["Plugins:"] + newpluginlist)

serverPlugin = CorePlugin