# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *

class InteractionPlugin():

    commands = {
        "say": "commandSay"
    }

    @config("rank", "admin")
    def commandSay(self, parts, triggeredBy, channel):
        "$say channel message - Admin | Says something in a channel the bot has joined."
        if parts[1].lower() in self.client.channels:
            self.client.msg(parts[1].lower(), " ".join(parts[2:]))
        else:
            self.client.msg(channel, "I'm not on %s." % parts[1])

ircPlugin = InteractionPlugin