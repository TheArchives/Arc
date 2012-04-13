# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, random, time, traceback

from twisted.internet import reactor

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

SPECIAL_CMDS = ["wait", "if", "exit", "getinput", "getnum", "getblock", "getyn",
                "self"] # not actual commands but can be used in cmdblocks

class CommandPlugin(ProtocolPlugin):
    commands = {
        "cmdhelp": "commandCmdHelp",
        "cmd": "commandCommand",
        "gcmd": "commandGuestCommand",
        "scmd": "commandSensorCommand",
        "gscmd": "commandGuestSensorCommand",
        "cmdend": "commandCommandEnd",
        "cmddel": "commandCommandDel",
        "cmddelend": "commandCommandDelEnd",
        "cmdshow": "commandShowCMDBlocks",
        "cmdinfo": "commandCMDInfo",
        "cmddelcmd": "commandDelPreviousCMD",
        "r": "commandLastCommand",
        "lastcmd": "commandLastCommand",
        }

    hooks = {
        "onPlayerConnect": "playerConnected",
        "blockclick": "blockChanged",
        "newworld": "newWorld",
        "poschange": "posChanged",
        "chatmsg": "message"
    }

    def playerConnected(self, data):
        self.twocoordcommands = list(
            ["blb", "bhb", "bwb", "mountain", "hill", "dune", "pit", "lake", "hole", "copy", "replace", "line"])
        self.onecoordcommands = list(["sphere", "hsphere", "paste"])
        data["client"].command_remove = False
        self.last_block_position = None
        self.command_cmd = list({})
        self.command_dest = None
        data["client"].placing_cmd = False
        self.cmdinfo = False
        self.runningcmdlist = list({})
        self.runningsensor = False
        data["client"].listeningforpay = False
        self.inputvar = None
        self.inputnum = None
        self.inputblock = None
        self.inputyn = None
        self.customvars = dict({})
        data["client"].cmdinfolines = None
        self.infoindex = None
        self.lastcommand = None
        self.savedcommands = list({})

    def loadBank(self):
        file = open("config/data/balances.dat", 'r')
        bank_dic = cPickle.load(file)
        file.close()
        return bank_dic

    def message(self, message):
        if message.startswith("/") and not (
        message.split()[0].lower() == "/lastcmd" or message.split()[0].lower() == "/r"):
            self.lastcommand = message
        if data["client"].cmdinfolines != None:
            if message.lower() == "next":
                self.infoindex += 10
                index = int(self.infoindex)
                cmdlist = self.cmdinfolines[index:index + 10]
                if len(cmdlist) < 10:
                    if len(cmdlist) > 0:
                        data["client"].sendServerMessage(
                            "Page %s of %s:" % (int((index + 11) / 10), int((len(self.cmdinfolines) / 10) + 1)))
                        for x in cmdlist:
                            data["client"].sendServerMessage(x)
                    data["client"].sendServerMessage("Reached the end.")
                    self.infoindex = None
                    self.cmdinfolines = None
                    return True
                data["client"].sendServerMessage(
                    "Page %s of %s:" % (int((index + 11) / 10), int((len(self.cmdinfolines) / 10) + 1)))
                for x in cmdlist:
                    data["client"].sendServerMessage(x)
                return True
            elif message.lower() == "back":
                self.infoindex -= 10
                try:
                    cmdlist = self.cmdinfolines[self.infoindex:self.infoindex + 10]
                except:
                    self.infoindex += 10
                    data["client"].sendServerMessage("Reached the beginning.")
                    return
                data["client"].sendServerMessage(
                    "Page %s of %s:" % (int((self.infoindex + 1) / 10), int(len(self.cmdinfolist) / 10)))
                for x in cmdlist:
                    data["client"].sendServerMessage(x)
                return True
            elif message.lower() == "cancel":
                self.infoindex = None
                self.cmdinfolines = None
                return True
            else:
                data["client"].sendServerMessage("Please use 'next', 'back' or 'cancel'.")
                return True
        if self.listeningforpay:
            if message.lower() == "y" or message.lower() == "yes":
                self.listeningforpay = False
                data["client"].sendServerMessage("Payment confirmed!")
                try:
                    x = self.runningcmdlist[0]
                except IndexError:
                    return
                runcmd = True
                thiscmd = x
                thiscmd = thiscmd.replace(" /", "/") # sometimes the meta file stores it with a leading space
                if thiscmd.startswith("/gcmd"):
                    guest = True
                    runcmd = not self.runningsensor
                elif thiscmd.startswith("/gscmd"):
                    guest = True
                    runcmd = self.runningsensor
                elif thiscmd.startswith("/scmd"):
                    guest = False
                    runcmd = self.runningsensor
                else:
                    guest = False
                    runcmd = not self.runningsensor
                thiscmd = thiscmd.replace("/gcmd", "")
                thiscmd = thiscmd.replace("/cmd", "")
                thiscmd = thiscmd.replace("/gscmd", "")
                thiscmd = thiscmd.replace("/scmd", "")
                thiscmd = thiscmd.replace("$name", data["client"].username)
                thiscmd = thiscmd.replace("$date", time.strftime("%m/%d/%Y", time.localtime(time.time())))
                thiscmd = thiscmd.replace("$time", time.strftime("%H:%M:%S", time.localtime(time.time())))
                parts = thiscmd.split()
                command = str(parts[0])
                self.runningcmdlist.remove(x)
                reactor.callLater(0.01, self.runcommands)
                if not command.lower() in data["client"].commands:
                    if runcmd:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                    runcmd = False
                try:
                    func = data["client"].commands[command.lower()]
                except KeyError:
                    if runcmd:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                    runcmd = False
                try:
                    if runcmd:
                        func(parts, False, guest)
                except UnboundLocalError:
                    data["client"].sendSplitServerMessage(
                        traceback.format_exc().replace("Traceback (most recent call last):", ""))
                    data["client"].sendSplitServerMessage(
                        "Internal Server Error - Traceback (Please report this to the Server Staff or the Arc Team, see /about for contact info)")
                    data["client"].logger.error(traceback.format_exc())
            elif message.lower() == "n" or message.lower() == "no":
                self.listeningforpay = False
                self.runningcmdlist = list({})
                self.runningsensor = False
                self.listeningforpay = False
                data["client"].sendServerMessage("Payment declined.")
            else:
                data["client"].sendServerMessage("Please use 'y' or 'n' to confirm.")
            return True
        if self.inputvar:
            self.customvars[self.inputvar] = message
            self.inputvar = None
            reactor.callLater(0.01, self.runcommands)
            return True
        if self.inputnum:
            try:
                int(message)
            except ValueError:
                data["client"].sendServerMessage("Please enter an valid integer.")
                return True
            self.customvars[self.inputnum] = message
            self.inputnum = None
            reactor.callLater(0.01, self.runcommands)
            return True
        if self.inputblock:
            try:
                block = ord(data["client"].getBlockValue(message))
            except TypeError:
                # it was invalid
                return True
            if 49 < block < 0:
                data["client"].sendServerMessage("Invalid block number.")
                return True
            self.customvars[self.inputblock] = message
            self.inputblock = None
            reactor.callLater(0.01, self.runcommands)
            return True
        if self.inputyn:
            if message in ["y", "yes"]:
                self.customvars[self.inputyn] = "y"
                self.inputyn = None
                reactor.callLater(0.01, self.runcommands)
                return True
            elif message in ["n", "no"]:
                self.customvars[self.inputyn] = "n"
                self.inputyn = None
                reactor.callLater(0.01, self.runcommands)
                return True
            else:
                data["client"].sendServerMessage("Please answer 'yes' or 'no'.")
                return True

    def blockChanged(self, x, y, z, block, fromloc):
        "Hook trigger for block changes."
        # avoid infinite loops by making blocks unaffected by commands
        if fromloc != "user":
            return False
        if data["client"].world.has_cmdblock(x, y, z):
            if self.cmdinfo:
                cmdlist = data["client"].world.get_cmdblock(x, y, z)
                if len(cmdlist) < 11:
                    data["client"].sendServerMessage("Page 1 of 1:")
                    for x in cmdlist:
                        data["client"].sendServerMessage(x)
                else:
                    data["client"].sendServerMessage("Page 1 of %s:" % int((len(cmdlist) / 10) + 1))
                    for x in cmdlist[:9]:
                        data["client"].sendServerMessage(x)
                    self.infoindex = 0
                    self.cmdinfolines = cmdlist
                return False
            if data["client"].command_remove:
                data["client"].world.delete_cmdblock(x, y, z)
                data["client"].sendServerMessage("You deleted a command block.")
            else:
                if self.listeningforpay:
                    data["client"].sendServerMessage("Please confirm or cancel payment before using a cmdblock.")
                    return False

                if self.inputvar is not None or self.inputnum is not None or self.inputblock is not None or self.inputyn is not None:
                    data["client"].sendServerMessage("Please give input before using a cmdblock.")
                    return False
                if self.cmdinfolines is not None:
                    data["client"].sendServerMessage("Please complete the cmdinfo before using a cmdblock.")
                    return False
                self.runningcmdlist = list(data["client"].world.get_cmdblock(x, y, z))
                self.runningsensor = False
                reactor.callLater(0.01, self.runcommands)
                return False
        if self.command_cmd:
            if self.placing_cmd:
                data["client"].sendServerMessage("You placed a command block. Type /cmdend to stop.")
                data["client"].world.add_cmdblock(x, y, z, self.command_cmd)

    def newWorld(self, world):
        "Hook to reset Command abilities in new worlds if not op."
        if not data["client"].isBuilder():
            self.command_cmd = None
            self.command_remove = False

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        try:
            if data["client"].world.has_cmdblock(rx, ry, rz) and (rx, ry, rz) != self.last_block_position:
                if self.listeningforpay:
                    data["client"].sendServerMessage("Please confirm or cancel payment before using a cmdblock.")
                    return False
                if self.inputvar is not None or self.inputnum is not None or self.inputblock is not None or self.inputyn is not None:
                    data["client"].sendServerMessage("Please give input before using a cmdblock.")
                    return False
                self.runningcmdlist = list(data["client"].world.get_cmdblock(rx, ry, rz))
                self.runningsensor = True
                reactor.callLater(0.01, self.runcommands)
        except AssertionError:
            pass
        self.last_block_position = (rx, ry, rz)

    @config("category", "info")
    def commandCmdHelp(self, data):
        "/cmdhelp category [subcategory] - Guest\ncmdblocks help, learn what you can do in them."
        if len(parts) > 1:
            if parts[1].lower() == "types":
                if len(parts) > 2:
                    if parts[2].lower() == "cmd":
                        data["client"].sendSplitServerMessage(
                            "cmd - This is the main type of cmdblocks. Activated by clicking the block, these commands will only work if the user can.")
                    elif parts[2].lower() == "gcmd":
                        data["client"].sendSplitServerMessage(
                            "gcmd - This is the guest type of cmdblocks. Activated by clicking the block, these commands will work for anyone.")
                    elif parts[2].lower() == "scmd":
                        data["client"].sendSplitServerMessage(
                            "scmd - This is the sensor type of cmdblocks. Activated by passing through, these commands will only work if the user can.")
                    elif parts[2].lower() == "gscmd":
                        data["client"].sendSplitServerMessage(
                            "gscmd - This is the guest sensor of cmdblocks. Activated by passing through, these commands will work for anyone.")
                    else:
                        data["client"].sendServerMessage("That subcategory doesn't exist.")
                else:
                    data["client"].sendServerMessage("cmdblocks Help - Types")
                    data["client"].sendServerMessage("There are 4 types of cmdblocks.")
                    data["client"].sendServerMessage("Subcategories: cmd gcmd scmd gscmd")
            elif parts[1].lower() == "functions":
                if len(parts) > 2:
                    if parts[2].lower() in ["self", "m"]:
                        data["client"].sendServerMessage("self/m message - Outputs a message like a msgblock.")
                    elif parts[2].lower() == "exit":
                        data["client"].sendServerMessage("exit - Stops the cmdblock, no more commands.")
                    elif parts[2].lower() == "wait":
                        data["client"].sendServerMessage("wait seconds - Pauses the cmdblock for x seconds.")
                    elif parts[2].lower() == "getinput":
                        data["client"].sendSplitServerMessage(
                            "getinput varname displaymsg - Pauses the cmdblock waiting for input. The input will be any type of data, stores it for retrieval via $varname")
                    elif parts[2].lower() == "getnum":
                        data["client"].sendSplitServerMessage(
                            "getnum varname displaymsg - Pauses the cmdblock waiting for num input. The input will be any type of number, stores it for retrieval via $varname")
                    elif parts[2].lower() == "getblock":
                        data["client"].sendSplitServerMessage(
                            "getblock varname displaymsg - Pauses the cmdblock waiting for block input. The input will be any type of block, stores it for retrieval via $varname")
                    elif parts[2].lower() == "getyesno":
                        data["client"].sendSplitServerMessage(
                            "getyesno varname displaymsg - Pauses the cmdblock waiting for yesno input. The input will be a 'y' or 'n', stores it for retrieval via $varname")
                    else:
                        data["client"].sendServerMessage("That subcategory doesn't exist.")
                else:
                    data["client"].sendServerMessage("cmdblocks Help - Functions")
                    data["client"].sendSplitServerMessage(
                        "In cmdblocks there are functions, these are commands that exist only in cmdblocks and can't be done seperate.")
                    data["client"].sendSplitServerMessage(
                        "Subcategories: exit getblock getinput getnum getyesno m self wait")
            elif parts[1].lower() == "variables":
                if len(parts) > 2:
                    if parts[2].lower() == "bank":
                        data["client"].sendServerMessage("$bank - Balance of the player.")
                    elif parts[2].lower() == "block":
                        data["client"].sendSplitServerMessage(
                            "$block(x, y, z) - Block type, as a integer, for the block at x, y, z in the current world")
                    elif parts[2].lower() == "bname":
                        data["client"].sendServerMessage("$bname - Returns the block num as name, can use with $block")
                    elif parts[2].lower() == "cname":
                        data["client"].sendServerMessage("$cname - Name color of the player.")
                    elif parts[2].lower() == "date":
                        data["client"].sendServerMessage("$date - Date of the server, Month/Day/Year")
                    elif parts[2].lower() == "eval":
                        data["client"].sendServerMessage("$eval(expression) - Evaluate the string, returns the cal.")
                    elif parts[2].lower() == "first":
                        data["client"].sendServerMessage("$first - True if first time, False if not.")
                    elif parts[2].lower() == "irc":
                        data["client"].sendServerMessage("$irc - Returns the IRC network and channel.")
                    elif parts[2].lower() == "ircchan":
                        data["client"].sendServerMessage("$ircchan - Returns the IRC channel.")
                    elif parts[2].lower() == "ircnet":
                        data["client"].sendServerMessage("$ircnet - Returns the IRC network.")
                    elif parts[2].lower() == "name":
                        data["client"].sendServerMessage("$name - Username of the player.")
                    elif parts[2].lower() == "owner":
                        data["client"].sendServerMessage("$owner - Returns the server owner.")
                    elif parts[2].lower() == "posa":
                        data["client"].sendServerMessage("$posa - Returns the xyz of the player.")
                    elif parts[2].lower() == "posx":
                        data["client"].sendServerMessage("$posx - Returns the x of the player.")
                    elif parts[2].lower() == "posy":
                        data["client"].sendServerMessage("$posy - Returns the y of the player.")
                    elif parts[2].lower() == "posz":
                        data["client"].sendServerMessage("$posz - Returns the z of the player.")
                    elif parts[2].lower() == "rank":
                        data["client"].sendServerMessage("$rank - Rank name of the player.")
                    elif parts[2].lower() == "ranknum":
                        data["client"].sendServerMessage("$ranknum - Rank number of the player.")
                    elif parts[2].lower() == "rnd":
                        data["client"].sendServerMessage(
                            "$rnd(min, max) - Returns a random number between the min and max.")
                    elif parts[2].lower() == "server":
                        data["client"].sendServerMessage("$server - Name of the server.")
                    elif parts[2].lower() == "time":
                        data["client"].sendServerMessage("$time - Time of the server, hours:minutes:seconds")
                    else:
                        data["client"].sendServerMessage("That subcategory doesn't exist.")
                else:
                    data["client"].sendServerMessage("cmdblocks Help - Variables")
                    data["client"].sendSplitServerMessage(
                        "In cmdblocks there are variables, these get replaced with the respectful information when the user uses a cmdblock. All Variables start with a $ for use and work in very purposes like display and IFs.")
                    data["client"].sendSplitServerMessage(
                        "Subcategories: bank block bname cname date eval first irc ircchan ircnet name owner posa posx posy posz rank ranknum rnd server time")
            else:
                data["client"].sendServerMessage("That category doesn't exist.")
        else:
            data["client"].sendServerMessage("cmdblocks Help - Use: /cmdhelp category [subcategory]")
            data["client"].sendSplitServerMessage("Categories: types functions variables")

    @config("category", "info")
    def commandLastCommand(self, parts, fromloc, rankoverride):
        "/lastcmd - Guest\nAliases: r\nRepeats the last command that you used."
        message = self.lastcommand
        try:
            parts = [x.strip() for x in message.split() if x.strip()]
        except:
            data["client"].sendServerMessage("You haven't used a command yet.")
            return
        command = parts[0].strip("/")
        # See if we can handle it internally
        try:
            func = getattr(self.client, "command%s" % command.title())
        except AttributeError:
            # Can we find it from a plugin?
            try:
                func = data["client"].commands[command.lower()]
            except KeyError:
                data["client"].sendServerMessage("Unknown command '%s'" % command)
                return
            if hasattr(func, "config"):
                if func.config["disabled"]:
                    if fromloc == "user":
                        self.sendServerMessage("Command %s has been disabled by the server owners." % command)
                        return
                if data["client"].isSpectator() and func.config["rank"]:
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is not available to spectators." % command)
                        return
                if func.config["rank"] == "owner" and not data["client"].isOwner():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is an Owner-only command!" % command)
                        return
                if func.config["rank"] == "director" and not data["client"].isDirector():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is a Director-only command!" % command)
                        return
                if func.config["rank"] == "admin" and not data["client"].isAdmin():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is an Admin-only command!" % command)
                        return
                if func.config["rank"] == "mod" and not data["client"].isMod():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is a Mod-only command!" % command)
                        return
                if func.config["rank"] == "helper" and not data["client"].isHelper():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is a Helper-only command!" % command)
                        return
                if func.config["rank"] == "worldowner" and not data["client"].isWorldOwner():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is an WorldOwner-only command!" % command)
                        return
                if func.config["rank"] == "op" and not data["client"].isOp():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is an Op-only command!" % command)
                        return
                if func.config["rank"] == "builder" and not data["client"].isBuilder():
                    if fromloc == "user":
                        self.sendServerMessage("'%s' is a Builder-only command!" % command)
                        return
                    # Using custom message?
                if hasattr(func, "config"):
                    if func.config["custom_cmdlog_msg"]:
                        data["client"].logger.info("%s %s" % (self.username, func.config["custom_cmdlog_msg"]))
                else:
                    data["client"].logger.info("%s just used: %s" % (self.username, " ".join(parts)))
        try:
            func(parts, "user", False) # fromloc is user, overriderank is false
        except Exception, e:
            data["client"].sendSplitServerMessage(traceback.format_exc().replace("Traceback (most recent call last):", ""))
            data["client"].sendSplitServerMessage(
                "Internal Server Error - Traceback (Please report this to the Server Staff or the Arc Team, see /about for contact info)")
            data["client"].logger.error(traceback.format_exc())


    @config("rank", "builder")
    def commandCommand(self, data):
        "/cmd command [arguments] - Builder\nStarts creating a command block, or adds a command to the command\nblock. The command can be any server command. After you have\nentered all commands, type /cmd again to begin placing. Once\nplaced, the blocks will run the command when clicked as if the\none clicking had typed the commands."
        if len(parts) < 2:
            if self.command_cmd == list({}):
                data["client"].sendServerMessage("Please enter a command.")
            else:
                self.placing_cmd = True
                data["client"].sendServerMessage("You are now placing command blocks.")
        else:
            if parts[0] != "//cmd":
                if parts[1] in self.twocoordcommands:
                    if len(parts) < 8:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            x2, y2, z2 = data["client"].last_block_changes[1]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
                            parts.append(x2)
                            parts.append(y2)
                            parts.append(z2)
                if parts[1] in self.onecoordcommands:
                    if len(parts) < 5:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
            parts[0] = "/cmd"
            commandtext = ""
            command = str(parts[1])
            if command not in SPECIAL_CMDS:
                # See if we can handle it internally
                try:
                    func = getattr(self.client, "command%s" % command.title())
                except AttributeError:
                    # Can we find it from a plugin?
                    try:
                        func = data["client"].commands[command.lower()]
                    except KeyError:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                        return
                if hasattr(func, "config"):
                    if func.config["disabled"]:
                        data["client"].sendServerMessage("The command has been disabled by the server owners.")
                        return
                    if func.config["disabled_cmdblocks"]:
                        data["client"].sendServerMessage("You cannot use this command in a cmdblock.")
                        return
            for x in parts:
                commandtext = commandtext + " " + str(x)
            if not self.command_cmd is None:
                var_string = ""
                var_cmdparts = parts[1:]
                for index in range(len(var_cmdparts)):
                    if index == 0:
                        var_string = var_string + str(var_cmdparts[0])
                    else:
                        var_string = var_string + ' ' + str(var_cmdparts[index])
                self.command_cmd.append(commandtext)
                if len(self.command_cmd) > 1:
                    data["client"].sendServerMessage("Command %s added." % var_string)
                else:
                    data["client"].sendServerMessage("You are now creating a command block.")
                    data["client"].sendServerMessage("Use /cmd command again to add a command")
                    data["client"].sendSplitServerMessage(
                        "Use //cmd command to add a command without adding any coordinates (for things like blb, sphere, etc.)")
                    data["client"].sendServerMessage("Type /cmd with no args to start placing the block.")
                    data["client"].sendServerMessage("Command %s added." % var_string)

    @config("rank", "mod")
    def commandGuestCommand(self, data):
        "/gcmd command [arguments] - Mod\nMakes the next block you place a guest command block."
        if len(parts) < 2:
            if self.command_cmd == list({}):
                data["client"].sendServerMessage("Please enter a command.")
            else:
                data["client"].sendServerMessage("You are now placing guest command blocks.")
                self.placing_cmd = True
        else:
            if parts[0] != "//gcmd":
                if parts[1] in self.twocoordcommands:
                    if len(parts) < 8:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            x2, y2, z2 = data["client"].last_block_changes[1]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
                            parts.append(x2)
                            parts.append(y2)
                            parts.append(z2)

                if parts[1] in self.onecoordcommands:
                    if len(parts) < 5:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
            parts[0] = "/gcmd"
            commandtext = ""
            command = str(parts[1])
            if command not in SPECIAL_CMDS:
                # See if we can handle it internally
                try:
                    func = getattr(self.client, "command%s" % command.title())
                except AttributeError:
                    # Can we find it from a plugin?
                    try:
                        func = data["client"].commands[command.lower()]
                    except KeyError:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                        return
                if hasattr(func, "config"):
                    if func.config["disabled"]:
                        data["client"].sendServerMessage("The command has been disabled by the server owners.")
                        return
                    if func.config["disabled_cmdblocks"]:
                        data["client"].sendServerMessage("You cannot use this command in a cmdblock.")
                        return
                    if func.config["rank"] == "owner" and not data["client"].isOwner():
                        data["client"].sendServerMessage("This command can only be added by an owner.")
                        return
                    if func.config["rank"] == "director" and not data["client"].isDirector():
                        data["client"].sendServerMessage("This command can only be added by a director.")
                        return
                    if func.config["rank"] == "admin" and not data["client"].isAdmin():
                        data["client"].sendServerMessage("This command can only be added by an admin.")
                        return
            for x in parts:
                commandtext = commandtext + " " + str(x)
            if not self.command_cmd is None:
                var_string = ""
                var_cmdparts = parts[1:]
                for index in range(len(var_cmdparts)):
                    if index == 0:
                        var_string = var_string + str(var_cmdparts[0])
                    else:
                        var_string = var_string + ' ' + str(var_cmdparts[index])
                self.command_cmd.append(commandtext)
                if len(self.command_cmd) > 1:
                    data["client"].sendServerMessage("Command %s added." % var_string)
                else:
                    data["client"].sendServerMessage("You are now creating a guest command block.")
                    data["client"].sendServerMessage("WARNING: Commands on this block can be run by ANYONE")
                    data["client"].sendServerMessage("Use /gcmd command again to add a command")
                    data["client"].sendSplitServerMessage(
                        "Use //gcmd command to add a command without adding any coordinates (for things like blb, sphere, etc.)")
                    data["client"].sendServerMessage("Type /gcmd with no args to start placing the block.")
                    data["client"].sendServerMessage("Command %s added." % var_string)

    @config("rank", "builder")
    def commandSensorCommand(self, data):
        "/scmd command [arguments] - Builder\nStarts creating a command block, or adds a command to the command\nblock. The command can be any server command. After you have\nentered all commands, type /cmd again to begin placing. Once\nplaced, the blocks will run the command when clicked as if the\none clicking had typed the commands."
        if len(parts) < 2:
            if self.command_cmd == list({}):
                data["client"].sendServerMessage("Please enter a command.")
            else:
                self.placing_cmd = True
                data["client"].sendServerMessage("You are now placing sensor command blocks.")
        else:
            if parts[0] != "//scmd":
                if parts[1] in self.twocoordcommands:
                    if len(parts) < 8:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            x2, y2, z2 = data["client"].last_block_changes[1]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
                            parts.append(x2)
                            parts.append(y2)
                            parts.append(z2)
                if parts[1] in self.onecoordcommands:
                    if len(parts) < 5:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
            parts[0] = "/scmd"
            commandtext = ""
            command = str(parts[1])
            if command not in SPECIAL_CMDS:
                # See if we can handle it internally
                try:
                    func = getattr(self.client, "command%s" % command.title())
                except AttributeError:
                    # Can we find it from a plugin?
                    try:
                        func = data["client"].commands[command.lower()]
                    except KeyError:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                        return
                if hasattr(func, "config"):
                    if func.config["disabled"]:
                        data["client"].sendServerMessage("The command has been disabled by the server owners.")
                        return
                    if func.config["disabled_cmdblocks"]:
                        data["client"].sendServerMessage("You cannot use this command in a cmdblock.")
                        return
            for x in parts:
                commandtext = commandtext + " " + str(x)
            if not self.command_cmd is None:
                var_string = ""
                var_cmdparts = parts[1:]
                for index in range(len(var_cmdparts)):
                    if index == 0:
                        var_string = var_string + str(var_cmdparts[0])
                    else:
                        var_string = var_string + ' ' + str(var_cmdparts[index])
                self.command_cmd.append(commandtext)
                if len(self.command_cmd) > 1:
                    data["client"].sendServerMessage("Command %s added." % var_string)
                else:
                    data["client"].sendServerMessage("You are now creating a sensor command block.")
                    data["client"].sendServerMessage("Use /scmd command again to add a command.")
                    data["client"].sendSplitServerMessage(
                        "Use //scmd command to add a command without adding any coordinates (for things like blb, sphere, etc.)")
                    data["client"].sendServerMessage("Type /scmd with no args to start placing the block.")
                    data["client"].sendServerMessage("Command %s added." % var_string)

    @config("rank", "mod")
    def commandGuestSensorCommand(self, data):
        "/gscmd command [arguments] - Mod\nMakes the next block you place a guest sensor command block."
        if len(parts) < 2:
            if self.command_cmd == list({}):
                data["client"].sendServerMessage("Please enter a command.")
            else:
                data["client"].sendServerMessage("You are now placing guest sensor command blocks.")
                self.placing_cmd = True
        else:
            if parts[0] != "//gscmd":
                if parts[1] in self.twocoordcommands:
                    if len(parts) < 8:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            x2, y2, z2 = data["client"].last_block_changes[1]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
                            parts.append(x2)
                            parts.append(y2)
                            parts.append(z2)
                if parts[1] in self.onecoordcommands:
                    if len(parts) < 5:
                        if len(data["client"].last_block_changes) > 1:
                            x, y, z = data["client"].last_block_changes[0]
                            parts.append(x)
                            parts.append(y)
                            parts.append(z)
            parts[0] = "/gscmd"
            commandtext = ""
            command = str(parts[1])
            if command not in SPECIAL_CMDS:
                # See if we can handle it internally
                try:
                    func = getattr(self.client, "command%s" % command.title())
                except AttributeError:
                    # Can we find it from a plugin?
                    try:
                        func = data["client"].commands[command.lower()]
                    except KeyError:
                        data["client"].sendServerMessage("Unknown command '%s'" % command)
                        return
                if hasattr(func, "config"):
                    if func.config["disabled"]:
                        data["client"].sendServerMessage("The command has been disabled by the server owners.")
                        return
                    if func.config["disabled_cmdblocks"]:
                        data["client"].sendServerMessage("You cannot use this command in a cmdblock.")
                        return
                    if func.config["rank"] == "owner" and not data["client"].isOwner():
                        data["client"].sendServerMessage("This command can only be added by an owner.")
                        return
                    if func.config["rank"] == "director" and not data["client"].isDirector():
                        data["client"].sendServerMessage("This command can only be added by a director.")
                        return
                    if func.config["rank"] == "admin" and not data["client"].isAdmin():
                        data["client"].sendServerMessage("This command can only be added by an admin.")
                        return
            for x in parts:
                commandtext = commandtext + " " + str(x)
            if not self.command_cmd is None:
                var_string = ""
                var_cmdparts = parts[1:]
                for index in range(len(var_cmdparts)):
                    if index == 0:
                        var_string = var_string + str(var_cmdparts[0])
                    else:
                        var_string = var_string + ' ' + str(var_cmdparts[index])
                self.command_cmd.append(commandtext)
                if len(self.command_cmd) > 1:
                    data["client"].sendServerMessage("Command %s added." % var_string)
                else:
                    data["client"].sendServerMessage("You are now creating a guest sensor command block.")
                    data["client"].sendServerMessage("WARNING: Commands on this block can be run by ANYONE.")
                    data["client"].sendServerMessage("Use /gscmd command again to add a command.")
                    data["client"].sendSplitServerMessage(
                        "Use //gscmd command to add a command without adding any coordinates (for things like blb, sphere, etc.)")
                    data["client"].sendServerMessage("Type /gscmd with no args to start placing the block.")
                    data["client"].sendServerMessage("Command %s added." % var_string)

    @config("rank", "builder")
    def commandCommandEnd(self, data):
        "/cmdend [save]- Builder\nStops placing command blocks (type save to save your commands)."
        if len(parts) == 2:
            if parts[1] == "save":
                data["client"].sendServerMessage("Current command block type and its commands kept.")
            else:
                self.command_cmd = list({})
        else:
            self.command_cmd = list({})
        self.command_remove = False
        self.placing_cmd = False
        data["client"].sendServerMessage("You are no longer placing command blocks.")
        data["client"].sendSplitServerMessage(
            "Note: you can type '/cmdend save' to keep the block you are making and it's commands.")

    @config("rank", "builder")
    def commandCommandDel(self, data):
        "/cmddel - Builder\nEnables command deleting mode."
        data["client"].sendServerMessage("You are now able to delete command blocks. /cmddelend to stop")
        self.command_remove = True

    @config("rank", "builder")
    def commandDelPreviousCMD(self, data):
        "/cmddelcmd - Builder\nDeletes the previous command for the block."
        if len(self.command_cmd) > 0:
            del self.command_cmd[len(self.command_cmd) - 1]
            data["client"].sendServerMessage("Previous command for the block deleted.")
        else:
            data["client"].sendServerMessage("There is no block command to delete.")

    @config("rank", "builder")
    def commandCommandDelEnd(self, data):
        "/cmddelend - Builder\nDisables command deleting mode."
        data["client"].sendServerMessage("Command deletion mode ended.")
        self.command_remove = False

    @config("rank", "builder")
    def commandShowCMDBlocks(self, data):
        "/cmdshow - Builder\nShows all command blocks as yellow, only to you."
        for offset in data["client"].world.cmdblocks.keys():
            x, y, z = data["client"].world.get_coords(offset)
            data["client"].sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_YELLOW)
        data["client"].sendServerMessage("All cmdblocks appearing yellow temporarily.")

    @config("rank", "builder")
    @on_off_command
    def commandCMDInfo(self, onoff, fromloc, overriderank):
        "/cmdinfo - Builder\nTells you the commands in a cmdblock"
        if onoff == "on":
            self.cmdinfo = True
        else:
            self.cmdinfo = False
        data["client"].sendServerMessage("Command block info is now %s." % onoff)

    def runcommands(self):
        try:
            x = self.runningcmdlist[0]
        except IndexError:
            self.customvars = dict({})
            return
        runcmd = True
        thiscmd = str(x)
        thiscmd = thiscmd.replace(" /", "/") # sometimes the meta file stores it with a leading space
        if thiscmd.startswith("/gcmd"):
            guest = True
            runcmd = not self.runningsensor
        elif thiscmd.startswith("/gscmd"):
            guest = True
            runcmd = self.runningsensor
        elif thiscmd.startswith("/scmd"):
            guest = False
            runcmd = self.runningsensor
        else:
            guest = False
            runcmd = not self.runningsensor
        thiscmd = thiscmd.replace("/gcmd", "")
        thiscmd = thiscmd.replace("/cmd", "")
        thiscmd = thiscmd.replace("/gscmd", "")
        thiscmd = thiscmd.replace("/scmd", "")
        thiscmd = thiscmd.replace("$name", data["client"].username)
        thiscmd = thiscmd.replace("$cname", data["client"].colouredUsername())
        bank = self.loadBank()
        user = data["client"].username.lower()
        if user in bank:
            balance = bank[user]
        else:
            balance = 0
        thiscmd = thiscmd.replace("$bank", str(balance))
        thiscmd = thiscmd.replace("$first", str(data["client"].username in self.factory.lastseen))
        thiscmd = thiscmd.replace("$server", self.factory.server_name)
        if self.factory.irc_relay:
            thiscmd = thiscmd.replace("$irc",
                self.factory.irc_config.get("irc", "server") + " " + self.factory.irc_channel)
            thiscmd = thiscmd.replace("$ircchan", self.factory.irc_channel)
            thiscmd = thiscmd.replace("$ircnet", self.factory.irc_config.get("irc", "server"))
        else:
            thiscmd = thiscmd.replace("$irc", "N/A")
            thiscmd = thiscmd.replace("$ircchan", "N/A")
            thiscmd = thiscmd.replace("$ircnet", "N/A")
        thiscmd = thiscmd.replace("$owner", ", ".join(self.factory.owners))
        thiscmd = thiscmd.replace("$owners", ", ".join(self.factory.owners))
        thiscmd = thiscmd.replace("$year", time.strftime("%Y", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$month", time.strftime("%m", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$day", time.strftime("%d", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$date", time.strftime("%m/%d/%Y", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$rdate", time.strftime("%d/%m/%Y", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$sdate", time.strftime("%m/%d", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$rsdate", time.strftime("%d/%m", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$time", time.strftime("%H:%M:%S", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$hour", time.strftime("%H", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$min", time.strftime("%M", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$sec", time.strftime("%S", time.localtime(time.time())))
        thiscmd = thiscmd.replace("$stime", time.strftime("%H:%M", time.localtime(time.time())))
        myrank = "guest"
        myranknum = 1
        if data["client"].isSpectator():
            myrank = "spec"
            myranknum = 0
        elif data["client"].isOwner():
            myrank = "owner"
            myranknum = 9
        elif data["client"].isDirector():
            myrank = "director"
            myranknum = 8
        elif data["client"].isAdmin():
            myrank = "admin"
            myranknum = 7
        elif data["client"].isMod():
            myrank = "mod"
            myranknum = 6
        elif data["client"].isHelper():
            myrank = "helper"
            myranknum = 5
        elif data["client"].isWorldOwner():
            myrank = "worldowner"
            myranknum = 4
        elif data["client"].isOp():
            myrank = "op"
            myranknum = 3
        elif data["client"].isBuilder():
            myrank = "builder"
            myranknum = 2
        rx = data["client"].x >> 5
        ry = data["client"].y >> 5
        rz = data["client"].z >> 5
        thiscmd = thiscmd.replace("$posx", str(rx))
        thiscmd = thiscmd.replace("$posy", str(ry))
        thiscmd = thiscmd.replace("$posz", str(rz))
        thiscmd = thiscmd.replace("$posa", str(rx) + " " + str(ry) + " " + str(rx))
        thiscmd = thiscmd.replace("$rank", myrank)
        thiscmd = thiscmd.replace("$rnum", str(myranknum))
        for variable in self.customvars.keys():
            thiscmd = thiscmd.replace("$" + variable, str(self.customvars[variable]))
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 4)] == "$rnd":
                try:
                    limits = thiscmd[thiscmd.find("(", num) + 1:thiscmd.find(")", num + 5)].split(",")
                    thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num) + 1],
                        str(random.randint(int(limits[0]), int(limits[1]))))
                except:
                    data["client"].sendServerMessage("$rnd Syntax Error; Use: $rnd(num1,num2)")
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 4)] == "$mod":
                try:
                    limits = thiscmd[thiscmd.find("(", num) + 1:thiscmd.find(")", num + 5)].split(",")
                    thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num) + 1],
                        str(int(limits[0]) % int(limits[1])))
                except:
                    data["client"].sendServerMessage("$mod Syntax Error; Use: $mod(num1,num2)")
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 6)] == "$block":
                try:
                    coords = thiscmd[thiscmd.find("(", num) + 1:thiscmd.find(")", num + 5)].split(",")
                    x = int(coords[0])
                    y = int(coords[1])
                    z = int(coords[2])
                    check_offset = data["client"].world.blockstore.get_offset(x, y, z)
                    block = ord(data["client"].world.blockstore.raw_blocks[check_offset])
                    thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num) + 1], str(block))
                except:
                    data["client"].sendServerMessage("$block Syntax Error; Use: $block(x,y,z)")
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 4)] == "$bin":
                try:
                    HexBin = {"0": "0000", "1": "0001", "2": "0010", "3": "0011", "4": "0100", "5": "0101", "6": "0110",
                              "7": "0111", "8": "1000", "9": "1001", "A": "1010", "B": "1011", "C": "1100", "D": "1101",
                              "E": "1110", "F": "1111"}
                    coords = thiscmd[thiscmd.find("(", num) + 1:thiscmd.find(")", num + 5)] #.split(",")
                    thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num) + 1],
                        str("".join([HexBin[i] for i in '%X' % coords[0]]).lstrip('0')))
                except:
                    data["client"].sendServerMessage("$bin Syntax Error; Use: $bin(x)")
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 5)] == "$eval" or thiscmd[num:(num + 4)] == "$int":
                try:
                    parentheses = 0
                    for num2 in range(num + 6, len(thiscmd) - 1):
                        if thiscmd[num2] == "(":
                            parentheses = parentheses + 1
                        elif thiscmd[num2] == ")":
                            parentheses = parentheses - 1
                        if parentheses == 0:
                            # We've reached the end of the expression
                            lastindex = num2
                    expression = str(eval(thiscmd[thiscmd.find("(", num) + 1:lastindex + 1]))
                    thiscmd = thiscmd.replace(thiscmd[num:lastindex + 2], expression)
                except:
                    data["client"].sendServerMessage("$eval Syntax Error; Use: $eval(expression)")
        for num in range(len(thiscmd)):
            if thiscmd[num:(num + 6)] == "$bname":
                try:
                    blocknum = int(thiscmd[thiscmd.find("(", num) + 1:thiscmd.find(")", num + 5)])
                    thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num) + 1], BlockList[blocknum])
                except:
                    data["client"].sendServerMessage("$bname Syntax Error; Use: $bname(blockint)")
        if thiscmd.startswith(" if"):
            try:
                condition = thiscmd[4:thiscmd.find(":")]
                if (bool(eval(condition, {}, {}))) == False:
                    runcmd = False
                thiscmd = thiscmd.replace(thiscmd[:thiscmd.find(":") + 1], "")
            except:
                data["client"].sendServerMessage("IF Syntax Error; Use: if \"a\"==\"b\": command")
        parts = thiscmd.split()
        command = str(parts[0])
        # Require confirmation
        if command == "pay":
            try:
                target = parts[1]
                amount = int(parts[2])
            except:
                data["client"].sendServerMessage("Pay syntax error.")
                runcmd = False
            if runcmd:
                bank = self.loadBank()
                user = data["client"].username.lower()
            if user in bank:
                if bank[user] > amount:
                    self.listeningforpay = True
                    data["client"].sendServerMessage("%s is requesting payment of C%s. Pay? [Y/N]" % (target, amount))
                    return
                else:
                    data["client"].sendServerMessage("You don't have enough money to pay!")
                    self.runningcmdlist = list({})
                    self.runningsensor = False
                    return
            else:
                data["client"].sendServerMessage("You don't have a bank account!")
                self.runningcmdlist = list({})
                self.runningsensor = False
                return
            # Comments
        if command == "#" and runcmd:
            runcmd = False
        if (command == "self" or command == "m") and runcmd:
            msg = ""
            parts.pop(0)
            msg = " ".join(parts)
            data["client"]._sendMessage(COLOUR_GREEN, msg)
            runcmd = False
        if command == "wait" and runcmd:
            delay = float(0.1)
            try:
                delay = float(parts[1])
            except:
                data["client"].sendServerMessage("Wait time must be a number!")
                runcmd = False
            self.runningcmdlist.remove(self.runningcmdlist[0])
            reactor.callLater(delay, self.runcommands)
            return
        if command == "exit" and runcmd:
            self.runningcmdlist = list({})
            return
        if command == "getinput" and runcmd:
            try:
                self.inputvar = parts[1]
            except IndexError:
                data["client"].sendServerMessage("You must give a variable name!")
                runcmd = False
            if runcmd:
                if len(parts) > 2:
                    data["client"].sendServerMessage("[INPUT] " + " ".join(parts[2:]))
                else:
                    data["client"].sendServerMessage("This command block is requesting input.")
                self.runningcmdlist.remove(self.runningcmdlist[0])
                return
        if command == "getnum" and runcmd:
            try:
                self.inputnum = parts[1]
            except IndexError:
                data["client"].sendServerMessage("You must give a variable name!")
                runcmd = False
            if runcmd:
                if len(parts) > 2:
                    data["client"].sendServerMessage("[INPUT] " + " ".join(parts[2:]))
                else:
                    data["client"].sendServerMessage("This command block is requesting input.")
                self.runningcmdlist.remove(self.runningcmdlist[0])
                return
        if command == "getblock" and runcmd:
            try:
                self.inputblock = parts[1]
            except IndexError:
                data["client"].sendServerMessage("You must give a variable name!")
                runcmd = False
            if runcmd:
                if len(parts) > 2:
                    data["client"].sendServerMessage("[BLOCK INPUT] " + " ".join(parts[2:]))
                else:
                    data["client"].sendServerMessage("This command block is requesting block input.")
                self.runningcmdlist.remove(self.runningcmdlist[0])
                return
        if command == "getyesno" and runcmd:
            try:
                self.inputyn = parts[1]
            except IndexError:
                data["client"].sendServerMessage("You must give a variable name!")
                runcmd = False
            if runcmd:
                if len(parts) > 2:
                    data["client"].sendServerMessage("[Y/N] " + " ".join(parts[2:]))
                else:
                    data["client"].sendServerMessage("This command block is requesting yes/no input.")
                self.runningcmdlist.remove(self.runningcmdlist[0])
                return
        try:
            if not command.lower() in data["client"].commands:
                if runcmd:
                    data["client"].sendServerMessage("Unknown command '%s'" % command)
                runcmd = False
            func = data["client"].commands[command.lower()]
        except KeyError:
            if runcmd:
                data["client"].sendServerMessage("Unknown command '%s'" % command)
                runcmd = False
        if runcmd is True:
            if hasattr(func, "config"):
                if func.config["disabled"]:
                    data["client"].sendServerMessage("Command %s has been disabled by the server owners." % command)
                    runcmd = False
                if func.config["disabled_cmdblocks"]:
                    data["client"].sendServerMessage("This command cannot be used in a command block.")
                    runcmd = False
            if guest is False:
                if data["client"].isSpectator() and func.config["rank"]:
                    data["client"].sendServerMessage("'%s' is not available to spectators." % command)
                    runcmd = False
                if func.config["rank"] == "owner" and not data["client"].isOwner():
                    data["client"].sendServerMessage("'%s' is an Owner-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "director" and not data["client"].isDirector():
                    data["client"].sendServerMessage("'%s' is a Director-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "admin" and not data["client"].isAdmin():
                    data["client"].sendServerMessage("'%s' is an Admin-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "mod" and not data["client"].isMod():
                    data["client"].sendServerMessage("'%s' is a Mod-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "helper" and not data["client"].isHelper():
                    data["client"].sendServerMessage("'%s' is a Helper-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "worldowner" and not data["client"].isWorldOwner():
                    data["client"].sendServerMessage("'%s' is an WorldOwner-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "op" and not data["client"].isOp():
                    data["client"].sendServerMessage("'%s' is an Op-only command!" % command)
                    runcmd = False
                if func.config["rank"] == "builder" and not data["client"].isBuilder():
                    data["client"].sendServerMessage("'%s' is a Builder-only command!" % command)
                    runcmd = False
            try:
                if runcmd:
                    func(parts, "cmdblock", guest)
            except Exception as e:
                data["client"].sendSplitServerMessage(
                    traceback.format_exc().replace("Traceback (most recent call last):", ""))
                data["client"].sendSplitServerMessage(
                    "Internal Server Error - Traceback (Please report this to the Server Staff or the Arc Team, see /about for contact info)")
                data["client"].logger.error(traceback.format_exc())
        self.runningcmdlist.remove(self.runningcmdlist[0])
        reactor.callLater(0.1, self.runcommands)
