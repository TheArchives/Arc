

if len(entitylist) <= maxentitiesperworld:
    x,y,z = var_position
    randnum = randint(1,6)
    if randnum < 4:
        entitylist.append(["zombie",(x,y+1,z),8,8])
    elif randnum == 6:
        entitylist.append(["creeper",(x,y+1,z),8,8])
    else:
        entitylist.append(["blob",(x,y+1,z),8,8])
