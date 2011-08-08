# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys
from arc.logger import ColouredLogger

class ServerPlugin(object):
    """
    Parent object all server plugins inherit from.
    """

    def __init__(self, factory):
        # Store the factory
        self.factory = factory
        self.logger = ColouredLogger(debug)
        # Call clean setup method
        self.gotServer()