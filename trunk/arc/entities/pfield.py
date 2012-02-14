# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

for var_index in range(len(entitylist)):
    var_entity = entitylist[var_index]
    identity = var_entity[0]
    ownername = entity[4]
    ownerclient = self.client.username
    if ownername in worldusernamelist:
        x, y, z = (ownerclient.x >> 5, ownerclient.y >> 5, ownerclient.z >> 5)
        if identity != "pfield" or "forcefield":
            rx, ry, rz = var_entity[1]
            xd = rx - x
            yd = ry - y
            zd = rz - z
            distance = math.sqrt((xd * xd + yd * yd + zd * zd))
            if distance <= 3:
                var_dellist.append(var_index)
                block = 0
                self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
                self.client.sendBlock(rx, ry, rz, block)
    else:
        var_dellist.append(var_index)
