from .. import logging
from .SpecificationBase import SpecificationBase
from ..core.properties import UntypedProperty


__all__ = ['SpecificationFactory']


class SpecificationFactory(type):
  """

  The Factory provides facility to create Specifications of the most derived
  class. Useful when restoring data from an @ref Entity for specific use.

  """

  classMap = {}

  def __new__(cls, name, bases, namespace):

    # Make sure properties have a suitable data name and store
    for k,v in namespace.items():
      if isinstance(v, UntypedProperty):
        v.dataVar = '_data'
        v.dataName = k

    newcls = super(SpecificationFactory, cls).__new__(cls, name, bases, namespace)
    if not hasattr(newcls, '__factoryIgnore'):
      if newcls._type:
        key = newcls.generateSchema(newcls._prefix, newcls._type)
      else:
        key = newcls._prefix
      cls.classMap[key] = newcls
    return newcls


  @classmethod
  def instantiate(cls, schema, data):
    """

    Creates a new Specification that contains the supplied data. The most
    derived class that matches the schema will be used. If no class has been
    registered with the exact scheme, then attempts will be made to find a
    class that matches the prefix. If all attempts fail, a @ref
    SpecificationBase will be used.

    """


    if not schema:
      logging.log(("SpecificationFactory.instantiate() No schema specified"), logging.kDebugAPI)
      return None

    customCls = cls.classMap.get(schema, None)
    prefix, type = SpecificationBase.schemaComponents(schema)
    if not customCls:
      customCls = cls.classMap.get(prefix)
    if customCls:
      instance = customCls(data)
      instance._setSchema(schema)
      instance._type = type
      return instance
    else:
      logging.log(("SpecificationFactory.instantiate(%r) Unable to find a "
          +"mapping for Specification schema") % schema, logging.kDebugAPI)
      return SpecificationBase(schema, data)


  @classmethod
  def upcast(cls, specification):
    schema = specification.getSchema()
    return cls.instantiate(schema, specification.getData(copy=False))

