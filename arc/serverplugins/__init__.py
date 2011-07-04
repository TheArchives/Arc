# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys
from arc.logger import ColouredLogger

class ServerPlugin(object):
    """
    Parent object all server plugins inherit from.
    TODO: Make use of PluginMetaclass to register ServerPlugin to factory.
    """

    def __init__(self, factory):
        # Store the factory
        self.factory = factory
        self.logger = ColouredLogger(debug)
        # Register our hooks
        if hasattr(self, "hooks"):
            for name, fname in self.hooks.items():
                try:
                    self.factory.registerHook(name, getattr(self, fname))
                except AttributeError:
                    # Nope, can't find the method for that hook. Return error
                    self.logger.error("Cannot find hook code for %s." % fname)
        # Call clean setup method
        self.gotServer()

debug = (True if "--debug" in sys.argv else False)
logger = ColouredLogger()
logger.debug("Imported arc/serverplugins/ folder.")
del logger
del ColouredLogger
del sys