vx, vy, vz = entity[4]
rx, ry, rz = var_position
x, y, z = int(round(rx)), int(round(ry)), int(round(rz))
rx, ry, rz = rx+vx, ry+vy, rz+vz
var_position = rx, ry, rz
cx, cy, cz = int(round(rx)), int(round(ry)), int(round(rz))
var_cango = True
try:
    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx, cy, cz)])
    if blocktocheck != 0:
        var_cango = False
except:
    var_cango = False
if (x,y,z) != (cx,cy,cz):
    if var_cango:
        if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)] in ('(','\x00'):
            block = '\x00'
            world[x, y, z] = block
            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
            self.client.sendBlock(x, y, z, block)
        x,y,z = cx,cy,cz
        block = chr(40)
        world[x, y, z] = block
        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
        self.client.sendBlock(x, y, z, block)
    else:
        del entities_childerenlist[entities_childerenlist.index(entity[5])]
        var_dellist.append(index)
        if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)]) in [0,40]:
            block = '\x00'
            world[x, y, z] = block
            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
            self.client.sendBlock(x, y, z, block)
        x,y,z = cx,cy,cz
        block = chr(entity[6])
        try:
            if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx,cy,cz)]) not in var_unpainablelist:
                world[x, y, z] = block
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                self.client.sendBlock(x, y, z, block)
        except:
            pass
