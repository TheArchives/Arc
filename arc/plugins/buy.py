# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle

from arc.constants import *
from arc.decorators import *
from arc.globals import *
from arc.plugins import ProtocolPlugin

class BuyPlugin(ProtocolPlugin):
    
    commands = {
        "buy": "commandBuy",
    }
    
    def commandBuy(self, parts, fromloc, overriderank):
        "/buy worldname size - Guest\nsmall - 64x64x64, 2000 Minecash.\nnormal - 128x128x128, 4000 Minecash.\nMakes a new world, and boots it, if the user has enough money."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify a new worldname and size.")
        elif self.client.factory.world_exists(parts[1]):
            self.client.sendServerMessage("Worldname in use")
        else:
            if len(parts) == 3 or len(parts) == 4:
                size = parts[2].lower()
                if size == "small":
                    template = "small"
                    price = 2000
                elif size == "normal":
                    template = "normal"
                    price = 4000
                else:
                    self.client.sendServerMessage("%s is not a valid size." % size)
                    return
            else:
                self.client.sendServerMessage("Please specify a worldname and size.")
                return
            file = open('config/data/balances.dat', 'r')
            bank = cPickle.load(file)
            file.close()
            amount = price
            user = self.client.username.lower()
            if user not in bank:
                self.client.sendServerMessage("You don't have an account yet. Use /bank first.")
                return
            if not amount <= bank[user]:
                self.client.sendServerMessage("You need at least %s to buy this world." % amount)
                return False
            else:
                file = open('config/data/balances.dat', 'w')
                bank[user] = bank[self.client.username.lower()] - amount
                cPickle.dump(bank, file)
                file.close()
                self.client.sendServerMessage("Paid %s for the world." % amount)
            world_id = parts[1].lower()
            self.client.factory.newWorld(world_id, template)
            returned = self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
            if returned == False:
                self.client.sendServerMessage("World %s loading failed, please contact the staff." % world_id)
            self.client.factory.worlds[world_id].all_write = False
            if len(parts) < 4:
                self.client.sendServerMessage("World '%s' made and booted." % world_id)
                self.client.changeToWorld(world_id)
                self.client.sendServerMessage(Rank(self, ["/rank", "worldowner", self.client.username, world_id], fromloc, True))
            world = self.client.factory.worlds[world_id]
            world.all_write = False
