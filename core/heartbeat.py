import asyncore, logging, time, traceback, urllib, urllib2

from twisted.internet import reactor

from core.constants import *

class Heartbeat(object):
    """
    Deals with registering with the Minecraft main server every so often.
    The Salt is also used to help verify users' identities.
    """

    def __init__(self, factory):
        self.factory = factory
        self.logger = logging.getLogger("Heartbeat")
        self.turl()

    def turl(self):
        try:
            asyncore.dispatcher.__init__(self.get_url)
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
            open('config/data/SERVERURL', 'w').write(self.url)
            #fh = urllib2.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
            #"port": CHANGETHEPORT,
            #"users": len(self.factory.clients),
            #"max": self.factory.max_clients,
            #"name": "more servers here",
            #"public": self.factory.public,
            #"version": 7,
            #"salt": self.factory.salt,
            #}), 30)
            #self.url2 = fh.read().strip()
            if not self.factory.console.is_alive():
                self.factory.console.run()
        except urllib2.URLError as r:
            self.logger.error("Minecraft.net seems to be offline: %s" % r)
        except:
            self.logger.error(traceback.format_exc())
        finally:
            if not onetime:
                reactor.callLater(60, self.get_url)