# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *

class MessageBlockPlugin(object):
    commands = {
        "mb": "commandMessageBlock",
        "mbend": "commandMessageBlockEnd",
        "mbshow": "commandShowMessageBlocks",
        "mbdel": "commandMessageBlockDel",
        "mbdelend": "commandMessageBlockDelEnd",
        }

    hooks = {
        "onPlayerConnect": "gotClient",
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
        }

    def gotClient(self, data):
        data["client"].msgblock_message = None
        data["client"].msgblock_remove = False
        data["client"].last_block_position = None

    def newWorld(self, data):
        "Hook to reset msgblocks abilities in new worlds if not op."
        if not data["client"].isOp(): data["client"].msgblock_message = None

    def blockChanged(self, data):
        "Hook trigger for block changes."
        if data["client"].world.has_msgblock(data["x"], data["y"], data["z"]):
            if data["client"].msgblock_remove:
                data["client"].world.delete_msgblock(data["x"], data["y"], data["z"])
                data["client"].sendServerMessage("You deleted a message block.")
            else:
                data["client"].sendServerMessage("That is a message block, you cannot change it. (/mbdel?)")
                return False # False = they weren't allowed to build
        if data["client"].msgblock_message:
            data["client"].sendServerMessage("You placed a message block.")
            data["client"].world.add_msgblock(data["x"], data["y"], data["z"], data["client"].msgblock_message)

    def posChanged(self, data):
        "Hook trigger for when the user moves."
        rx, ry, rz = data["x"] >> 5, data["y"] >> 5, data["z"] >> 5
        try:
            if data["client"].world.has_msgblock(rx, ry, rz) and (rx, ry, rz) != data["client"].last_block_position:
                for message in data["client"].world.get_msgblock(rx, ry, rz).split('\n'):
                    data["client"]._sendMessage(COLOUR_GREEN, message)
        except AssertionError:
            pass
        data["client"].last_block_position = (rx, ry, rz)

    @config("rank", "op")
    @config("usage", "message")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMessageBlock(self, data):
        "Makes the next block you place a message block.\nUse /mb \\message to append to the last message, or use /mb message to make a new line."
        msg_part = (" ".join(data["parts"][1:])).strip()
        if not msg_part:
            data["client"].sendServerMessage("Please enter a message.")
            return
        new_message = False
        if not data["client"].msgblock_message:
            data["client"].msgblock_message = ""
            data["client"].sendServerMessage("You are now placing message blocks.")
            new_message = True
        if msg_part[-1] == "\\":
            data["client"].msgblock_message += msg_part[:-1] + " "
        else:
            data["client"].msgblock_message += msg_part + "\n"
        if len(data["client"].msgblock_message) > 200:
            data["client"].msgblock_message = data["client"].msgblock_message[:200]
            data["client"].sendServerMessage("Your message ended up longer than 200 chars, and was truncated.")
        elif not new_message:
            data["client"].sendServerMessage("Message extended; you've used %i characters." % len(data["client"].msgblock_message))

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMessageBlockEnd(self, data):
        "Stops placing message blocks."
        data["client"].msgblock_message = None
        data["client"].sendServerMessage("You are no longer placing message blocks.")

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandShowMessageBlocks(self, data):
        "Shows all message blocks as green, only to you."
        for offset in data["client"].world.msgblocks.keys():
            x, y, z = data["client"].world.get_coords(offset)
            data["client"].sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_GREEN)
        data["client"].sendServerMessage("All msgblocks appearing green temporarily.")

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMessageBlockDel(self, data):
        "Enables msgblock-deleting mode."
        data["client"].sendServerMessage("You are now able to delete msgblocks. /mbdelend to stop")
        data["client"].msgblock_remove = True

    @config("rank", "op")
    @config("disabled-on", ["cmdblock", "irc", "irc_query", "console"])
    def commandMessageBlockDelEnd(self, data):
        "Disables msgblock-deleting mode."
        data["client"].sendServerMessage("Msgblock deletion mode ended.")
        data["client"].msgblock_remove = False

serverPlugin = MessageBlockPlugin