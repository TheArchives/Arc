# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

#!/usr/bin/python

import datetime, logging, sys, time, traceback, os
from ConfigParser import RawConfigParser as ConfigParser

from twisted.internet import reactor
from twisted.internet.error import CannotListenError

from arc.logger import ColouredLogger

debug = (True if "--debug" in sys.argv else False)
logger = ColouredLogger(debug)

try:
    from colorama import init
    init()
    logger.stdout("&f")
    logger.debug("&fIf you see this, debug mode is &eon&f!")
    logger.info("&fColorama &ainstalled&f - Console colours &cENABLED&f.")
except ImportError:
    logger.warn("Colorama is not installed - console colours DISABLED.")
except Exception as e:
    logger.warn("Unable to import colorama: %s" % e)
    logger.warn("Console colours DISABLED.")

from arc.controller import ControllerFactory
from arc.constants import *
from arc.globals import *
from arc.server import ArcFactory

def doExit():
    if os.name == "nt":
        raw_input("\nYou may now close the server console window.")
    else:
        raw_input("\nPlease press enter to exit.")

def main():
    global logger

    makefile("logs/")
    makefile("logs/console/")
    makefile("logs/console/console.log")
    makefile("arc/archives/")
    makefile("logs/chat.log")
    makefile("logs/server.log")
    makefile("logs/staff.log")
    makefile("logs/whisper.log")
    makefile("logs/world.log")
    makefile("config/data/")
    makedatfile("config/data/balances.dat")
    makedatfile("config/data/inbox.dat")
    makedatfile("config/data/jail.dat")
    makedatfile("config/data/titles.dat")

    #logging.basicConfig(
    #    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    #    level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
    #    datefmt="%m/%d/%Y %H:%M:%S",
    #)

    #rotate = logging.handlers.TimedRotatingFileHandler(
    #    filename="logs/console/console.log", when="H",
    #    interval=6, backupCount=14,
    #)
    #logging.root.addHandler(rotate)

    logger.info("Starting up &bArc&f v%s" % VERSION)
    factory = ArcFactory(debug)
    try:
        factory.ip = reactor.listenTCP(factory.server_port, factory).getHost()
    except CannotListenError:
        logger.critical("Something is already running on port %s" % (factory.server))
        doExit()
    if factory.use_controller:
        controller = ControllerFactory(factory)
        try:
            reactor.listenTCP(factory.controller_port, controller)
        except CannotListenError as a:
            logger.warning("Controller cannot listen on port %s. Disabled." % factory.controller_port)
            logger.warning("Error: %s" % a)
            del controller
    # TODO: Well...
    money_logger = logging.getLogger('TransactionLogger')
    fh = logging.FileHandler('logs/server.log')
    formatter = logging.Formatter("%(asctime)s: %(message)s")
    fh.setFormatter(formatter)
    money_logger.addHandler(fh)
    config = ConfigParser()
    config.read("config/main.conf") # This can't fail because it has been checked before
    factory.heartbeats = dict()
    for element in factory.hbs:
        name = config.get("heartbeatnames", element)
        port = config.getint("heartbeatports", element)
        factory.heartbeats[element] = (name, port)
        reactor.listenTCP(port, self)
        logger.info("Starting spoofed heartbeat %s on port %s..." % (name, port))
    try:
        reactor.run()
    except Exception as e:
        if e not in ["KeyboardInterrupt", "SystemExit"]:
            logger.critical("The server has encountered a critical error and is shutting down.")
            logger.critical("Details about the error can be found in crashlog.txt")
            makefile("crashlog.txt")
            with open("crashlog.txt", "a") as f:
                f.write("=" * 10 + " START CRASH REPORT " + "=" * 10 + "\n")
                f.write("Crash date: %s\n" % time.strftime("%c", time.gmtime()))
                traceback.print_exc(file=f)
                f.write("=" * 11 + " END CRASH REPORT " + "=" * 11 + "\n")
                f.close()
        else:
            logger.info("Shutting down...")
    finally:
        logger.info("Saving server metas...")
        factory.saveMeta()
        logger.info("Flushing worlds to disk...")
        for world in factory.worlds.values():
            logger.info("Saving: %s" % world.basename)
            world.stop()
            world.save_meta()
        logger.info("Done flushing...")
        doExit()

if __name__ == "__main__":
    main()