if ph >= 224 or ph < 32:
    var_orientation = 0
elif 32 <= ph < 96:
    var_orientation = 1
elif 96 <= ph < 160:
    var_orientation = 2
elif 160 <= ph < 224:
    var_orientation = 3
entitylist.append(["cannon",(x,y,z),8,8,None,var_orientation,False])
self.client.sendSplitServerMessage("A cannon was created, load it by placing TNT on the obsidian block.")