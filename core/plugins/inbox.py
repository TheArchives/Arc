import cPickle, traceback

from core.constants import *
from core.decorators import *
from core.plugins import ProtocolPlugin

class OfflineMessPlugin(ProtocolPlugin):

    commands = {
        "s": "commandSendMessage",
        "sendmessage": "commandSendMessage",
        "inbox": "commandCheckMessages",
        "c": "commandClear",
        "clear": "commandClear",
    }

    def commandSendMessage(self,parts, fromloc, overriderank):
        "/s username message - Guest\nAliases: sendmessage\nSends an message to the users Inbox."
        if len(parts) < 3:
            self.client.sendServerMessage("You must provide a username and a message.")
        else:
            try:
                from_user = self.client.username.lower()
                to_user = parts[1].lower()
                mess = " ".join(parts[2:])
                file = open('config/data/inbox.dat', 'r')
                messages = cPickle.load(file)
                file.close()
                if to_user in messages:
                    messages[to_user]+= "\n" + from_user + ": " + mess
                else:
                    messages[to_user] = from_user + ": " + mess
                file = open('config/data/inbox.dat', 'w')
                cPickle.dump(messages, file)
                file.close()
                self.client.factory.usernames[to_user].MessageAlert()
                self.client.sendServerMessage("A message has been sent to %s." % to_user)
            except:
                self.client.sendServerMessage("Error sending message.")

    def commandCheckMessages(self, parts, fromloc, overriderank):
        "/inbox - Guest\nChecks your Inbox of messages."
        file = open('config/data/inbox.dat', 'r')
        messages = cPickle.load(file)
        file.close()
        if self.client.username.lower() in messages:
            self.client._sendMessage(COLOUR_DARKPURPLE, messages[self.client.username.lower()])
            self.client.sendServerMessage("NOTE: Might want to do /c now.")
        else:
            self.client.sendServerMessage("You do not have any messages.")

    def commandClear(self,parts, fromloc, overriderank):
        "/c - Guest\nAliases: clear\nClears your Inbox of messages."
        target = self.client.username.lower()
        file = open('config/data/inbox.dat', 'r')
        messages = cPickle.load(file)
        file.close()
        if len(parts) == 2:
            target = parts[1]
        elif self.client.username.lower() not in messages:
            self.client.sendServerMessage("You have no messages to clear.")
            return False
        messages.pop(target)
        file = open('config/data/inbox.dat', 'w')
        cPickle.dump(messages, file)
        file.close()
        self.client.sendServerMessage("All your messages have been deleted.")
