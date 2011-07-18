# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, threading, time, traceback, urllib, urllib2

from twisted.internet import reactor
from random import randint

from arc.constants import *
from arc.logger import ColouredLogger

import logging

debug = (True if "--debug" in sys.argv else False)

class Heartbeat(threading.Thread):
    """
    Deals with registering with the Minecraft main server every so often.
    The Salt is also used to help verify users' identities.
    """

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.factory.runServerHook("heartbeatBuilt")
        self.turl()

    def turl(self):
        try:
            threading.Thread(target=self.get_url).start()
        except:
            self.logger.error(traceback.format_exc())
            reactor.callLater(1, self.turl)

    def get_url(self, onetime=False):
        try:
            self.factory.last_heartbeat = time.time()
            fh = urllib2.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
            "port": self.factory.config.getint("network", "port"),
            "users": len(self.factory.clients),
            "max": self.factory.max_clients,
            "name": self.factory.server_name,
            "public": self.factory.public,
            "version": 7,
            "salt": self.factory.salt,
            }), 30)
            self.url = fh.read().strip()
            self.logger.info("Heartbeat Sent. Your URL (saved to docs/SERVERURL): %s" % self.url)
            fh = open('config/data/SERVERURL', 'w')
            fh.write(self.url)
            fh.flush()
            fh.close()
            self.factory.runServerHook("heartbeatSent")
            if not self.factory.console.is_alive():
                self.factory.console.run()
        except urllib2.URLError as r:
            self.logger.error("Minecraft.net seems to be offline: %s" % r)
        except:
            self.logger.error(traceback.format_exc())
        i = 0
        for element in self.factory.heartbeats:
            if i > 5:
                break
            try:
                self.factory.last_heartbeat = time.time()
                fh = urllib2.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
                "port": element[1],
                "users": len(self.factory.clients),
                "max": self.factory.max_clients,
                "name": element[0],
                "public": self.factory.public,
                "version": 7,
                "salt": self.factory.salt,
                }), 30)
                self.logger.debug("Spoofed heartbeat: %s" % element[0])
            except:
                pass
        if not onetime:
            reactor.callLater(60, self.get_url)