import traceback, sys

from core.logger import ColouredLogger

debug=(True if "--debug" in sys.argv else False)
ColouredLogger(debug).debug("Imported plugins/ folder.")

protocol_plugins = []
server_plugins = []

class PluginMetaclass(type):

    """
    A metaclass which registers any subclasses of Plugin.
    """

    def __new__(cls, name, bases, dct):
        # Supercall
        new_cls = type.__new__(cls, name, bases, dct)
        debug = (True if "--debug" in sys.argv else False)
        logger = ColouredLogger(debug)
        # Register!
        if bases != (object,):
            if ProtocolPlugin in bases:
                logger.debug("Loaded protocol plugin: %s" % name)
                protocol_plugins.append(new_cls)
            elif ServerPlugin in bases:
                logger.debug("Loaded server plugin: %s" % name)
                server_plugins.append(new_cls)
            else:
                self.logger.warn("Plugin '%s' is not a server or a protocol plugin." % name)
        return new_cls

class ServerPlugin(object):
    """
    Parent object all server plugins inherit from.
    """

    __metaclass__ = PluginMetaclass

    def __init__(self, factory):
    # Store the factory
    # self.factory = factory
        pass

class ProtocolPlugin(object):
    """
    Parent object all plugins inherit from.
    """

    __metaclass__ = PluginMetaclass

    def __init__(self, client):
        debug = (True if "--debug" in sys.argv else False)
        self.logger = ColouredLogger(debug)
        # Store the client
        self.client = client
        # Register our commands
        if hasattr(self, "commands"):
            for name, fname in self.commands.items():
                try:
                    self.client.registerCommand(name, getattr(self, fname))
                except AttributeError:
                    # Nope, can't find the method for that command. Return error
                    self.logger.error("Cannot find command code for %s (command name is %s)." % (fname, name))
        # Register our hooks
        if hasattr(self, "hooks"):
            for name, fname in self.hooks.items():
                try:
                    self.client.registerHook(name, getattr(self, fname))
                except AttributeError:
                    # Nope, can't find the method for that hook. Return error
                    self.logger.error("Cannot find hook code for %s." % fname)
        # Call clean setup method

        self.gotClient()

    def unregister(self):
        # Unregister our commands
        if hasattr(self, "commands"):
            for name, fname in self.commands.items():
                self.client.unregisterCommand(name, getattr(self, fname))
        # Unregister our hooks
        if hasattr(self, "hooks"):
            for name, fname in self.hooks.items():
                self.client.unregisterHook(name, getattr(self, fname))
        del self.client

    def gotClient(self):
        pass

def load_plugins(plugins):
    "Given a list of plugin names, imports them so they register."
    debug=(True if "--debug" in sys.argv else False)
    logger = ColouredLogger(debug)
    for module_name in plugins:
        try:
            __import__("core.plugins.%s" % module_name)
        except ImportError:
            logger.error(traceback.format_exc())
            logger.error("Cannot load plugin %s." % module_name)

def unload_plugin(plugin_name):
    "Given a plugin name, reloads and re-imports its code."
    # Unload all its classes from our lists
    debug=(True if "--debug" in sys.argv else False)
    logger = ColouredLogger(debug)
    for plugin in plugins_by_module_name(plugin_name):
        if plugin in protocol_plugins:
            protocol_plugins.remove(plugin)
            logger.debug("Unloaded protocol plugin: %s" % plugin)
        if plugin in server_plugins:
            server_plugins.remove(plugin)
            logger.debug("Unloaded server plugin: %s" % plugin)

def load_plugin(plugin_name):
    # Reload the module, in case it was imported before
    try:
        reload(__import__("core.plugins.%s" % plugin_name, {}, {}, ["*"]))
    except ImportError:
        logger = ColouredLogger()
        logger.warn("No such plugin: %s" % plugin_name)

def plugins_by_module_name(module_name):
    "Given a module name, returns the plugin classes in it."
    debug=(True if "--debug" in sys.argv else False)
    logger = ColouredLogger(debug)
    try:
        module = __import__("core.plugins.%s" % module_name, {}, {}, ["*"])
    except ImportError:
        logger.warn("Unable to load plugin: %s" % module_name)
    except Exception as a:
        logger.warn("Unable to load plugin: %s" % module_name)
        logger.error("%s" % a)
    else:
        for name, val in module.__dict__.items():
            if isinstance(val, type):
                if issubclass(val, ProtocolPlugin) and val is not ProtocolPlugin:
                    yield val
                elif issubclass(val, ServerPlugin) and val is not ServerPlugin:
                    yield val
