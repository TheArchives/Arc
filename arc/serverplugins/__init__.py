# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys
from arc.logger import ColouredLogger

debug = (True if "--debug" in sys.argv else False)
logger = ColouredLogger()
logger.debug("Imported arc/serverplugins/ folder.")
del logger
del ColouredLogger
del sys