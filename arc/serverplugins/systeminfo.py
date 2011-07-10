# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

try:
    import psutil
except ImportError:
    import reqs.psutil

class SystemInfoServerPlugin():

    hooks = {
        "heartbeatSent": onHeartbeat
    }

    name = "SystemInfoPlugin"
    errored = False

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger

    def calculateSystemUsage(self):
        cpuall = psutil.cpu_percent(interval=0)
        cores = len(cpucores)
        diskusage = psutil.disk_usage("/")
        physramusage = psutil.phymem_usage()
        virtramusage = psutil.virtmem_usage()
        processes = len(psutil.get_pid_list())
        theDict = {cpuall, cores, diskusage[3], physramusage[3], virtramusage[3], processes}
        return theDict

    def onHeartbeat(self, data=None):
        usageDict = self.calculateSystemUsage
        cpucores = psutil.cpu_percent(interval=0, percpu=True)
        self.logger.info("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % (usageDict))
        if cores == 1:
            self.logger.debug("CPU: %s%% (in one core)" % usageDict[0])
        elif cores > 1:
            done = ""
            i = 1
            for element in cpucores:
                done = done + ("%s: %s%%, " % (i, element))
                i = i + 1
            done = done[0:(len(done)-2)]
            self.logger.debug("CPU: %s%% (%s)" % (usageDict[0], done))

serverPlugin = SystemInfoServerPlugin
