import logging, string, sys, time

class ColouredLogger(logging.Logger):
    """
    This class is used to colour and log output.
    It handles colours, printing, and logging to console.log.
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

    def __init__(self, level=logging.INFO, debug=False):
        "Constructor, set everything up"
        self.debugswitch = debug
        self.logfile = open("logs/console/console.log", "a")
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
        for element in self.cols.keys():
            data = string.replace(data, element, self.cols[element])
        sys.stdout.write(data + "\n")
        self.log(data)

    def stderr(self, data):
        "Output to stderr, parsing colours."
        for element in self.cols.keys():
            data = string.replace(data, element, self.cols[element])
        sys.stderr.write(data + "\n")
        self.log(data)

    def log(self, data):
        "Outputs to the console.log file"
        for element in self.nocol.keys():
            data = string.replace(data, element, self.nocol[element])
        self.logfile.write(data + "\n")
        self.logfile.flush()

    def info(self, data):
        "INFO level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " -   &2INFO&f   - "
        done = "&f" + atime + status + data
        self.stdout(done)

    def warn(self, data):
        "WARN level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " -   &eWARN&f   - "
        done = "&f" + atime + status + data
        self.stderr(done)

    warning = warn

    def error(self, data):
        "ERROR level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " -   &cERROR&f  - "
        done = "&f" + atime + status + data
        self.stdout(done)

    def critical(self, data):
        "CRITICAL level output"
        atime = time.strftime("%d %b (%H:%M:%S)")
        status = " - " + "\x01" + "c" + "CRITICAL&f - "
        done = "&f" + atime + status + data
        self.stdout(done)

    def debug(self, data):
        "DEBUG level output"
        if self.debugswitch:
            time = time.strftime("%d %b (%H:%M:%S)")
            status = " -  &9DEBUG  &f - "
            done = "&f" + time + status + data
            self.stdout(done)