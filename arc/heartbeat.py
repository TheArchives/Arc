# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, threading, time, traceback, urllib

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.web import error as twistedError
from twisted.web.client import getPage

from arc.constants import *
from arc.logger import ColouredLogger

import logging

debug = (True if "--debug" in sys.argv else False)

class Heartbeat(object):
    """
    Deals with registering with the Minecraft main server every so often.
    The Salt is also used to help verify users' identities.
    """

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.hburl = "http://www.minecraft.net/heartbeat.jsp" if not self.factory.wom_heartbeat else "http://direct.worldofminecraft.com/hb.php"
        self.hbdata = ""
        self.hbservers = dict()
        self.loop = LoopingCall(self.sendHeartbeat)
        self.loop.start(25) # In the future for every spoofed heartbeat it would deduct by 2 seconds, but not now
        self.logger.info("Heartbeat sending process initiated.")
        self.factory.runServerHook("heartbeatBuilt")

    def buildHeartbeatData(self):
        # To be extended
        return urllib.urlencode({
            "port": self.factory.config.getint("network", "port"),
            "users": len(self.factory.clients),
            "max": self.factory.max_clients,
            "name": self.factory.server_name,
            "public": self.factory.public,
            "version": 7,
            "salt": self.factory.salt,
            })

    def sendHeartbeat(self):
        d = dict()
        try:
            d[0] = getPage(self.hburl, method="POST", postdata=self.buildHeartbeatData(), headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
            d[0].addCallback(self.heartbeatSentCallback, 0)
            d[0].addErrback(self.heartbeatFailedCallback, 0)
        except:
            self.logger.error(traceback.format_exc())
            self.factory.last_heartbeat = time.time()
        else:
            for element in self.factory.heartbeats:
                for valueset in self.factory.heartbeats.values():
                    spoofdata = urllib.urlencode({
                        "port": valueset[1],
                        "users": len(self.factory.clients),
                        "max": self.factory.max_clients,
                        "name": valueset[0],
                        "public": self.factory.public,
                        "version": 7,
                        "salt": self.factory.salt,
                        })
                    self.factory.last_heartbeat = time.time()
                    d[element] = getPage(self.hburl, method="POST", postdata=spoofdata, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
                    d[element].addCallback(self.heartbeatSentCallback, element)
                    d[element].addErrback(self.heartbeatFailedCallback, element)

    def heartbeatSentCallback(self, result, id):
        if id == 0:
            self.url = result
            self.logger.info("Heartbeat Sent. URL (saved to docs/SERVERURL): %s" % self.url)
            fh = open('config/data/SERVERURL', 'w')
            fh.write(self.url)
            fh.flush()
            fh.close()
            self.factory.runServerHook("heartbeatSent")
        else:
            self.logger.info("Spoof heartbeat for %s sent." % self.factory.heartbeats[id])

    def heartbeatFailedCallback(self, err, id):
        if isinstance(err, twistedError.Error):
            if id == 0:
                self.logger.error("Heartbeat failed to send. Error:")
            else:
                self.logger.info("Spoof heartbeat for %s could not be sent. Error:" % self.factory.heartbeats[id])
            self.logger.error(str(err))
        else:
            raise err