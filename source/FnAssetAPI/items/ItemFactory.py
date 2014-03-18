from .. import logging
from ..constants import *
from ..core.properties import UntypedProperty


__all__ = ['ItemFactory']


class ItemFactory(type):
  """

  The ItemFactory keeps track of any derived classes, without needing a
  separate registration stage. They can be found in Item.classMap.

  The factory also improves the configuration of any Properties of the
  python.core.FixedInterfaceObject, by setting their dataName to match the
  property name. This makes it much more straight forward for they implementors
  of Item-derived classes, as the don't need to worry about filling in the
  dataName field - yet the values will be stored in keys with the name of the
  property prefixed with '__'.

  @note Sometimes when deriving from Item, you may wish to simply supplement
  host-side behaviour without introducing a new unique type string. In this
  case, its important to set the **_factoryIgnore** property on the Item to
  True, which will instruct the factory to omit that specific class from the
  type map. You can then simply manually instantiate your own Class in host-side
  code where you need it.

  """

  classMap = {}

  def __new__(cls, name, bases, namespace):

    # Conform the data name for safety
    for k,v in namespace.items():
      if isinstance(v, UntypedProperty):
        v.dataName = "__%s" % k

    newcls = super(ItemFactory, cls).__new__(cls, name, bases, namespace)

    ## @todo Should we synthesize _type here from MRO inspection so that
    # implementers don't have to worry about knowing the parent type to
    # extend?

    if namespace.get('_factoryIgnore', False):
      if newcls._type in cls.classMap:
        logging.log("Duplicate ItemFactory registration for: %s, previous: %s new: %s"
            % (newcls._type, cls.classMap[newcls._type], newcls), logging.kWarning)

      cls.classMap[newcls._type] = newcls

    return newcls



