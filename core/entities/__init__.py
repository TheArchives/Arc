explosionblocklist = [[-3, -1, 0], [-3, 0, -1], [-3, 0, 0], [-3, 0, 1], [-3, 1, 0],
                      [-2, -2, -1], [-2, -2, 0], [-2, -2, 1], [-2, -1, -2], [-2, -1, -1], [-2, -1, 0], [-2, -1, 1], [-2, -1, 2], [-2, 0, -2], [-2, 0, -1],
                      [-2, 0, 0], [-2, 0, 1], [-2, 0, 2], [-2, 1, -2], [-2, 1, -1], [-2, 1, 0], [-2, 1, 1], [-2, 1, 2], [-2, 2, -1], [-2, 2, 0], [-2, 2, 1],
                      [-1, -3, 0], [-1, -2, -2], [-1, -2, -1], [-1, -2, 0], [-1, -2, 1], [-1, -2, 2], [-1, -1, -2], [-1, -1, -1], [-1, -1, 0], [-1, -1, 1], [-1, -1, 2], [-1, 0, -3], [-1, 0, -2], [-1, 0, -1],
                      [-1, 0, 0], [-1, 0, 1], [-1, 0, 2], [-1, 0, 3], [-1, 1, -2], [-1, 1, -1], [-1, 1, 0], [-1, 1, 1], [-1, 1, 2], [-1, 2, -2], [-1, 2, -1], [-1, 2, 0], [-1, 2, 1], [-1, 2, 2], [-1, 3, 0],
                      [0, -3, -1], [0, -3, 0], [0, -3, 1], [0, -2, -2], [0, -2, -1], [0, -2, 0], [0, -2, 1], [0, -2, 2],
                      [0, -1, -3], [0, -1, -2], [0, -1, -1], [0, -1, 0], [0, -1, 1], [0, -1, 2], [0, -1, 3], [0, 0, -3], [0, 0, -2], [0, 0, -1],
                      [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 1, -3], [0, 1, -2], [0, 1, -1], [0, 1, 0], [0, 1, 1], [0, 1, 2], [0, 1, 3],
                      [0, 2, -2], [0, 2, -1], [0, 2, 0], [0, 2, 1], [0, 2, 2], [0, 3, -1], [0, 3, 0], [0, 3, 1],
                      [1, -3, 0], [1, -2, -2], [1, -2, -1], [1, -2, 0], [1, -2, 1], [1, -2, 2], [1, -1, -2], [1, -1, -1], [1, -1, 0], [1, -1, 1], [1, -1, 2], [1, 0, -3], [1, 0, -2], [1, 0, -1],
                      [1, 0, 0], [1, 0, 1], [1, 0, 2], [1, 0, 3], [1, 1, -2], [1, 1, -1], [1, 1, 0], [1, 1, 1], [1, 1, 2],[1, 2, -2], [1, 2, -1], [1, 2, 0], [1, 2, 1], [1, 2, 2], [1, 3, 0],
                      [2, -2, -1], [2, -2, 0], [2, -2, 1], [2, -1, -2], [2, -1, -1], [2, -1, 0], [2, -1, 1], [2, -1, 2], [2, 0, -2], [2, 0, -1],
                      [2, 0, 0], [2, 0, 1], [2, 0, 2], [2, 1, -2], [2, 1, -1], [2, 1, 0], [2, 1, 1], [2, 1, 2], [2, 2, -1], [2, 2, 0], [2, 2, 1],
                      [3, -1, 0], [3, 0, -1], [3, 0, 0], [3, 0, 1], [3, 1, 0]
                      ]
maxentitiystepsatonetime = 20
twoblockhighentities = ["creeper", "zombie", "noob", "person"]
twoblockhighshootingentities = ["bckchngdetector", "testbow", "paintballgun"]
entityblocklist = {"zombie": [(0, 0, 0), (0, 1, 0)],
                  "creeper": [(0, 0, 0), (0, 1, 0)],
                  "person": [(0, 0, 0), (0, 1, 0)],
                  "noob": [(0, 0, 0), (0, 1, 0)],
                  "bckchngdetector": [(0, 0, 0), (0, 1, 0)],
                  "testbow": [(0, 0, 0), (0, 1, 0)],
                  "paintballgun": [(0, 0, 0), (0, 1, 0)]
                  }
colorblocks = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
var_unpainablelist = [7, 20, 42, 41, 49, 40, 44, 43, 39, 38, 6, 37, 38]
var_unbreakables = ['\x07', '*', ')', '.', '1']
var_childrenentities = ["testarrow", "paintball", "cannonball"]
unselectableentities = ["testarrow", "paintball", "cannonball", "bckchngdetector", "entity1", "passiveblob", "petblob", "smoke", "rain", "testarrow"]

# Work in progress
class EntityMetaclass(type):

    """
    A metaclass which registers any subclasses of Entities.
    """

    def __new__(cls, name, bases, dct):
        # Supercall
        new_cls = type.__new__(cls, name, bases, dct)
        logger = logging.getLogger("Entities")
        pass

class BaseEntity(object): # No default values here!
    """
    Parent object all entities inherit from.
    """
    
    metaclass=EntityMetaclass

    def __init__(self):
        pass

    def mainLoop(self):
        pass

    def onCreate(self):
        pass

    def onDestory(self):
        pass
