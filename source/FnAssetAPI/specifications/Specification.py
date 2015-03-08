import inspect

from .SpecificationBase import SpecificationBase
from .SpecificationFactory import SpecificationFactory

# We want these properties to be available here, so people just deriving a
# 'Specificaion' don't need to worry about where these properties really come
# from - we don't want most people to have to care about the 'core' module.
from ..core.properties import UntypedProperty, TypedProperty


__all__ = ['Specification', 'UntypedProperty', 'TypedProperty']


class Specification(SpecificationBase):
  """

  The simplest form of Specification in common use. It extends the base
  specification to better define the schema.

  If introduces the notion that the @ref specification_schema consists of two
  parts, separated by a token - the 'prefix' and 'type'. For example:

    @li `core.locale:image.catalog`
    @li **prefix**: `core.locale`
    @li **type**: `image.catalog`

  This is to allow common prefixes to be best represented by a single derived
  class. For example, several commands would have different types, but the same
  prefix, which allows the generic @ref CommandSpecification class to be used
  to manipulate these objects.

  Types should also be hierarchical, in a way that indicates compatibility with
  the class hierarchy.  It should be that a file.image.texture can degenerate
  into a file.image if necessary. As such, a properties of a more derived
  specification should always be a superset of any other specification
  indicated by its 'type'.

  The @ref SpecificationFactory understands the concept of prefixes, etc...
  when wrapping on instantiating a Specification from data.

  """
  __metaclass__ = SpecificationFactory

  _prefix = "core"
  _type = ""


  def __init__(self, data=None):
    schema = self.generateSchema(self._prefix, self._type)
    super(Specification, self).__init__(schema, data)


  def __str__(self):
    data = []
    for k,v in self._data.iteritems():
      if v is not None:
        data.append("'%s':%s" % (k,repr(v)))
    return "%s({%s})" % (self.__class__.__name__, ", ".join(data))


  def __repr__(self):
    return str(self)


  def isOfType(self, typeOrTypes, includeDerived=True, prefix=None):
    """

    Returns whether the specification is of a requested type, by comparison of
    the type string.

    @param typeOrTypes, [str or Specification, or list of] The types to
    compare against. eg:
     @code
        spec.isOfType(FnAssetAPI.specifications.FileSpecification)
        spec.isOfType(('file', 'group.shot'), includeDerived=True)
     @endcode

    @param includeDerived bool, If True, then the match will include any
    specifialisations of the supplied type. For example if you used a
    typeString of "file", a specification of type "file.image" would still
    match. If this is false, it must be the exact type match.

    @param prefix str, An optional prefix string, to allow complete comparison
    of the schema, not just the type.

    @note This call doesn't not consider the 'prefix' of the Specification,
    unless the additional 'prefix' argument is supplied.

    """
    if self._type and self._prefix:
      ourPrefix = self._prefix
      ourType = self._type
    else:
      ourPrefix, ourType = self.schemaComponents()

    if prefix and not prefix == ourPrefix:
      return False

    if not isinstance(typeOrTypes, (list, tuple)):
      typeOrTypes = (typeOrTypes,)

    for t in typeOrTypes:
      if inspect.isclass(t) and issubclass(t, Specification):
        t = t._type
      if includeDerived:
        if ourType.startswith(t):
          return True
      elif ourType == t:
          return True

    return False


  def getField(self, name, defaultValue=None):
    """

    Fetches the property from the specification, if present, otherwise returns
    the default value.

    This is short hand for the following code, that avoids either copying the
    data, or exposing the mutable data dictionary. Consequently, it should be
    used by preference.

    @code
    data = specification.getData(copy=False).get(name, defaultValue)
    @endcode

    """
    return self._data.get(name, defaultValue)


