# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

class BlbManagerServerPlugin():
    """
    A class that handles blb I/Os. Apply changes and respawn people
    when necessary.
    """

    name = "BlbManagerPlugin"
 
    def acceptChangeset(self, client, changeset):
        """ Accepts a changeset. 
        The changeset can either be a range or a generator.
        """
        pass

    hooks = {
        }

serverPlugin = BlbManagerServerPlugin