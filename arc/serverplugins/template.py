# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

class TemplateServerPlugin():

    name = "TemplatePlugin" # What does this do? -tyteen

    def __init__(self, factory):
        factory.logger.debug("Logged from template plugin!")
        
    def onLastseen(factory, data):
        factory.logger.info("Player %s had lastseen set at %s" % (data["username"], data["time"]))
        
    hooks = {
        "lastseen": onLastseen
    }
        
serverPlugin = TemplateServerPlugin
