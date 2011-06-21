# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

if len(parts) < 5:
    self.client.sendServerMessage("For Make-a-Mob please use:")
    self.client.sendServerMessage("/entity var blocktype MovementBehavior NearBehavior")
    self.client.sendServerMessage("MovementBehavior: follow engulf pet random none")
    self.client.sendServerMessage("NearBehavior: kill explode none")
    var_continue = False
else:
    if parts[2] == 0 or parts[2].lower() == "air" or parts[2].lower() == "blank" or parts[2].lower() == "clear" or parts[2].lower() == "empty" or parts[2].lower() == "none" or parts[2].lower() == "nothing":
        self.client.sendServerMessage("Sorry, no invisible Make-a-Mobs allowed.")
        var_continue = False
    if var_continue:
        try:
            block = int(parts[2])
        except ValueError:
            try:
                block = globals()['BLOCK_%s' % parts[2].upper()]
            except KeyError:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[2])
                var_continue = False
        if var_continue:
            validmovebehaviors = ["follow","engulf","pet","random","none"]
            movementbehavior = parts[3]
            if movementbehavior not in validmovebehaviors:
                self.client.sendServerMessage("'%s' is not a valid MovementBehavior." % movementbehavior)
                var_continue = False
            if var_continue:
                validnearbehaviors = ["kill","explode","none"]
                nearbehavior = parts[4]
                if nearbehavior not in validnearbehaviors:
                    self.client.sendServerMessage("'%s' is not a valid NearBehavior." % nearbehavior)
                    var_continue = False
                if var_continue:
                    self.var_entityselected = "var"
                    self.var_entityparts = [block,movementbehavior,nearbehavior]
