# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import *

class ServerUtilPlugin(ProtocolPlugin):
    commands = {
        "worldsoper": "commandWorldsOper",
        "sinfo": "commandServerInfo",
        "restartloop": "commandRestartLoop"
    }

    @config("rank", "admin")
    def commandWorldsOper(self, parts, fromloc, overriderank):
        "/worldsoper shutdownall|saveall|help [action] - Admin\nPerforms mass world operations.\nDo /worldsoper help [action] for more information on a specific action."
        if len(parts) < 1:
            self.client.sendServerMessage("Syntax: /worldsoper action or /worldsoper help action")
            return
        elif parts[1] not in ["shutdownall", "saveall", "help"]:
            self.client.sendServerMessage("Unknown action %s" % parts[1])
            self.client.sendServerMessage("Available actions: shutdownall saveall help")
            return
        loopsToReschedule = []
        # Do we need to reschedule the saveWorlds and backup loop?
        if parts[1] in ["shutdownall", "saveall"]:
            loopsToReschedule.append("saveworlds")
        elif parts[1] == "shutdownall":
            loopsToReschedule.append("backup")
        # Firstly, stop the loops.
        for loop in loopsToReschedule:
            if self.client.factory.loops[loop].running:
                self.client.factory.loops[loop].stop()
        # Okay, let's continue with the main job.
        if parts[1] == "shutdownall":
            self.client.sendServerMessage("Shutting down all empty worlds...")
            self.value = 0
            def doShutdown():
                for world in self.client.factory.worlds.values():
                    if world.id == self.client.factory.default_name:
                        continue
                    if world.clients == set():
                        self.client.factory.unloadWorld(world.id)
                        self.value += 1
                        yield
            shutdownIter = iter(doShutdown())
            def doStep():
                try:
                    shutdownIter.next()
                    reactor.callLater(0.1, doStep)
                except StopIteration:
                    if fromloc == "user":
                        self.client.sendServerMessage("%s empty world(s) have been shut down." % self.value)
                    del self.value
                    pass
            doStep()
        elif parts[1] == "saveall":
            self.client.sendServerMessage("Saving all worlds...")
            self.client.factory.saveWorlds()
            self.client.sendServerMessage("All online worlds saved.")
        # Restart the loops
        for loop in loopsToReschedule:
            self.client.factory.loops[loop].start(self.client.factory.loops[loop].interval, self.client.factory.loops[loop]._runAtStart)

    def commandServerInfo(self, parts, fromloc, overriderank):
        "/sinfo - Guest\nDisplay server information."
        if self.client.factory.serverPluginExists("SystemInfoPlugin"):
            usageList = self.client.factory.serverPlugins["SystemInfoPlugin"].calculateSystemUsage()
            self.client.sendSplitServerMessage("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % (usageList[0], usageList[1], usageList[2], usageList[3], usageList[4], usageList[5]))
        else:
            self.client.sendServerMessage("System information plugin disabled, unable to display system information.")

    @config("rank", "owner")
    def commandRestartLoop(self, parts, fromloc, overriderank):
        "/restartloop loop time - Owner\nRestarts a factory loop.\nUSE AT YOUR OWN RISK!"
        if len(parts) < 2:
            self.client.sendServerMessage("You need to specify the loop and the time.")
        else:
            if parts[1] not in self.client.factory.loops:
                self.client.sendServerMessage("That loop does not exist in the server loops directory.")
            else:
                self.client.factory.loop[parts[1]].stop()
                self.client.factory.loop[parts[1]].start(parts[2])
                self.client.sendServerMessage("Loop %s restarted." % parts[1])