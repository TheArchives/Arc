# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import os

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class CorePlugin(ProtocolPlugin):
    
    commands = {
        "pll": "commandPluginload",
        "plu": "commandPluginunload",
        "plr": "commandPluginreload",
        "pllist": "commandPluginlist",
        "pllistall": "commandPluginlist",
    }
    
    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled_cmdblocks", True)
    def commandPluginreload(self, plugin_name, fromloc, overriderank):
        try:
            self.client.factory.unloadPlugin(plugin_name)
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' reloaded." % plugin_name)
    
    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled_cmdblocks", True)
    def commandPluginload(self, plugin_name, fromloc, overriderank):
        try:
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' loaded." % plugin_name)
    
    @config("rank", "admin")
    @only_string_command("plugin name")
    @config("disabled_cmdblocks", True)
    def commandPluginunload(self, plugin_name, fromloc, overriderank):
        try:
            self.client.factory.unloadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' unloaded." % plugin_name)

    @config("rank", "admin")
    def commandPluginlist(self, parts, fromloc, overriderank):
        "/pllist - Admin\nAliases: pllistall\nShows all plugins."
        pluginlist = os.listdir("arc/plugins")
        newpluginlist = []
        for plugin in pluginlist:
            if not plugin.endswith(".pyc"):
                plugin = plugin.replace(".py","")
                newpluginlist.append(plugin)
        self.client.sendServerList(["Plugins:"] + newpluginlist)