# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *

class CorePlugin(object):
    commands = {
        "load": "commandLoad",
        "unload": "commandUnload",
    }

    @config("rank", "admin")
    def commandLoad(self, parts, triggeredBy, channel):
        "$load module1(, module2, module3, ...) - Admins | Loads the given module names."
        for mod in parts[2:]:
            toSend = (triggeredBy if triggeredBy == channel else channel)
            self.client.loadModule(mod, toSend)

    @config("rank", "admin")
    def commandUnload(self, parts, triggeredBy, channel):
        "$unload module1(, module2, module3, ...) - Admins | Unloads the given module names."
        for mod in parts[2:]:
            toSend = (triggeredBy if triggeredBy == channel else channel)
            self.client.loadModule(mod, toSend)

ircPlugin = CorePlugin