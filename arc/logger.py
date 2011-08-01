# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import logging, string, sys, time, os

class ColouredLogger(object):
    """
    This class is used to colour and log output.
    It handles colours, printing, and logging to console.log and
        the individual level log files.
    """
    cols = {
        "&0": "",
        "&1": "",
        "&2": "",
        "&3": "",
        "&4": "",
        "&5": "",
        "&6": "",
        "&7": "",
        "&8": "",
        "&9": "",
        "&a": "",
        "&b": "",
        "&c": "",
        "&d": "",
        "&e": "",
        "&f": "",
        "\x01" + "0": "",
        "\x01" + "1": "",
        "\x01" + "2": "",
        "\x01" + "3": "",
        "\x01" + "4": "",
        "\x01" + "5": "",
        "\x01" + "6": "",
        "\x01" + "7": "",
        "\x01" + "8": "",
        "\x01" + "9": "",
        "\x01" + "0": "",
        "\x01" + "a": "",
        "\x01" + "b": "",
        "\x01" + "c": "",
        "\x01" + "d": "",
        "\x01" + "e": "",
        "\x01" + "f": "",
    }

    nocol = cols

    def __init__(self, debug=False, level=logging.INFO):
        "Constructor, set everything up"
        self.debugswitch = debug
        try:
            self.logfile = "logs/console/console.log"
            self.infolog = "logs/levels/info.log"
            self.errorlog = "logs/levels/error.log"
            self.warnlog = "logs/levels/warn.log"
            self.criticallog = "logs/levels/critical.log"
            self.debuglog = "logs/levels/debug.log"
            self.commandlog = "logs/commands.log"
        except Exception as a:
            pass
        try:
            from colorama import Fore, Back, Style
            self.cols = {
                # Standard Minecraft colours
                "&0": Fore.BLACK + Back.WHITE + Style.NORMAL,            # Black, inverse
                "&1": Fore.BLUE + Back.RESET + Style.DIM,                # Blue, dark
                "&2": Fore.GREEN + Back.RESET + Style.DIM,               # Green, dark
                "&3": Fore.CYAN + Back.RESET + Style.DIM,                # Cyan, dark
                "&4": Fore.RED + Back.RESET + Style.DIM,                 # Red, dark
                "&5": Fore.MAGENTA + Back.RESET + Style.DIM,             # Magenta, dark
                "&6": Fore.YELLOW + Back.RESET + Style.DIM,              # Yellow, dark
                "&7": Fore.WHITE + Back.RESET + Style.NORMAL,            # Grey, light
                "&8": Fore.WHITE + Back.RESET + Style.NORMAL,            # Grey, dark
                "&9": Fore.BLUE + Back.RESET + Style.NORMAL,             # Blue, light
                "&a": Fore.GREEN + Back.RESET + Style.NORMAL,            # Green, light
                "&b": Fore.CYAN + Back.RESET + Style.NORMAL,             # Cyan, light
                "&c": Fore.RED + Back.RESET + Style.NORMAL,              # Red, light
                "&d": Fore.MAGENTA + Back.RESET + Style.NORMAL,          # Magenta, light
                "&e": Fore.YELLOW + Back.RESET + Style.NORMAL,           # Yellow, light
                "&f": Fore.WHITE + Back.RESET + Style.BRIGHT,            # White, normal
                # Special colours for highlighting text in the console
                "\x01" + "0": Fore.WHITE + Back.RESET + Style.BRIGHT,    # A reset. Inverse inverse black on black?
                "\x01" + "1": Fore.BLUE + Back.WHITE + Style.DIM,        # Blue, dark, inverse
                "\x01" + "2": Fore.GREEN + Back.WHITE + Style.DIM,       # Green, dark, inverse
                "\x01" + "3": Fore.CYAN + Back.WHITE + Style.DIM,        # Cyan, dark, inverse
                "\x01" + "4": Fore.RED + Back.WHITE + Style.DIM,         # Red, dark, inverse
                "\x01" + "5": Fore.MAGENTA + Back.WHITE + Style.DIM,     # Magenta, dark, inverse
                "\x01" + "6": Fore.YELLOW + Back.WHITE + Style.DIM,      # Yellow, dark, inverse
                "\x01" + "7": Fore.WHITE + Back.WHITE + Style.NORMAL,    # Grey, light, inverse
                "\x01" + "8": Fore.WHITE + Back.WHITE + Style.DIM,       # Grey, dark, inverse
                "\x01" + "9": Fore.BLUE + Back.WHITE + Style.NORMAL,     # Blue, light, inverse
                "\x01" + "a": Fore.GREEN + Back.WHITE + Style.NORMAL,    # Green, light, inverse
                "\x01" + "b": Fore.CYAN + Back.WHITE + Style.NORMAL,     # Cyan, light, inverse
                "\x01" + "c": Fore.RED + Back.WHITE + Style.NORMAL,      # Red, light, inverse
                "\x01" + "d": Fore.MAGENTA + Back.WHITE + Style.NORMAL,  # Magenta, light, inverse
                "\x01" + "e": Fore.YELLOW + Back.WHITE + Style.NORMAL,   # Yellow, light, inverse
                "\x01" + "f": Fore.WHITE + Back.RESET + Style.BRIGHT,    # A reset. White on white?
            }
        except:
            pass

    def stdout(self, data):
        "Output to stdout, parsing colours."
        origdata = data
        for element in self.cols.keys():
            data = string.replace(data, element, self.cols[element])
        try:
            sys.stdout.write(data + "\n")
        except Exception as e:
            print("Unable to write directly to stdout! Data: %s" % origdata)
            print("%s" % e)

    def stderr(self, data):
        "Output to stderr, parsing colours."
        origdata = data
        for element in self.cols.keys():
            data = string.replace(data, element, self.cols[element])
        try:
            sys.stderr.write(data + "\n")
        except Exception as e:
            self.stdout(data)

    def log(self, data, file = None):
        if file is None:
            file = self.logfile
        "Outputs to the console.log file"
        for element in self.nocol.keys():
            data = string.replace(data, element, self.nocol[element]) # Do not log colour codes in file
        file = open(file, "a")
        file.write(data + "\n")
        file.flush()
        os.fsync(file.fileno())
        file.close()

    def info(self, data):
        "INFO level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - &2INFO&f - "
        done = "&f" + atime + status + data
        self.log(done)
        self.log(done, self.infolog)
        self.stdout(done)

    def warn(self, data):
        "WARN level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - &eWARN&f - "
        done = "&f" + atime + status + data
        self.log(done)
        self.log(done, self.warnlog)
        self.stderr(done)

    warning = warn

    def error(self, data):
        "ERROR level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - &cERROR&f - "
        done = "&f" + atime + status + data
        self.log(done)
        self.log(done, self.errorlog)
        self.stdout(done)

    def critical(self, data):
        "CRITICAL level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - " + "\x01" + "c" + "CRITICAL&f - "
        done = "&f" + atime + status + data
        self.log(done)
        self.log(done, self.criticallog)
        self.stdout(done)
        
    def command(self, data):
        "CRITICAL level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - %sCOMMAND&f - " % (Fore.MAGENTA + Back.RESET + Style.BRIGHT)
        done = "&f" + atime + status + data
        self.log(done)
        self.log(done, self.commandlog)
        self.stdout(done)

    def debug(self, data):
        "DEBUG level output"
        if self.debugswitch:
            atime = time.strftime("%d %b (%H:%M:%S)")
            status = " - &9DEBUG &f - "
            done = "&f" + atime + status + data
            self.log(done)
            self.log(done, self.debuglog)
            self.stdout(done)

class ChatLogHandler(object):
    """
    A Chat Log handler. Given a file and a format, starts
    listening for logs to get in.
    """

    def __init__(self):
        self.worldlog = "logs/world.log"
        self.whisperlog = "logs/whisper.log"
        self.stafflog = "logs/staff.log"
        self._write(self.worldlog, "\n -------------------------------------------- \n")
        self._write(self.whisperlog, "\n -------------------------------------------- \n")
        self._write(self.stafflog, "\n -------------------------------------------- \n")

    def world(self, player, world, message):
        data = "[%s] %s (in %s): %s" % (time.strftime("%d %b (%H:%M:%S)"), player, world, message)
        self._write(self.worldlog, data)

    def staff(self, player, message):
        data = "[%s] %s: %s" % (time.strftime("%d %b (%H:%M:%S)"), player, message)
        self._write(self.stafflog, data)

    def whisper(self, player, target, message):
        data = "[%s] %s -> %s: %s" % (time.strftime("%d %b (%H:%M:%S)"), player, target, message)
        self._write(self.whisperlog, data)

    def _write(self, file, data):
        file = open(file, "a")
        file.write("%s\n" % data)
        file.flush()
        file.close()
