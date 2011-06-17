for var_index in range(len(entitylist)):
    var_entity = entitylist[var_index]
    identity = var_entity[0]
    if identity != "inhibitor":
        rx,ry,rz = var_entity[1]
        var_dellist.append(var_index)
        block = 0
        self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
        self.client.sendBlock(rx, ry, rz, block)
