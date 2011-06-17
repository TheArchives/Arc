w = y
entitylist.append(["ladder", (x, y, z), 7, 7, w])
self.client.sendServerMessage("A ladder was created.")
self.client.sendSplitServerMessage("A single ladder teleports a person to the closest air block in its column.")