# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

class IUSer(Interface):
    """
    I am the interface that defines all methods a 'user' should have.
    """

    factory = Attribute("The factory")
    username = Attribute("Username")
    logger = Attribute("The logger object")
    