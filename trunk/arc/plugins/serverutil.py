# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

try:
    import psutil
except ImportError:
    nopsutils = True
else:
    nopsutils = False
from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *

class ServerUtilPlugin():
    name = "ServerUtilPlugin"

    hooks = {
        "heartbeatSent": "onHeartbeat"
    }

    commands = {
        "sinfo": "commandServerInfo",
        "worldsoper": "commandWorldsOper",
        "restartloop": "commandRestartLoop",
        "sendhb": "commandSendHeartBeat"
    }

    def gotServer(self):
        if nopsutils:
            self.logger.warn("PSUtils module not found. No system information available.")

    def calculateSystemUsage(self):
        if not nopsutils:
            cpuall = psutil.cpu_percent(interval=0)
            cores = len(psutil.cpu_percent(interval=0, percpu=True))
            diskusage = psutil.disk_usage("/")
            physramusage = psutil.phymem_usage()
            virtramusage = psutil.virtmem_usage()
            processes = len(psutil.get_pid_list())
            theList = [cpuall, cores, diskusage[3], physramusage[3], virtramusage[3], processes]
            return theList
        else:
            return False

    def onHeartbeat(self, data=None):
        if not nopsutils:
            usageList = self.calculateSystemUsage()
            cpucores = psutil.cpu_percent(interval=0, percpu=True)
            cores = len(psutil.cpu_percent(interval=0, percpu=True))
            self.logger.info("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % 
                (usageList[0], usageList[1], usageList[2], usageList[3], usageList[4], usageList[5]))
            if cores == 1:
                self.logger.debug("CPU: %s%% (in one core)" % usageList[0])
            elif cores > 1:
                done = ""
                i = 1
                for element in cpucores:
                    done = done + ("%s: %s%%, " % (i, element))
                    i = i + 1
                done = done[0:(len(done) - 2)]
                self.logger.debug("CPU: %s%% (%s)" % (usageList[0], done))

    @config("rank", "admin")
    @config("disabled-on", ["irc"])
    def commandWorldsOper(self, data):
        "Performs mass world operations.\nDo /worldsoper help for more information."
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("Syntax: /worldsoper action or /worldsoper help action")
            return
        action = data["parts"][1].lower()
        if action not in ["shutdownall", "saveall", "help"]:
            data["client"].sendServerMessage("Unknown action %s" % action)
            data["client"].sendServerMessage("Available actions: shutdownall saveall help")
            return
        if action == "help":
            if len(data["parts"]) > 3:
                subject = data["parts"][2].lower()
                data["client"].sendServerMessage("Help for %s:" % subject)
                if subject == "shutdownall":
                    data["client"].sendServerMessage("This shuts down all worlds with nobody in it.")
                elif subject == "saveall":
                    data["client"].sendServerMessage("This forces a save on all worlds and server rank settings.")
                else:
                    data["client"].SendServerMessage("No help found for %s." % subject)
            else:
                data["client"].sendServerMessage("Available actions: shutdownall saveall")
                data["client"].sendServerMessage("Please do /worldsoper help action to view help for that action.")
            return
        loopsToReschedule = []
        # Do we need to reschedule the saveWorlds and backup loop?
        if action in ["shutdownall", "saveall"]:
            loopsToReschedule.append("saveworlds")
        elif action == "shutdownall":
            loopsToReschedule.append("backup")
            # Firstly, stop the loops.
        for loop in loopsToReschedule:
            if data["client"].factory.loops[loop].running:
                data["client"].factory.loops[loop].stop()
            # Okay, let's continue with the main job.
        if action == "shutdownall":
            data["client"].sendServerMessage("Shutting down all empty worlds...")
            i = 0

            def doShutdown():
                for world in self.factory.worlds.values():
                    if world.id == self.factory.default_name:
                        continue
                    if world.clients == set():
                        self.factory.unloadWorld(world.id)
                        i += 1
                        yield

            shutdownIter = iter(doShutdown())

            def doStep():
                try:
                    shutdownIter.next()
                    reactor.callLater(0.1, doStep)
                except StopIteration:
                    data["client"].sendServerMessage("%s empty world(s) have been shut down." % i)
                    pass

            doStep()
        elif action == "saveall":
            data["client"].sendServerMessage("Saving all worlds...")
            self.factory.saveWorlds()
            data["client"].sendServerMessage("All online worlds saved.")
            # Restart the loops
        for loop in loopsToReschedule:
            self.factory.loops[loop].start(self.factory.loops[loop].interval,
                self.factory.loops[loop]._runAtStart)

    def commandServerInfo(self, data):
        "Displays server information."
        if nopsutils:
            data["client"].sendServerMessage("System information plugin disabled, unable to display system information.")
            return
        usageList = self.calculateSystemUsage()
        data["client"].sendSplitServerMessage("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % usageList)

    @config("rank", "owner")
    @config("disabled-on", ["cmdblock"])
    def commandRestartLoop(self, data):
        "Restarts a factory loop.\nUSE AT YOUR OWN RISK!"
        if len(data["parts"]) < 2:
            data["client"].sendServerMessage("You need to specify the loop and the time.")
            return
        if data["parts"][1] not in self.factory.loops:
            data["client"].sendServerMessage("That loop does not exist in the server loops directory.")
        else:
            self.factory.loop[data["parts"][1]].stop()
            self.factory.loop[data["parts"][1]].start(data["parts"][2])
            data["client"].sendServerMessage("Loop %s restarted." % data["parts"][1])

    @config("rank", "admin")
    @config("disabled-on", ["cmdblock"])
    def commandSendHeartBeat(self, data):
        "Sends a single heartbeat."
        self.factory.heartbeat.sendHeartbeat()
        data["client"].sendServerMessage("Heartbeat sent.")

serverPlugin = ServerUtilPlugin
