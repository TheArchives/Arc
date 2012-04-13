# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, gzip, os, colorsys
from array import array
from ConfigParser import SafeConfigParser as ConfigParser
from PIL import Image
from constants import *

BLOCK_COLOURS = {
    BLOCK_ROCK: (0, 0, 60),
    BLOCK_GRASS: (133, 97, 51),
    BLOCK_DIRT: (35, 59, 46),
    BLOCK_STONE: (0, 0, 50),
    BLOCK_WOOD: (35, 92, 62),
    BLOCK_PLANT: (133, 44, 70),
    BLOCK_GROUND_ROCK: (241, 8, 20),
    BLOCK_WATER: (215, 57, 56),
    BLOCK_STILL_WATER: (215, 57, 56),
    BLOCK_LAVA: (18, 100, 77),
    BLOCK_STILL_LAVA: (215, 57, 56),
    BLOCK_SAND: (53, 38, 76),
    BLOCK_GRAVEL: (31, 23, 52),
    BLOCK_GOLD_ORE: (35, 59, 46),
    BLOCK_COPPER_ORE: (35, 59, 46),
    BLOCK_COAL_ORE: (35, 59, 46),
    BLOCK_LOG: (35, 79, 24),
    BLOCK_LEAVES: (133, 44, 70),
    BLOCK_SPONGE: (57, 100, 70),
    BLOCK_RED_CLOTH: (0, 100, 70),
    BLOCK_ORANGE_CLOTH: (31, 100, 70),
    BLOCK_YELLOW_CLOTH: (57, 100, 70),
    BLOCK_LIME_CLOTH: (84, 100, 70),
    BLOCK_GREEN_CLOTH: (114, 100, 56),
    BLOCK_TURQUOISE_CLOTH: (158, 100, 70),
    BLOCK_CYAN_CLOTH: (180, 100, 70),
    BLOCK_BLUE_CLOTH: (215, 100, 70),
    BLOCK_INDIGO_CLOTH: (259, 100, 70),
    BLOCK_VIOLET_CLOTH: (272, 100, 70),
    BLOCK_PURPLE_CLOTH: (286, 100, 70),
    BLOCK_MAGENTA_CLOTH: (307, 100, 70),
    BLOCK_PINK_CLOTH: (325, 100, 70),
    BLOCK_DARKGREY_CLOTH: (0, 0, 40),
    BLOCK_GREY_CLOTH: (0, 0, 60),
    BLOCK_WHITE_CLOTH: (0, 0, 80),
    BLOCK_YELLOW_FLOWER: (57, 100, 70),
    BLOCK_RED_FLOWER: (0, 100, 70),
    BLOCK_RED_MUSHROOM: (0, 100, 70),
    BLOCK_BROWN_MUSHROOM: (22, 61, 50),
    BLOCK_GOLD: (57, 82, 62),
    BLOCK_IRON: (42, 90, 52),
    BLOCK_DOUBLESTEP: (34, 8, 52),
    BLOCK_STEP: (34, 8, 52),
    BLOCK_BRICK: (42, 90, 82),
    BLOCK_TNT: (35, 80, 50),
    BLOCK_BOOKCASE: (35, 92, 72),
    BLOCK_MOSSY_STONE: (121, 20, 50),
    BLOCK_OBSIDIAN: (0, 0, 0),
    }

CHR_AIR = chr(BLOCK_AIR)
CHR_GLASS = chr(BLOCK_GLASS)


class Imager(object):
    """
    Takes a level file, and turns it into a nice topographic map.
    """

    def __init__(self, level):
        self.level = level
        self.blocks_path = os.path.join(level, "blocks.gz")
        self.meta_path = os.path.join(level, "world.meta")
        assert os.path.exists(self.blocks_path)
        assert os.path.exists(self.meta_path)
        self.load()

    def load(self):
        "Load the world file into memory."
        config = ConfigParser()
        config.read(self.meta_path)
        self.x = config.getint("size", "x")
        self.y = config.getint("size", "y")
        self.z = config.getint("size", "z")
        self.blocks = array("c")
        gzf = gzip.GzipFile(self.blocks_path)
        gzf.read(4)
        chunk = gzf.read(2048)
        while chunk:
            self.blocks.extend(chunk)
            chunk = gzf.read(2048)
        gzf.close()

    def get_offset(self, x, y, z):
        "Turns block coordinates into a data offset"
        assert 0 <= x < self.x
        assert 0 <= y < self.y
        assert 0 <= z < self.z
        return y * (self.x * self.z) + z * (self.x) + x

    def get_coords(self, offset):
        "Turns a data offset into coordinates"
        x = offset % self.x
        z = (offset // self.x) % self.z
        y = offset // (self.x * self.z)
        return x, y, z

    def top_block(self, x, z):
        "Returns the top block in an x,z column that isn't air."
        cur_offset = self.get_offset(x, self.y - 1, z)
        offset_jump = self.x * self.z
        for y in reversed(range(self.y)):
            block = self.blocks[cur_offset]
            cur_offset -= offset_jump
            if block is not CHR_AIR and block is not CHR_GLASS:
                return ord(block), y
        return BLOCK_GROUND_ROCK, 0

    def draw_map(self, filename):
        img = Image.new("RGBA", (self.x, self.z))
        px = img.load()
        for x in range(self.x):
            for z in range(self.z):
                block, y = self.top_block(x, z)
                h, s, v = BLOCK_COLOURS.get(block, (0, 0, 0))
                if not (h or s or v):
                    print block
                v = (y / float(self.y)) * 50 + v * 0.5
                r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
                px[x, z] = (int(r * 255), int(g * 255), int(b * 255), 255)
        img.save(filename)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Please provide a world folder and a filename to save to."
    else:
        Imager(sys.argv[1]).draw_map(sys.argv[2])
