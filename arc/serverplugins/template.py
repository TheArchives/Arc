class serverPlugin():

    name = "TemplatePlugin"

    hooks = {
        "heartbeat": "heartbeat()"
    }

    def __init__(self, factory):
        self.factory = factory
        self.logger = self.factory.logger
        self.logger.debug("Logged from template plugin!")