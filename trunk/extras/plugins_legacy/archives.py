# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import datetime

from arc.decorators import *

class ArchivesPlugin(object):
    name = "ArchivesPlugin"
    hooks = {
        "onPlayerConnect": "gotClient",
        "consoleLoaded": "gotConsole"
    }

    commands = {
        "aname": "commandAname",
        "atime": "commandAtime",
        "aboot": "commandAboot",
    }

    def gotClient(self, data):
        data["client"].selected_archive_name = None
        data["client"].selected_archive = None

    def gotConsole(self):
        self.factory.console.selected_archive_name = None
        self.factory.console.selected_archive = None

    @config("usage", "searchterm")
    def commandAname(self, data):
        "Selects an archive name, by part or all of the name."
        if len(data["parts"]) == 1:
            self.client.sendServerMessage("Please enter a search term")
        else:
            # See how many archives match
            searchterm = data["parts"][1].lower()
            matches = [x for x in self.factory.archives if searchterm in x.lower()]
            if len(matches) == 0:
                data["client"].sendServerMessage("No matches for '%s'" % searchterm)
            elif len(matches) == 1:
                data["client"].sendServerMessage("Selected '%s'." % matches[0])
                data["client"].selected_archive_name = matches[0]
            else:
                data["client"].sendServerMessage("%s matches! Be more specific." % len(matches))
                for match in matches[:3]:
                    data["client"].sendServerMessage(match)
                if len(matches) > 3:
                    data["client"].sendServerMessage("..and %s more." % (len(matches) - 3))

    @config("usage", "yyyy/mm/dd hh_mm")
    def commandAtime(self, data):
        "Selects the archive time to get"
        if len(data["parts"]) == 2:
            # Hackish. So sue me.
            if data["parts"][1].lower() == "newest":
                data["parts"][1] = "2020/1/1"
                data["parts"].append("00_00")
            elif data["parts"][1].lower() == "oldest":
                data["parts"][1] = "1970/1/1"
                data["parts"].append("00_00")
        if len(data["parts"]) < 3:
            data["client"].sendServerMessage("Please enter a date and time.")
        elif not data["client"].selected_archive_name or data["client"].selected_archive_name not in self.factory.archives:
            data["client"].sendServerMessage("Please select an archive name first. (/aname)")
        else:
            try:
                when = datetime.datetime.strptime(parts[1] + " " + parts[2], "%Y/%m/%d %H:%M:%S")
            except ValueError:
                data["client"].sendServerMessage("Please use the format yyyy/mm/dd hh_mm")
            else:
                # Pick the closest time
                times = []
                for awhen, filename in self.factory.archives[data["client"].selected_archive_name].items():
                    dt = when - awhen
                    secs = abs(dt.seconds + (dt.days * 86400))
                    times.append((secs, awhen, filename))
                times.sort()
                data["client"].selected_archive = times[0][2]
                data["client"].sendServerMessage("Selected archive from %s" % times[0][1].strftime("%Y/%m/%d %H_%M"))

    def commandAboot(self, data):
        "Boots an archive after you've done /aname and /atime"
        if not data["client"].selected_archive:
            if not data["client"].selected_archive_name:
                data["client"].sendServerMessage("Please select an archive name first. (/aname)")
            else:
                data["client"].sendServerMessage("Please select an archive time first. (/atime)")
        else:
            world_id = self.factory.loadArchive(data["client"].selected_archive)
            data["client"].sendServerMessage("Archive loaded, as %s" % world_id)
            if data["fromloc"] == "user": data["client"].changeToWorld(world_id)

serverPlugin = ArchivesPlugin