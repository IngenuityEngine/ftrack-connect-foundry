import inspect

from . import properties


__all__ = ['FixedInterfaceObject']


class FixedInterfaceObject(object):
  """

  This class is a simple extension to object, to dis-allow get/set of any
  attributes not defined with the class. This can be useful to make
  introspectable objects with meaningful help() messages by creating data
  members like so:

  /code
  numCakes = TypedProperty(int, doc="Some member variable")
  edible = UntypedProperty()
  /endcode

  """

  def __getattr__(self, name):
    # This is only called if the attribute is not found by other means, ie: it
    # has not been defined in the class definition, etc...
    classname = self.__class__.__name__
    raise AttributeError, "%s does not have an attribute '%s'" % (classname, name)


  def __setattr__(self, name, value):
    if name.startswith('_') or name in self.getDefinedPropertyNames():
      object.__setattr__(self, name, value)
    else:
      classname = self.__class__.__name__
      raise AttributeError, "%s does not have an attribute '%s'" % (classname, name)


  @classmethod
  def getDefinedPropertyNames(cls):
    """

    @return list, A list of property names, sorted by their specified order.

    """
    predicate = lambda m : isinstance(m, properties.UntypedProperty)
    members = inspect.getmembers(cls, predicate)

    # We want to sort by the 'order' key if its greater than -1
    sortFn = lambda p : p[1].order if p[1].order > -1 else 9999999
    members.sort(key=sortFn)

    # Extract the names from the now sorted tuple list
    return [ name for name,value in members ]


