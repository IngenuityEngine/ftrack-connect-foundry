from .. import logging
from ..core import FixedInterfaceObject
from ..core.properties import TypedProperty
from ..constants import *

from .ItemFactory import ItemFactory


__all__ = ['Item']


class Item(FixedInterfaceObject):
  """

  Items form concrete classes with known accessors to represent something that
  a @ref Host may wish to treat as an asset.
  They also provide convenience methods to convert them to a @ref
  Specification, @ref metadata or suitable @ref mime_data for use with other
  calls in the API.

  It's vital that the _type attribute is properly configured. It is used for
  reconstruction, and should follow the primary inheritance chain of the Item's
  class inheritance. For example

  A 'texture' Item that derives from ImageItem (which derives from FileItem)
  should have a _type of "file.image.texture". To be safe, use the following
  syntax:

    @li <tt>_type = "@s.texture" % ImageItem._type</tt>

  Items use needlessly overcomplicated meta-programming to allow
  auto-registration of any derived classes. This is to simplify re-construction
  when we get the C binding up and running, and when round-tripping to a
  Manager. The idea is that the _type can be mapped back to a Class, and
  decomposition of the _type string will allow automatic up-casting should the
  most derived class not be available.

  @see python.items.ItemFactory.ItemFactory

  """

  __metaclass__ = ItemFactory

  # The _type is used for persistent storage and class re-instantiation
  _type = "item"

  # The _primaryProperty is the property that is passed to register() and
  # populated from resolve().
  _primaryProperty = None

  # All Item's can hold and map to an Entity
  _entity = None

  ##
  # @name Properties
  ## @{

  # Property name should always match kField_HintName
  nameHint = TypedProperty(str, doc="A hint for the name of the Entity the "
      +"Item represents, in cases where it is not already determined")

  ## @}

  def __str__(self):

    vals = []
    properties = self.getDefinedPropertyNames()
    for p in properties:
      v = getattr(self,p)
      if v is not None:
        vals.append("%s:%s" % ( p, repr(v)))

    vals.append("entity:%r" % self._entity)

    return "%s({%s})" % (self.__class__.__name__, ", ".join(vals))


  def __repr__(self):
    return str(self)


  ##
  # @name Entity mapping
  # As the purpose of an Item is to map between an Entity, and some other
  # strong object with known properties, these methods deal with setting up
  # this relationship.
  #
  ## @{

  def getEntity(self):
    """

    @return python.Entity.Entity, The Entity held by the Item, or None if none
    has been set.

    """
    return self._entity

  def setEntity(self, entity, read=False, context=None):
    """

    Sets the Entity that should be associated with this Item.

    @param entity python.Entity.Entity, The Entity instance.

    @param read bool [False] If True, the Item's properties will be updated to
    hold the values stored in the supplied Entity.

    """
    self._entity = entity
    if read:
      self.readEntity(context)


  def updateEntity(self, context=None):
    """

    This call first requires that an Entity has been set in the Item, if one
    has then the Entities \ref metadata will be updated to match the current values
    of the Item's properties.

    @warning The property that represents the Primary String is effectively
    read-only once the Entity has been registered.

    @exceptions RuntimeError if there is no Entity set in the Item

    """

    entity = self.getEntity()
    if not entity:
      ## @todo Be a bit more professional here
      raise RuntimeError("Item has no Entity")

    if not context:
      session = FnAssetAPI.SessionManager.currentSession()
      context = session.createContext()
      context.locale = self.toLocale()
      context.access = context.kWrite

    entity.setMetadata(self.toMetadata(), context)

  ## @}


  ##
  # @name Decomposition
  # In order to represent an Entity, it's useful to be able to decompose an
  # Item into constituent parts - such as a Specification or Metadata.
  #
  # In order to facilitate easy registration, all Items have a property that
  # is considered to be the 'string value' of the item. This string value
  # should be used when registering the Item with a Manager, and is considered
  # to be the same string as resolving the resultant Entity would give.
  #
  ## @{

  def getString(self):
    """

    The 'string' represents the primary string for an Entity - that which
    should be passed to register().

    """
    value = getattr(self, self._primaryProperty, None)
    return value if value else ""

  def setString(self, value):
      setattr(self._primaryProperty, value)


  def toSpecification(self, spec=None):
    """

    Produces a \ref specification to represent this Item. This is only usually
    meaningful when called on a derived class.

    @param spec python.specifications.Specification.Specification an existing
    Specification that should be configured, rather than creating a new one.

    @return python.specifications.Specification.Specification the configured
    specification.

    @todo Define a base spec from the _type string in the Item (these should
    match)
    """

    if spec is None:
      raise RuntimeError("Base-class implementation requires an input Specification")

    # Iterate over the properties of the specification and set them to our
    # value if we have one, save having to maintain this later
    for p in spec.getDefinedPropertyNames():

      if not hasattr(self, p):
        continue

      v = getattr(self, p)
      # As a general rule, we 'silently ignore' None values.
      if v is not None:
        setattr(spec, p, v)

    return spec



  def toMetadata(self, type_=None, skip=None, force=None):
    """

    The base class method attempts to convert all properties of the object to
    metadata, it skips properties with no value (if not value and value is not
    False).

    @param type_ str, A custom type to store in the metadata - this can be used
    to make a derived class look like a parent class for broad compatibility.

    @param skip list, Allows certain known properties to be ignored.

    @exception ValueError If any of the properties holds a value not supported
    by the ManagerInterfaces metadata API.

    @see python.constants.kSupportedMetadataTypes
    @see python.Entity.Entity.setMetadata

    """

    meta = {}
    for prop in self.getDefinedPropertyNames():

      # Skip any that are internal data for the Item.
      if prop.startswith('_'):
        continue

      if prop == self._primaryProperty:
        continue

      if prop == kField_HintName:
        continue

      if skip and prop in skip:
        continue

      value = getattr(self, prop)
      if value is None:
        if not force or prop not in force:
          continue

      if type(value) not in kSupportedMetadataTypes:
        raise ValueError(("Property '%s' is not of a "+
          "supported type '%s' must be %s")
          % (prop, type(value), kSupportedMetadataTypes))

      meta[prop] = value

    if not type_:
      type_ = self._type

    meta[kField_ItemType] = type_

    return meta


  def toMime(self):
    raise NotImplementedError


  def toLocale(self):
    """

    As the python.Context.Context.locale is an important part of any
    interactions with the API - it is important that this is well configured.
    Items provide to this method to make it easier to define a well suited
    python.specifications.LocaleSpecification.

    Generally, you would derive from a suitable Item class within a Host
    implementation and implement this method to return something suitable based
    on the host-side object that the Item is bridging too.

    @return python.specifications.LocaleSpecfication or None

    """
    return None


  ## @}


  def readEntity(self, context, skip=None):
    """

    Reads the properties from the Entity set in the Item, updating the values
    of any applicable properties of the Item to match those stored in the
    Entity.

    @note This call will override the Context configuration to ensure that
    access is always Context.kRead and if this Item implements toLocale, then
    the Context.locale will also be updated for the duration of the call.

    @param skip str list [()] A list of metadata keys/property names that
    should be ignored when reading the entity.

    @exception RuntimeError if no Entity has been set in the Item.

    @see python.Context.Context
    @see toLocale

    """
    entity = self.getEntity()
    if not entity:
      raise RuntimeError("Unable to read properties, no Entity is set in the "+
          "object or supplied to the call")

    self._readEntity(entity, context, skip=skip)


  def _readEntity(self, entity, context, skip=None):
    """

    The base class method attempts to call setattr for any metadata keys that
    match properties on this object. The entity will be set into the Item at
    the end of read.

    @param skip list, the named of any metadata keys to ignore.

    """

    ## @todo Do we need a pre-fetch call in here?

    with context.scopedOverride():

      context.access = context.kRead

      # We allow an item to create its own locale, use it if does
      ## @todo Is it WISE to override the context?
      itemLocale = self.toLocale()
      if itemLocale:
        context.locale = itemLocale

      props = self.getDefinedPropertyNames()

      meta = entity.getMetadata(context)
      for k,v in meta.iteritems():

        if skip and k in skip:
          continue

        if k not in props:
          continue

        if type(v) not in kSupportedMetadataTypes:
          logging.warning(("Manager supplied metadata of an invalid type for key"
             +" '%s' (%s), skipping. Valid type sare %s.")
             % (k, type(v), kSupportedMetadataTypes))
          continue

        setattr(self, k, v)

      if self._primaryProperty:
        setattr(self, self._primaryProperty, entity.resolve(context))

    self.setEntity(entity)

  ##
  # @name Instantiation
  # Sneaky tricks thanks to the automatic registration of Item classes via. the
  # 'ref python.items.ItemFactory.ItemFactory
  ## @{

  @classmethod
  def fromEntity(cls, entity, context=None):
    """

    Can be used to instantiate an Item by introspection of an Entities
    metadata. The \ref python.contants.kField_ItemType is used to look up an
    available Entity class with matching _type string.

    @todo Decomposition of the type string in the error case to look for
    increasingly less derived Item classes.

    @exception RuntimeError If not suitable Item derived class could be found.

    @return Item

    """

    itemType = entity.getMetadataEntry(kField_ItemType)
    if not itemType:
      raise RuntimeError("Unable to determine the item type from the Entities"+
          +" metadata (field %s on %s)" % (kField_ItemType, entity))

    cls = cls.classMap.get(itemType, cls)

    item = cls()
    item.setEntity(entity, read=True, context=context)

    return item

  ## @}

