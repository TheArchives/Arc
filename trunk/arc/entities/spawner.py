# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

if len(entitylist) <= maxentitiesperworld:
    x, y, z = var_position
    randnum = randint(1, 6)
    if randnum < 4:
        entitylist.append(["zombie", (x, y + 1, z), 8, 8])
    elif randnum == 6:
        entitylist.append(["creeper", (x, y + 1, z), 8, 8])
    else:
        entitylist.append(["blob", (x, y + 1, z), 8, 8])