from ..core import FixedInterfaceObject


__all__ = ['SpecificationBase']


class SpecificationBase(FixedInterfaceObject):

  """

  The simplest of Specifications that just holds the data store, and schema
  type. This can be used in cases that have no need to work with the data in
  any type-specific way.

  """

  __kPrefixSeparator = ':'
  _data = {}

  def __init__(self, schema, data=None):

    self.__schema = schema
    # The default for data is None, not {} to avoid mutable defaults issues
    # This data is written to by the SpecificationProperty class
    self._data = data if data else {}


  @classmethod
  def generateSchema(cls, prefix, type):
    """

    To be used over naive string concatenation to build a schema string.

    @return str, The schema string for the given prefix and type.

    """
    return "%s%s%s" % (prefix, cls.__kPrefixSeparator, type)


  @classmethod
  def schemaComponents(cls, schema):
    """

    Splits a schema string into a prefix, type tuple. Should be used over
    manual attempts at tokenization.

    @return tuple, (prefix, type), The prefix will be an empty string if there
    is none.

    """
    if cls.__kPrefixSeparator in schema:
      return schema.rsplit(cls.__kPrefixSeparator, 1)
    else:
      return "", schema


  def getPrefix(self):
    """

    @return str, the prefix of this specifications schema, or an empty string.

    """
    return self.schemaComponents(self.__schema)[0]


  def getType(self):
    """

    @return str, the schemas type, without prefix or separator token.

    """
    return self.schemaComponents(self.__schema)[1]


  def getSchema(self):
    """

    @return str, The schema identifier for the data held in the specification.

    """
    return self.__schema


  def getData(self, copy=True):
    """

    @param copy bool, When True (default) then a copy of the data will be
    returned, rather than a reference, to help avoid mutating the
    specifications data by accident.

    @return dict, The data of the specification.

    """
    if copy:
      return dict(self._data)
    else:
      return self._data

  def _setSchema(self, schema):
    self.__schema = schema

  def __str__(self):
    data = []
    for k,v in self._data.iteritems():
      if v is not None:
        data.append("'%s':%s" % (k,repr(v)))
    return "SpecificationBase('%s', {%s})" % (self.__schema, ", ".join(data))


  def __repr__(self):
    return str(self)




