# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *

class McBansServerPlugin():

    name = "McBansServerPlugin"

    hooks = {

    }
    
    commands = {
        "derp": "herp"
    }

    def gotServer(self):
        self.logger.debug("Loaded the test command ServerPlugin.")
        
    def testCommand(self, data):
        

serverPlugin = McBansServerPlugin