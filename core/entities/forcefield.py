for var_index in range(len(entitylist)):
    var_entity = entitylist[var_index]
    identity = var_entity[0]
    if identity != "forcefield":
        rx,ry,rz = var_entity[1]
        xd = rx-x
        yd = ry-y
        zd = rz-z
        distance = math.sqrt((xd*xd + yd*yd + zd*zd))
        if distance <= 10:
            var_dellist.append(var_index)
            block = 0
            self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
            self.client.sendBlock(rx, ry, rz, block)