# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

var_cango = False
var_open = False
closestposition = (0, 0)
closestclient = None
closestdistance = None
if entity[5] == True:
    try:
        blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)])
        entity[4] = blocktocheck
        entity[5] = False
    except:
        blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)])
        entity[4] = blocktocheck
for entry in userpositionlist:
    client = entry[0]
    var_pos = entry[1]
    i,j,k = var_pos
    xd = i-x
    yd = j-y
    zd = k-z
    distance = math.sqrt((xd*xd + yd*yd + zd*zd))
    if distance < 4:
        var_open = True
if var_open:
    block = entity[4]
    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
    self.client.sendBlock(x, y, z, block) 
else:
    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)])
    if blocktocheck == entity[4] or chr(0):
        var_cango = True
if var_cango == True:
    block = 0
    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
    self.client.sendBlock(x, y, z, block)
