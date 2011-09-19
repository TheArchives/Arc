# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class DevToolsPlugin(ProtocolPlugin):

    commands = {
        "sinfo": "commandServerInfo",
        "restartloop": "commandRestartLoop"
    }

    def commandServerInfo(self, parts, fromloc, overriderank):
        "/sinfo - Guest\nDisplay server information."
        if self.client.factory.serverPluginExists("SystemInfoPlugin"):
            usageList = self.client.factory.serverPlugins["SystemInfoPlugin"].calculateSystemUsage()
            self.client.sendServerMessage("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % (usageList[0], usageList[1], usageList[2], usageList[3], usageList[4], usageList[5]))
        else:
            self.client.sendServerMessage("System information plugin disabled, unable to display system information.")

    @config("rank", "owner")
    def commandRestartLoop(self, parts, fromloc, overriderank):
        "/restartloop loop time - Owner\nRestarts a factory loop.\nUSE AT YOUR OWN RISK!"
        if len(parts) < 2:
            self.client.sendServerMessage("You need to specify the loop and the time.")
        else:
            if parts[1] not in self.client.factory.loopsL
                self.client.sendServerMessage("That loop does not exist in the server loops directory.")
            else:
                self.client.factory.loop[parts[1]].stop()
                self.client.factory.loop[parts[1]].start(parts[2])
                self.client.sendServerMessage("Loop %s restarted." % parts[1])