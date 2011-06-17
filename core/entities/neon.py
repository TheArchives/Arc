var_colorindex = int(var_abstime*2)%5
if var_colorindex != entity[4]:
    entity[4] = var_colorindex
    block = entity[5+var_colorindex]
    world[x, y, z] = block
    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
    self.client.sendBlock(x, y, z, block)
