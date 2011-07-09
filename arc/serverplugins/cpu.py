# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import psutil

class CpuServerPlugin():

    name = "CPUPlugin"
    errored = False

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        
    def onHeartbeat(self, data=None):
        if not self.errored:
            cpuall = psutil.cpu_percent(interval=0)
            cpucores = psutil.cpu_percent(interval=0, percpu=True)
            cores = len(cpucores)
            if cores == 1:
                self.logger.info("CPU usage: %s%% (in one core)" % cpuall)
            elif cores > 1:
                done = ""
                i = 1
                for element in cpucores:
                    done = done + ("%s: %s%%, " % (i, element))
                    i = i + 1
                done = done[0:(len(done)-2)]
                self.logger.info("CPU usage: %s%% (%s)" % (cpuall, done))
        
    hooks = {
        "heartbeatSent": onHeartbeat
    }
        
serverPlugin = CpuServerPlugin
