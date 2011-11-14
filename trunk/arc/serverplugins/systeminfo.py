# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import psutil

class SystemInfoServerPlugin():
    name = "SystemInfoPlugin"
    
    hooks = {
        "heartbeatSent": "onHeartbeat"
    }

    def calculateSystemUsage(self):
        cpuall = psutil.cpu_percent(interval=0)
        cores = len(psutil.cpu_percent(interval=0, percpu=True))
        diskusage = psutil.disk_usage("/")
        physramusage = psutil.phymem_usage()
        virtramusage = psutil.virtmem_usage()
        processes = len(psutil.get_pid_list())
        theList = [cpuall, cores, diskusage[3], physramusage[3], virtramusage[3], processes]
        return theList

    def onHeartbeat(self, data=None):
        usageList = self.calculateSystemUsage()
        cpucores = psutil.cpu_percent(interval=0, percpu=True)
        cores = len(psutil.cpu_percent(interval=0, percpu=True))
        self.logger.info("CPU USAGE: %s%% (%s cores), DISK USAGE: %s%%, RAM USAGE: %s%% physical, %s%% virtual, PROCESSES: %s" % (usageList[0], usageList[1], usageList[2], usageList[3], usageList[4], usageList[5]))
        if cores == 1:
            self.logger.debug("CPU: %s%% (in one core)" % usageList[0])
        elif cores > 1:
            done = ""
            i = 1
            for element in cpucores:
                done = done + ("%s: %s%%, " % (i, element))
                i = i + 1
            done = done[0:(len(done)-2)]
            self.logger.debug("CPU: %s%% (%s)" % (usageList[0], done))

serverPlugin = SystemInfoServerPlugin
