# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

class TemplateServerPlugin():

    name = "TemplatePlugin" # What does this do? -tyteen

    hooks = {
        "onheartbeatbuild": "onHeartbeatBuild"
    }

    def __init__(self, factory):
        self.factory = factory
        self.logger = self.factory.logger
        self.logger.debug("Logged from template plugin!")