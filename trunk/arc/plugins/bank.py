# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, logging

from arc.decorators import *
from arc.plugins import ProtocolPlugin

class MoneyPlugin(ProtocolPlugin):

    commands = {
        "bank": "commandBalance",
        "balance": "commandBalance",
        "pay": "commandPay",
        "setbank": "commandSetAccount",
        "removebank": "commandRemoveAccount",
    }

    #System methods, not for commands
    def loadBank(self):
        file = open('config/data/balances.dat', 'r')
        bank_dic = cPickle.load(file)
        file.close()
        return bank_dic

    def dumpBank(self, bank_dic):
        file = open('config/data/balances.dat', 'w')
        cPickle.dump(bank_dic, file)
        file.close()

    def commandBalance(self, parts, fromloc, overriderank):
        "/bank - Guest\nAliases: balance\nFirst time: Creates you a account.\nOtherwise: Checks your balance."
        bank = self.loadBank()
        user = self.client.username.lower()
        if user in bank:
            self.client.sendServerMessage("Welcome to the Bank!")
            self.client.sendServerMessage("Your current balance is %d %s." % (bank[user], self.client.factory.currency))
        else:
            bank[user] = 5000
            self.dumpBank(bank)
            self.client.sendServerMessage("Welcome to the Bank!")
            self.client.sendServerMessage("We have created your account for %s." % user)
            self.client.sendServerMessage("Your balance is now %d %s." % (bank[user], self.client.factory.currency))
            self.client.factory.logger.info("%s created a new account!" % user)

    @config("rank", "director")
    def commandSetAccount(self, parts, fromloc, overriderank):
        "/setbank username amount - Director\nEdits Bank Account"
        if len(parts) != 3:
            self.client.sendServerMessage("Syntax: /setbank target amount")
            return False
        bank = self.loadBank()
        target = parts[1]
        if target not in bank:
            self.client.sendServerMessage("Invalid target")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Invalid amount")
            return False
        if self.client.username.lower() in bank:
            bank[target] = amount
            self.dumpBank(bank)
            self.client.sendServerMessage("Set user balance to %d %s." % (amount, self.client.factory.currency))
        else:
            self.client.sendServerMessage("You don't have bank account, use /bank to make one!")

    def commandPay(self, parts, fromloc, overriderank):
        "/pay username amount - Guest\nThis lets you send money to other people."
        if len(parts) != 3:
            self.client.sendServerMessage("/pay target amount")
            return False
        user = self.client.username.lower()
        target = parts[1].lower()
        bank = self.loadBank()
        if target not in bank:
            self.client.sendServerMessage("Error: Invalid Target")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Error: Invalid Amount")
            return False
        if user not in bank:
            self.client.sendServerMessage("Error: You don't have a /bank account.")
            return False
        elif amount < 0 and not self.client.isDirector():
            self.client.sendServerMessage("Error: Amount must be positive.")
            return False
        elif amount > bank[user] or amount < -(bank[target]):
            self.client.sendServerMessage("Error: Not enough %s." % self.client.factory.currency)
            return False
        elif user in bank:
            bank[target] = bank[target] + amount
            bank[user] = bank[user] - amount
            self.dumpBank(bank)
            self.client.sendServerMessage("You sent %d %s." % (amount, self.client.factory.currency))
            self.client.factory.logger.info("%(user)s sent %(amount)d %(currency)s to %(target)s" % {'user': user, 'amount': amount, 'currency': self.client.factory.currency, 'target': target})
            #factory.usernames uses all lowercased for some reason
            if target in self.client.factory.usernames:
                self.client.factory.usernames[target].sendServerMessage("You received %(amount)d %(currency)s from %(user)s." % {'amount': amount, 'currency': self.client.factory.currency, 'user': user})

    @config("rank", "director")
    def commandRemoveAccount(self, parts, fromloc, overriderank):
        "/removebank username - Director\nRemoves Bank Account"
        if len(parts) != 2:
            self.client.sendServerMessage("Syntax: /removebank target")
            return False
        bank = self.loadBank()
        target = parts[1]
        if target not in bank:
            self.client.sendServerMessage("Invalid target")
            return False
        bank.pop(target)
        self.dumpBank(bank)
        self.client.sendServerMessage("Account Deleted")
