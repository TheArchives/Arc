# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, threading, time, urllib

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.defer import TimeoutError
from twisted.web.error import Error as twistedError
from twisted.web.client import getPage

from arc.constants import *
from arc.logger import ColouredLogger

import logging

debug = (True if "--debug" in sys.argv else False)

class Heartbeat(object):
    """
    Deals with registering with the Minecraft main server every so often.
    The Salt is also used to help verify users' identities.
    Direct WoM Heartbeat info can be changed at https://direct.worldofminecraft.com/server.php
    """

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.hburl = "http://www.minecraft.net/heartbeat.jsp" if not self.factory.wom_heartbeat else "http://direct.worldofminecraft.com/hb.php"
        self.loop = LoopingCall(self.sendHeartbeat)
        self.loop.start(25) # In the future for every spoofed heartbeat it would deduct by 2 seconds, but not now
        self.logger.info("Heartbeat sending process initiated.")
        self.factory.runHook("heartbeatBuilt")

    def buildHeartbeatData(self):
        # To be extended
        return urllib.urlencode({
            "port": self.factory.server_port,
            "users": len(self.factory.clients),
            "max": self.factory.max_clients,
            "name": self.factory.server_name,
            "public": self.factory.public,
            "version": 7,
            "salt": self.factory.salt,
            })

    def sendHeartbeat(self):
        try:
            getattr(self.factory, "wom_heartbeat")
        except AttributeError:
            reactor.callLater(3, self.sendHeartbeat) 
            return
        try:
            getattr(self.factory, "heartbeats")
        except AttributeError:
            if self.factory.hbs != []: # Did we fill in the spoof heartbeat bit?
                reactor.callLater(3, self.sendHeartbeat) # Server has not finished loading yet - come back in 3 seconds maybe?
            return
        d = dict()
        d[0] = getPage(self.hburl, method="POST", postdata=self.buildHeartbeatData(), headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
        d[0].addCallback(self.heartbeatSentCallback, 0)
        d[0].addErrback(self.heartbeatFailedCallback, 0)
        for element, valueset in self.factory.heartbeats.iteritems():
            spoofdata = urllib.urlencode({
                "port": valueset[1],
                "users": len(self.factory.clients),
                "max": self.factory.max_clients,
                "name": valueset[0],
                "public": self.factory.public,
                "version": 7,
                "salt": self.factory.salt,
                })
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
            self.factory.runHook("heartbeatSent")
        else:
            self.logger.info("Spoof heartbeat for %s sent." % self.factory.heartbeats[id][0])

    def heartbeatFailedCallback(self, err, id):
        if isinstance(err, TimeoutError):
            self.logger.error("Heartbeat sending%s timed out." % ("" if id == 0 else " to "+self.factory.heartbeats[id][0]))
        elif isinstance(err, twistedError):
            if id == 0:
                self.logger.error("Heartbeat failed to send. Error:")
            else:
                self.logger.error("Spoof heartbeat for %s could not be sent. Error:" % self.factory.heartbeats[id][0])
            self.logger.error(str(err))
        else:
            self.logger.error("Unexpected error in heartbeat sending process%s. Error:" % ("" if id == 0 else " to "+self.factory.heartbeats[id][0]))
            self.logger.error(str(err))