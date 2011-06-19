#!/usr/bin/python

import datetime, logging, sys, time, traceback

from twisted.internet import reactor
from twisted.internet.error import CannotListenError

from core.logger import ColouredLogger

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

from core.controller import ControllerFactory
from core.constants import *
from core.globals import *
from core.server import CoreFactory



def doExit():
    raw_input("\nPlease press enter to exit.")

def main():  
    debug = (True if "--debug" in sys.argv else False)
    logger = ColouredLogger(debug)

    makefile("logs/")
    makefile("logs/console/")
    makefile("logs/console/console.log")
    makefile("core/archives/")
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
    '''
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
        datefmt="%m/%d/%Y %H:%M:%S",
    )

    rotate = logging.handlers.TimedRotatingFileHandler(
        filename="logs/console/console.log", when="H",
        interval=6, backupCount=14,
    )
    logging.root.addHandler(rotate)

    logger = logging.getLogger("iCraft")
    '''
    logger.info("Now starting up iCraft+ 1G version %s..." % VERSION)
    factory = CoreFactory(debug)
    try:
        factory.ip = reactor.listenTCP(factory.config.getint("network", "port"), factory).getHost()
        reactor.listenTCP(30000, factory)
    except CannotListenError:
        logger.critical("Something is already running on port %s" % (factory.config.getint("network", "port")))
        doExit()
    controller = ControllerFactory(factory)
    try:
        reactor.listenTCP(factory.config.getint("network", "controller_port"), controller)
    except CannotListenError:
        logger.warning("Controller cannot listen on port %s. Disabled." % factory.config.getint("network", "port"))
        del controller
    # TODO: Well...
    money_logger = logging.getLogger('TransactionLogger')
    fh = logging.FileHandler('logs/server.log')
    formatter = logging.Formatter("%(asctime)s: %(message)s")
    fh.setFormatter(formatter)
    money_logger.addHandler(fh)

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