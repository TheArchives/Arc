# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

w = y
entitylist.append(["ladder", (x, y, z), 7, 7, w])
self.client.sendServerMessage("A ladder was created.")
self.client.sendSplitServerMessage("A single ladder teleports a person to the closest air block in its column.")