# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

"""
Decorators for command methods.
"""

from arc.globals import recursive_default

def config(key, value):
    "Decorator that writes to the configuration of the command."

    def config_inner(func):
        if getattr(func, "config", None) is None:
            func.config = recursive_default()
        func.config[key] = value
        return func

    return config_inner


def username_command(func):
    "Decorator for commands that accept a single username parameter, and need a Client"

    def inner(self, data):
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify a username.")
            return
        names = []
        user = data["parts"][1].lower()
        for username in self.factory.usernames:
            if user in username:
                names.append(username)
        if len(names) == 1:
            user = names[0]
        if not user in self.factory.usernames:
            data["client"].sendServerMessage("No such user '%s' (3+ chars?)" % user)
            return
        data["user"] = self.factory.usernames[names[0]]
        if len(data["parts"]) > 2:
            del data["parts"][1]
        func(self, data)

    inner.__doc__ = func.__doc__
    return inner


def only_string_command(string_name):
    def only_inner(func):
        "Decorator for commands that accept a single username/plugin/etc parameter, and don't need it checked"

        def inner(self, data):
            if len(data["parts"]) == 1:
                data["client"].sendServerMessage("Please specify %s %s." % (("an" if string_name[0] in "aeiou" else "a"), string_name))
            elif len(data["parts"]) > 2:
                data["client"].sendServerMessage("You specified too many arguments.")
            else:
                func(self, data)

        inner.__doc__ = func.__doc__
        return inner

    return only_inner

only_username_command = only_string_command("username")

def on_off_command(func):
    "Decorator for commands that accept a single on/off parameter"

    def inner(self, data):
        if len(data["parts"]) == 1:
            data["client"].sendServerMessage("Please specify 'On' or 'Off'.")
            return
        if parts[1].lower() not in ["on", "off"]:
            data["client"].sendServerMessage("Use 'on' or 'off', not '%s'" % parts[1])
        else:
            data["onoff"] = data["parts"][1]
            del data["parts"][1]
            func(self, data)

    inner.__doc__ = func.__doc__
    return inner