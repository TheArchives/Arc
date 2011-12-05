# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import datetime, sys, threading, time, traceback

from twisted.internet.task import LoopingCall
from arc.constants import *
from arc.globals import *
from arc.logger import ColouredLogger

import logging

class StdinPlugin(threading.Thread):

    def __init__(self, factory):
        threading.Thread.__init__(self)
        self.factory = factory
        self.logger = self.factory.logger
        self.stop = False

    def run(self):
        try:
            try:
                while not self.stop:
                    try:
                        line = sys.stdin.readline()
                    except:
                        return
                    message = line
                    if len(line) > 1:
                        goodchars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", " ", "!", "@", "#", "$", "%", "*", "(", ")", "-", "_", "+", "=", "{", "[", "}", "]", ":", ";", "\"", "\'", "<", ",", ">", ".", "?", "/", "\\", "|"]
                        for character in message:
                            if not character.lower() in goodchars:
                                message = message.replace("&0", "&0")
                                message = message.replace("&1", "&1")
                                message = message.replace("&2", "&2")
                                message = message.replace("&3", "&3")
                                message = message.replace("&4", "&4")
                                message = message.replace("&5", "&5")
                                message = message.replace("&6", "&6")
                                message = message.replace("&7", "&7")
                                message = message.replace("&8", "&8")
                                message = message.replace("&9", "&9")
                                message = message.replace("&a", "&a")
                                message = message.replace("&b", "&b")
                                message = message.replace("&c", "&c")
                                message = message.replace("&d", "&d")
                                message = message.replace("&e", "&e")
                                message = message.replace("&f", "&f")
                                message = message.replace(character, "*")
                        message = message.replace("%0", "&0")
                        message = message.replace("%1", "&1")
                        message = message.replace("%2", "&2")
                        message = message.replace("%3", "&3")
                        message = message.replace("%4", "&4")
                        message = message.replace("%5", "&5")
                        message = message.replace("%6", "&6")
                        message = message.replace("%7", "&7")
                        message = message.replace("%8", "&8")
                        message = message.replace("%9", "&9")
                        message = message.replace("%a", "&a")
                        message = message.replace("%b", "&b")
                        message = message.replace("%c", "&c")
                        message = message.replace("%d", "&d")
                        message = message.replace("%e", "&e")
                        message = message.replace("%f", "&f")
                        message = message.replace("./", " /")
                        message = message.replace(".!", " !")
                        message = message.replace(".@", " @")
                        message = message.replace(".#", " #")
                        if message[len(message)-3] == "&":
                            print("You cannot use a color at the end of a message.")
                            return
                        if message.startswith("/"):
                            message = message.split(" ")
                            message[0] = message[0][1:]
                            message[len(message)-1] = message[len(message)-1][:len(message[len(message)-1])-1]
                            # It's a command
                            if message[0] == "kick":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    if message[1].lower() in self.factory.usernames:
                                        if message[2:]:
                                            self.factory.usernames[message[1].lower()].sendError("You were kicked by the console: %s" % " ".join(message[2:]))
                                        else:
                                            self.factory.usernames[message[1].lower()].sendError("You were kicked by the console!")
                                        print("%s has been kicked from the server." % message[1])
                                        continue
                                    else:
                                        print("User %s is not online." % message[1])
                                        continue
                            elif message[0] == "banb":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    username = message[1]
                                    if self.factory.isBanned(username):
                                        print("%s is already Banned." % username)
                                    else:
                                        if not len(message) > 2:
                                            print("Please give a reason.")
                                        else:
                                            self.factory.addBan(username, " ".join(message[2:]))
                                            if username in self.factory.usernames:
                                                ip = self.factory.usernames[username].transport.getPeer().host
                                                self.factory.addIpBan(ip, " ".join(message[2:]))
                                                self.factory.usernames[username].sendError("You got banned by the console: %s" % (" ".join(message[2:])))
                                                print("%s has been IPBanned." % ip)
                                            print("%s has been banned." % username)
                            elif message[0] == "ban":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    username = message[1]
                                    if self.factory.isBanned(username):
                                        print("%s is already Banned." % username)
                                    else:
                                        if not len(message) > 2:
                                            print("Please give a reason.")
                                        else:
                                            self.factory.addBan(username, " ".join(message[2:]))
                                            if username in self.factory.usernames:
                                                self.factory.usernames[username].sendError("You got banned by the console: %s" % (" ".join(message[2:])))
                                            print("%s has been banned." % username)
                            elif message[0] == "ipban":
                                if len(message) < 2:
                                    print("Please specify a username and the reason.")
                                else:
                                    username = message[1]
                                if username not in self.factory.usernames:
                                    print("That user is not online.")
                                else:
                                    ip = self.factory.usernames[username].transport.getPeer().host
                                    if self.factory.isIpBanned(ip):
                                        print("%s is already IPBanned." % ip)
                                    else:
                                        self.factory.addIpBan(ip, " ".join(params))
                                        self.factory.usernames[username].sendError("You got IPBanned by the console: %s" % (" ".join(message[2:])))
                                        print("%s has been IPBanned." % ip)
                            elif message[0] == "rank":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    try:
                                        print Rank(self, message, "console", True, self.factory)
                                    except:
                                        print("You must specify a rank and username.")
                            elif message[0] == "derank":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    try:
                                        print DeRank(self, message, "console", True, self.factory)
                                    except:
                                        print("You must specify a rank and username.")
                            elif message[0] == "spec":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    try:
                                        print Spec(self, message[1], "console", True, self.factory)
                                    except:
                                        print("Please specify a username.")
                            elif message[0] == "despec":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    try:
                                        print DeSpec(self, message[1], "console", True, self.factory)
                                    except:
                                        print("Please specify a username.")
                            elif message[0] == ("boot"):
                                try:
                                    world = str(message[1]).lower()
                                except:
                                    print("Please specify a worldname.")
                                    continue
                                try:
                                    self.factory.loadWorld("worlds/"+world, world)
                                except AssertionError:
                                    print("Either world %s doesn't exist, or is broken." % world)
                                    continue
                                else:
                                    print("World '"+world+"' booted.")
                            elif message[0] == ("shutdown"):
                                try:
                                    world = str(message[1]).lower()
                                except:
                                    print("Please specify a worldname.")
                                    continue
                                self.factory.unloadWorld(world)
                                print("World '"+world+"' shutdown.")
                            elif message[0] == ("new"):
                                if len(message) == 1:
                                    print("Please specify a new worldname.")
                                elif self.factory.world_exists(message[1]):
                                    print("Worldname in use.")
                                else:
                                    if len(message) == 2:
                                        template = "default"
                                    elif len(message) == 3 or len(message) == 4:
                                        template = message[2]
                                    world_id = message[1].lower()
                                    self.factory.newWorld(world_id, template)
                                    returned = self.factory.loadWorld("worlds/%s" % world_id, world_id)
                                    if returned == False:
                                        print("World %s loading failed." % world_id)
                                    self.factory.worlds[world_id].status["all_build"] = False
                                    if len(message) < 4:
                                        print("World '%s' made and booted." % world_id)
                            elif message[0] == ("me"):
                                if len(message) == 1:
                                    print("Please type an action.")
                                else:
                                    self.factory.sendMessageToAll(" ".join(message[1:]), "action")
                            elif message[0] == ("srb"):
                                self.factory.sendMessageToAll("%s[Server Reboot] %s" % (COLOUR_DARKRED, (" ".join(message[1:]) if len(message) > 1 else "Be back soon.")), "server", user="")
                            elif message[0] == ("srs"):
                                self.factory.sendMessageToAll("%s[Server Shutdown] %s" % (COLOUR_DARKRED, (" ".join(message[1:]) if len(message) > 1 else "See you later.")), "server")
                            elif message[0] == ("ircrehash"):
                                print("Rehashing the IRC Bot..")
                                self.factory.reloadIrcBot()
                            elif message[0] == ("rehash"):
                                print("Rehashing the Server Configuration..")
                                self.factory.reloadConfig()
                            elif message[0] == ("help"):
                                print("Whispers: @username message")
                                print("WorldChat: !worldname message")
                                print("StaffChat: #message")
                                print("Commands: /cmdlist")
                            elif message[0] == ("cmdlist"):
                                print("about boot ban banb cmdlist cpr derank despec gc help ircrehash ipban kick me new pll plr plu rank rehash say sendhb shutdown spec srb srs u")
                            elif message[0] == ("about"):
                                print("About The Server")
                                print("Powered by Arc %s" % (INFO_VERSION))
                                print("Name: %s" % self.factory.server_name)
                                try:
                                    print("URL: %s" % self.factory.heartbeat.url)
                                except AttributeError:
                                    print("URL: N/A (minecraft.net is offline)")
                            elif message[0] == ("say"):
                                if len(message) == 1:
                                    print("Please type a message.")
                                else:
                                    self.factory.sendMessageToAll(" ".join(message[1:]), "server")
                            elif message[0] == ("u"):
                                if len(message) == 1:
                                    print("Please type a message.")
                                else:
                                    self.factory.sendMessageToAll("[URGENT] %s" % (" ".join(message[1:])), "server")
                            elif message[0] == ("plr"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.unloadPlugin(message[1])
                                        self.factory.loadPlugin(message[1])
                                    except IOError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' reloaded." % message[1])
                            elif message[0] == ("plu"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.unloadPlugin(message[1])
                                    except IOError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' unloaded." % message[1])
                            elif message[0] == ("pll"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.loadPlugin(message[1])
                                    except IOError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' loaded." % message[1])
                            elif message[0] == "sendhb":
                                print("Sending heartbeat...")
                                self.factory.heartbeat.sendHeartbeat()
                            elif message[0] == "gc":
                                self.factory.cleanGarbage()
                            elif message[0] == "cpr":
                                self.factory.heartbeat.loop.stop()
                                del self.factory.heartbeat.loop
                                self.factory.heartbeat.loop = LoopingCall(self.factory.heartbeat.sendHeartbeat)
                                self.factory.heartbeat.loop.start(25)
                                print("Heartbeat sending restarted.")
                            else:
                                print("There is no %s command." % message[0])
                        elif message.startswith("@"):
                            # It's a whisper
                            try:
                                username, text = message[1:].strip().split(" ", 1)
                            except ValueError:
                                print("Please include a username and a message to send.")
                            else:
                                username = username.lower()
                                if username in self.factory.usernames:
                                    self.factory.usernames[username].sendWhisper(self.username, text)
                                    self.factory.logger.info("Console to %s: %s" % (username, text))
                                    self.factory.chatlogs["whisper"].write({"self": "Console", "other": username, "text": text})
                                    self.factory.chatlogs["main"].write({"self": "Console", "other": username, "text": text}, formatter=MSGLOGFORMAT["whisper"])
                                else:
                                    print("%s is currently offline." % username)
                        elif message.startswith("!"):
                            # It's a world message.
                            if len(message) < 2:
                                self.sendServerMessage("Please include a message and a world to send to.")
                            else:
                                world, out = message[1:len(message)-1].split(" ")
                                if world not in self.factory.worlds.keys():
                                    print("World %s is not booted." % world)
                                else:
                                    self.factory.sendMessageToAll(out, "world", user="Console")
                        elif message.startswith("#"):
                            # It's an staff-only message.
                            if len(message) == 1:
                                print("Please include a message to send.")
                            else:
                                text = message[1:]
                                text = text[:len(text)-1]
                                self.factory.sendMessageToAll(text, "staff", user="Console")
                        else:
                            self.factory.sendMessageToAll(message[0:len(message)-1], "chat", user="Console")
            except:
                print traceback.format_exc()
                self.logger.error(traceback.format_exc())
        finally:
            time.sleep(0.1)