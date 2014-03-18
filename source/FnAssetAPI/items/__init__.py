from .ItemFactory import ItemFactory
from .Item import Item

##
# @namespace python.items
# Items form a bridge between strong-typed objects and Entity metadata and
# strings. They are generally sub-classed and extended to additionally convert
# to/from a Host-specific API object in a 'centralised' fashion.
#
# Items follow a strict inheritance and derivation rules so please see the notes
# in the base classes
#
# @see python.items.Item.Item
# @see python.items.ItemFactory.ItemFactory
#

# Import the Item derived classes
from ._general import *
from ._2d import *
from ._group import *

