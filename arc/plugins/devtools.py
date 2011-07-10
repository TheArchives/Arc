# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class DevToolsPlugin(ProtocolPlugin):

    commands = {
        "sinfo": "commandServerInfo",
    }

    def commandServerInfo(self, parts, fromloc, overriderank):
        usageList = self.client.factory.serverPlugins["SystemInfoPlugin"].calculateSystemUsage()
        self.client.sendServerMessage("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % (usageList[0], usageList[1], usageList[2], usageList[3], usageList[4], usageList[5]))
