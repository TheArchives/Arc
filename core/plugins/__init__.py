import traceback

from core.logger import ColouredLogger

protocol_plugins = []
server_plugins = []

class PluginMetaclass(type):

    """
    A metaclass which registers any subclasses of Plugin.
    """

    def __new__(cls, name, bases, dct):
        # Supercall
        new_cls = type.__new__(cls, name, bases, dct)
        logger = output()
        # Register!
        if bases != (object,):
            if ProtocolPlugin in bases:
                logger.debug("Loaded protocol plugin: %s" % name)
                protocol_plugins.append(new_cls)
            elif ServerPlugin in bases:
                logger.debug("Loaded server plugin: %s" % name)
                server_plugins.append(new_cls)
            else:
                logger.warn("Plugin '%s' is not a server or a protocol plugin." % name)
        return new_cls

class ServerPlugin(object): # Can't have default values here!
    """
    Parent object all plugins inherit from.
    """

    def __init__(self, factory):
    # Store the factory
    # self.factory = factory
        pass

class ProtocolPlugin(object): # Can't have default values here!
    """
    Parent object all plugins inherit from.
    """

    metaclass=PluginMetaclass
    
    def __init__(self, client):
        # Store the client
        self.client = client
        # Register our commands
        if hasattr(self, "commands"):
            for name, fname in self.commands.items():
                try:
                    self.client.registerCommand(name, getattr(self, fname))
                except AttributeError:
                    # Nope, can't find the method for that command. Return error
                    ColouredLogger().error("Cannot find command code for %s (command name is %s)." % (fname, name))
        # Register our hooks
        if hasattr(self, "hooks"):
            for name, fname in self.hooks.items():
                try:
                    self.client.registerHook(name, getattr(self, fname))
                except AttributeError:
                    # Nope, can't find the method for that hook. Return error
                    ColouredLogger().error("Cannot find hook code for %s." % fname)
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
    for module_name in plugins:
        try:
            __import__("core.plugins.%s" % module_name)
        except ImportError:
            ColouredLogger().error(traceback.format_exc())
            ColouredLogger().error("Cannot load plugin %s." % module_name)

def unload_plugin(plugin_name):
    "Given a plugin name, reloads and re-imports its code."
    # Unload all its classes from our lists
    for plugin in plugins_by_module_name(plugin_name):
        if plugin in protocol_plugins:
            protocol_plugins.remove(plugin)
        if plugin in server_plugins:
            server_plugins.remove(plugin)

def load_plugin(plugin_name):
    # Reload the module, in case it was imported before
    reload(__import__("core.plugins.%s" % plugin_name, {}, {}, ["*"]))
    load_plugins([plugin_name])

def plugins_by_module_name(module_name):
    "Given a module name, returns the plugin classes in it."
    try:
        module = __import__("core.plugins.%s" % module_name, {}, {}, ["*"])
    except ImportError:
        raise ValueError("Cannot load plugin %s." % module_name)
    else:
        for name, val in module.__dict__.items():
            if isinstance(val, type):
                if issubclass(val, ProtocolPlugin) and val is not ProtocolPlugin:
                    yield val
                elif issubclass(val, ServerPlugin) and val is not ServerPlugin:
                    yield val
