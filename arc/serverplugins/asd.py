# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet.task import LoopingCall

class AutoShutdownServerPlugin():

    name = "AutoShutdownPlugin"

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.loop = LoopingCall(checkWorld)
        self.times = dict()
        
    def checkWorlds(self):
        # Check the worlds
        if self.client.factory.worlds.keys() != list("default"): # We don't care about default :P
            

    hooks = {
        "onWorldMetaLoaded": onWorldMetaLoaded
    }

serverPlugin = AutoShutdownServerPlugin
