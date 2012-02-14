# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

if len(parts) < 3:
    self.client.sendServerMessage("Please give a color (blue, red, white, green)")
    var_continue = False
if var_continue:
    color = parts[2]
    if color not in ["blue", "red", "white", "green"]:
        self.client.sendServerMessage("%s is not a valid color for neon." % color)
        var_continue = False
    if var_continue:
        self.var_entityparts = [color]
        self.var_entityselected = "neon"