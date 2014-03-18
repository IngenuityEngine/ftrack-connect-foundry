from .core.decorators import debugApiCall
from .audit import auditApiCall
from .import constants


__all__ = ['Entity']


class Entity(object):
  """

  The Entity is a @ref Host facing convenience class that holds an @ref
  entity_reference and a @ref Manager instance. It wraps the @ref
  ManagerInterfaceBase to make integration of the asset API into a host much more
  straight forward.

  Once created, the Entity becomes a self-contained representative for the
  asset in the @ref asset_management_system.

  @note In all cases, either the @ref Entity or @ref Manager
  should be used in implementation code. The @ref ManagerInterfaceBase should
  never be used directly.

  Most functions simply wrap the ManagerInterfaceBase, so see the docs there for
  more on their behaviour.

  @see python.implementation.ManagerInterfaceBase

  """

  def __init__(self, reference, manager):

    if isinstance(manager, str):
      ## If we have a current session, use this to try and get the required
      ## manager @todo This needs cleaning up I think.
      from SessionManager import SessionManager
      session = SessionManager.currentSession()
      if session:
        manager = session._factory.instantiate(manager)
      else:
        manager = None

    if not manager:
      raise RuntimeError("Entity constructed with no Manager, or invalid "+
          "identifier")

    self.__reference = reference
    self.__manager = manager
    self.__interface = manager._getInterface()

    # This can be set to false, to disable API debugging at the per-class level
    self._debugCalls = True


  def __eq__(self, other):
    if self.reference != other.reference: return False
    if self.manager != other.manager: return False
    return True


  @auditApiCall("Entity methods")
  def __str__(self):
    return self.reference


  def __repr__(self):
    managerId = self.__interface.getIdentifier() if self.__interface else None
    return "Entity(%r, %r)" % (self.reference, managerId)


  ## @name Properties
  ## These are read-only for entities
  ## @{

  def __getReference(self):
    """

    @return str, the ASCII @ref entity_reference that locates the Entity.

    """
    return self.__reference

  reference = property(__getReference)


  def __getManager(self):
    """

    @return object, The @ref Manager that maintains the Entity.

    """
    return self.__manager

  manager = property(__getManager)

  ## @}

  ##
  # @name Entity Resolution
  #
  # The concept of resolution is turning an @ref Entity into a 'finalized' or
  # 'primary' string. This, ultimately, is anything meaningful to the
  # situation. It could be a colour space, a directory, a script or image
  # sequence. A rule of thumb is that a resolved @ref Entity should be the
  # string the Host would have had anyway, in a unmanaged environment. For some
  # kind of Entity - such as a 'Shot', for example, there may not be a
  # meaningful string, though often some sensible return can be made. In these
  # cases its generally unlikely that you would be resolving the Entity in the
  # first place.
  #
  # @{

  @debugApiCall
  @auditApiCall("Entity methods")
  def resolve(self, context):
    """

    Returns the primary string held by the Entity. In general, any
    substitutions tokens - such as frame numbers, views, etc... remain intact
    and need handling as if the Asset API was never there..

    The API defines that all file paths passed though the API that represent
    file sequences should use the 'format' syntax, compatible with sprintf,
    etc... (eg.  %04d").

    @return str, The UTF-8 ASCII compatible string that that is represented by
    the Entity.

    @exception python.exceptions.InvalidEntityReference If the @ref Entity is
    not known by the associated \ref Manager.
    @exception python.exceptions.EntityResolutionError If the @ref Entity does
    not have a meaningful string representation, or if it is a valid Entity but
    it does not logically exist in a way required to resolve.
    @exception python.exceptions.InvalidEntityReference if the \ref Entity
    should not be resolved for that context, for example, if the context access
    is kWrite and the entity is an existing version - the exception means that
    it is not a valid action to perform on the entity.

    """
    return self.__manager.resolveEntityReference(self.__reference, context)

  ## @}

  ##
  # @name Entity information
  #
  # There are several common requests for basic, generic information about
  # an Entity that is assumed to be valid for all entity types.
  #
  # @see @ref metadata
  #
  # @{

  @debugApiCall
  @auditApiCall("Entity methods")
  def exists(self, context):
    """

    Can be called to determine if the Entity exists in the @ref
    asset_management_system, and that it can be resolved into a meaningful
    string. Managers may return perfectly valid \ref entity_references or
    Entities that don't exist *yet* (maybe a new version, for example). By
    'Exist' we mean 'is ready to be read'.

    In the future, this may need to be extended to cover a more complex
    definition of 'existence' (for example, known to the system, but not yet
    finalized). For now however, it should be assumed to simply mean, 'ready to
    be consumed', and if only a placeholder or un-finalized asset is available,
    False should be returned.

    It's important to properly configure the supplied context as the access
    pattern and locale may well disambiguating this subtle definition of
    'exists' in some cases too, as it better explains the intent.

    @return bool, True if it points to an existing entity, False if the Entity
    is not known or ready yet.

    @exception python.exceptions.InvalidEntityReference If the Entity does not
    hold a valid entity reference.

    """
    return self.__interface.entityExists(self.__reference, context)


  @debugApiCall
  @auditApiCall("Entity methods")
  def getName(self, context=None):
    """

    Returns the name of the Entity itself, not including any hierarchy or
    classification.

    For example:

     @li `"1"` - for a version of an asset
     @li `"seq003"` - for a sequence in a hierarchy

    @return str, A UTF-8 ASCII string with the Entity's name

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager

    @see getDisplayName

    """
    return self.__interface.getEntityName(self.__reference, context)


  @debugApiCall
  @auditApiCall("Entity methods")
  def getDisplayName(self, context=None):
    """

    Returns an unambiguous, humanised display name for the Entity that can
    uniquely identify the entity in that context.

    @note It's important to properly configure the Context - some Managers may
    give you much more meaningful and readable strings if they know the locale
    that you are wanting to use the result in.

    For example:

     @li `"dive / build / cuttlefish / model / v1"` - for a version of an
     asset in an 'open recent' menu.
     @li `"Sequence 003 [ Dive / Episode 1 ]"` - for a sequence in
     an hierarchy as a window title.

    @return str, a UTF-8 ASCII string

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager

    @see getName

    """
    return self.__interface.getEntityDisplayName(self.__reference, context)


  @debugApiCall
  @auditApiCall("Entity methods")
  def getMetadata(self, context):
    """

    Retrieve @ref metadata for the Entity.

    @warning See @ref setMetadata for important notes on metadata and its
    role in the system.

    @return dict, with the entities meta-data. Values will be P.O.D types, keys
    will be UTF-8 ASCII strings.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @see getMetadataEntry
    @see setMetadata
    @see setMetadataEntry

    """
    return self.__interface.getEntityMetadata(self.__reference, context)


  @debugApiCall
  @auditApiCall("Entity methods")
  def getMetadataEntry(self, key, context, throw=False, defaultValue=None):
    """

    Returns the value for the specified metadata key.

    @param key str, The key to look up

    @param throw bool [False] if True, the method will call a KeyError if the
    requested key does not exists. Otherwise, the defaultValue will be
    returned.

    @param defaultValue p.o.d If not None, this value will be returned in the
    case of the specified key not being set for the entity.

    @return p.o.d, The value for the specific key.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @exception KeyError If no defaultValue is supplied, and the Entity has no
    metadata for the specified key.

    @see setMetadataEntry
    @see getMetadata
    @see setMetadata

    """
    try:
      return self.__interface.getEntityMetadataEntry(self.__reference, key, context)
    except KeyError, e:
      if throw:
        raise e
      else:
        return defaultValue


  @debugApiCall
  @auditApiCall("Entity methods")
  def setMetadata(self, data, context, merge=True):
    """

    Sets an Entities metadata.

    @param data dict, A dictionaty of metadata - string key types, p.o.d value
    types.

    @param merge bool, If true, then the Entity's existing metadata will be
    merged with the new data (the new data taking precedence). If false,
    its metadata will entirely replaced by the new data.

    @note Mangers guarantee to faithfully round-trip any data stored in an
    Entities Metadata. They may elect to internally bridge this into other
    first-class concepts within their domain, but they  must present the same
    dictionary back when queried (unless it has been meaningfully modified in
    the mean time).

    If any value is 'None' it instructs that that key should be un-set on the
    Entity.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @exception ValueError if any of the metadata values are of an un-storable
    type. Presently it is only required to store str, float, int, bool

    @exception KeyError if any of the metadata keys are non-strings.

    @see getMetadata
    @see getMetadataEntry
    @see setMetadataEntry

    """
    return self.__interface.setEntityMetadata(self.__reference, data,
        context, merge)


  @debugApiCall
  @auditApiCall("Entity methods")
  def setMetadataEntry(self, key, value, context):
    """

    Stores a single metadata value under the supplied key.

    @param value p.o.d, the Value must be a bool, float, int or str

    @see getMetadataEntry
    @see getMetadata
    @see setMetadata

    """
    return self.__interface.setEntityMetadataEntry(self.__reference, key, value, context)

  ## @}

  ##
  # @name Versioning
  #
  # Most Managers allow multiple revisions of certain entities to be tracked
  # simultaneously. This API exposes this as a generalised concept, in order to
  # avoid Exceptions, you should take care to only query versioning where it's
  # meaningful to the type of Entity.
  #
  # @{

  @debugApiCall
  @auditApiCall("Entity methods")
  def getVersionName(self, context=None):
    """

    Retrieves the name of the version pointed to by the supplied Entity

    @return str, A UTF-8 ASCII string representing the version or an empty
    string if the entity was not versioned.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @see getVersions()
    @see getFinalizedVersion()

    """
    return self.__interface.getEntityVersionName(self.__reference, context)


  @debugApiCall
  @auditApiCall("Entity methods")
  def getVersions(self, context, includeMetaVersions=False, maxResults=-1,
      asRefs=False, asList=False):
    """

    Retrieves all available versions of the Entity (including this Entity, if
    it points to a specific version).

    @param includeMetaVersions bool, if true, @ref meta_versions such as
    'latest', etc... should be included, otherwise, only concrete versions
    will be retrieved.

    @param maxResults int, Limits the number of results collected, if more
    results are available than the limit, then the newest versions will be
    returned. If a value of -1 is used, then all results will be returned.

    @return dict, Where the keys are ASCII string versions, and the values are
    Entities. Additionally the python.constants.kVersionDict_OrderKey may be
    set to a list of the version names (ie: dict keys) in their natural
    ascending order, that may be used by UI elements, etc...

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @param asRefs bool [False] If True, then return will contain
    \ref entity_reference "Entity References" rather than \ref Entity
    instances.

    @param asList bool [False] If True, then the return will be a list, rather
    than the standard dictionary.

    @see getVersionName()
    @see getFinalizedVersion()

    """

    versions = self.__interface.getEntityVersions(self.__reference, context,
        includeMetaVersions, maxResults)

    if not asRefs:
      versions = dict( (v, Entity(r, self.__manager)) for (v, r) in versions.items() )

    if not asList:
      return versions

    hint = versions.get(constants.kVersionDict_OrderKey, None)
    if hint:
      return [ versions[v] for v in hint ]
    else:
      return [ versions[v] for v in sorted(versions.keys()) ]


  @debugApiCall
  @auditApiCall("Entity methods")
  def getFinalizedVersion(self, context, overrideVersionName=None, asRef=False):
    """

    Retrieves a @ref entity_reference that points to the concrete version
    of a @ref meta-version @ref entity_reference.

    If the supplied entity reference is not versioned, or already has a
    concrete version, the input reference is passed-through.

    If versioning is unsupported for the given @ref entity_reference, then the
    input reference is returned.

    @param overrideVersionName str If supplied, then the call should return the
    Entity for the version of the referenced asset that matches the
    name specified here, ignoring any version inferred by this Entity.

    @param asRef bool [False] if True, the return will be an \ref
    entity_reference instead of a \ref Entity.

    @return python.Entity.Entity or None

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @exception python.exceptions.EntityResolutionError should be thrown if the
    Entity is ambiguously versioned (for example if the version is
    missing as it points to the parent 'asset', and that behaviour is
    undefined in the Manager's model. It may be that it makes sense in
    the specific Manager to fall back on 'latest' in this case...)

    @exception python.exception.EntityResolutionError if the supplied
    overrideVersionName does not exist for the Entity.

    @see getVersionName()
    @see getVersions()

    """
    ref = self.__interface.getFinalizedEntityVersion(self.__reference,
        context, overrideVersionName)
    if asRef:
      return ref
    else:
      return Entity(ref, self.__manager) if ref else None

  ## @}


  ##
  # @name Related Entities
  #
  # A 'related' Entity could take many forms. For example:
  #
  #  @li In 3D CGI, Multiple @ref aovs may be related to a 'beauty' render.
  #  @li In Compositing, an image sequence may be related to the script
  #  that created it.
  #  @li An asset may be related to a task that specifies work to be done.
  #  @li Parent/child relationships are also (semantically) covered by
  #  these relationships.
  #
  # In the this API, these relationships are represented by a generic
  # Specification, this may just be a 'type', but can additionally have
  # arbitrary attributes to further define the relationship. For example in
  # the case of @ref aovs, the type might be 'alternate output' and the
  # attributes may be that the 'channel' is 'diffuse'.
  #
  # Related references form a vital part in the abstraction of the internal
  # structure of the asset management system from the Host application in its
  # attempts to provide the user with meaningful functionality. A good example
  # of this is in an editorial example, where it may need to query whether a
  # 'shot' exists in a certain part of the asset system. One approach would be
  # to use a 'getChildren' call, on this part of the system. This has the
  # drawback that is assumes that shots are always something that can be
  # described as 'immediate children' of the location in question. This lay not
  # always be the case (say, for example there is some kind of 'task' structure
  # in place too). Instead we use a request that asks for any 'shots' that
  # relate to the chosen location. It is then up to the implementation of the
  # ManagerInterfaceBase to determine how that maps to its own data model.
  # Hopefully this allows Hosts of this API to work with a broader range of
  # asset managements, without providing any requirements of their structure or
  # data model.
  #
  # @{

  @debugApiCall
  @auditApiCall("Entity methods")
  def getRelatedEntities(self, relationshipSpecOrSpecs, context, asRefs=False,
      resultSpec=None):
    """

    Returns related Entites, based on a relationship specification.

    This is an essential function in this API - as it is widely used to query
    organisational hierarchy, and other interesting relationships.

    There are two possible conventions for calling this function, to allow
    for batch optimisations in the implementation and prevent excessive query
    times with high-latency services.

      a) A single specification.
      b) A list of specifications.

    In both cases, the return value is a list of lists, for example:

    a)  getRelatedEntites( spec )

    > [ [ matches, ... ] ]

    b)  getRelatedEntites( [ s1, s2, s3 ] )

    > [ [ s1-matches, ... ], [ s2-matches, ... ], [ s3-matches, ... ] ]

    @note The order of entities in the inner lists of matching results should
    not be considered meaningful, but the outer list will match the input
    order.

    If any specification is not understood by the Manager, then an empty list
    will be returned for that Specificaion, and no errors should be raised.

    @param relationshipSpecOrSpecs python.specification.Specification This can
    either be a standard EntitySpecification, which will mean 'find me Entities
    that match this spec in relation to me'. Or, if a RelationshipSpecification
    is supplied, then more complex queries can be made.

    @param asRefs bool [False] if True, then the return list of lists will
    contain \ref entity_reference instead of Entity instances.

    @param resultSpec python.specifications.EntitySpecification or None, a hint
    as to what kind of entity your are expecting to be returned. May be
    None.

    @return list of Entity lists, The return is always a list of lists,
    regardless of how many specs are passed in.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @see python.specifications
    @see setRelatedReferences()

    """
    entities = self.__manager.getRelatedEntities( [self.__reference,],
        relationshipSpecOrSpecs, context, resultSpec=resultSpec, asRefs=asRefs)
    return entities


  @debugApiCall
  @auditApiCall("Entity methods")
  def setRelatedEntities(self, relationshipSpec, entities, context, append=True):
    """

    Creates a new relationship between this Entities and the other supplied
    Entities.

    @param append bool, When True (default) new relationships will be added to
    any existing ones. If False, then any existing relationships with the
    supplied specification will first be removed.

    Though a Manager is required to support getRelatedEntities, there is some
    asymetry here, as it is not required to be able to setRelatedReferences
    directly. For example, in the case of a 'shot' (as illustrated in the docs
    for getRelatedEntites) - any new shots would be created by registering a
    new @ref python.specifications.ShotSpecification under the parent, rather
    than using this call. The best way to think of it is that this call is
    reserved for defining relationships between existing assets (Such as
    connecting multiple image sequences published under the same shot, as being
    part of the same render.) and 'register' as being defining the relationship
    between a new asset and some existing one.

    In systems that don't support post-creation adjustment of relationships,
    this may simply be a no-op.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @return None

    @see @ref getRelatedEntities()
    @see @ref register()

    """
    references = [e.reference for e in entities]
    return self.__interface.setRelatedReferences( self.__reference,
        relationshipSpec, references, context, append)

  ## @}

  ##
  # @name Publishing
  #
  #
  # Certain Managers may have high latencies due to cloud hosting, or some such
  # other fun and games. In order to attempt to improve performance in these
  # situations, the API provides 'batch' alternatives to some of the well-used
  # calls. These are suffixed 'multiple'. One point to consider here is that
  # because Contexts can't be copied there is a slightly reduced scoped for
  # informing the Manager of the locale/etc... as a single context must be used
  # for all grouped actions.
  #
  # @{

  @debugApiCall
  @auditApiCall("Entity methods")
  def preflight(self, spec, context):
    """

    @note This call is only applicable when the Manager you are communicating with
    sets the @ref python.constants.kWillManagePath bit in response to a @ref
    python.Manager.Manager.managementPolicy for the Specification of Entity you
    are intending to publish.

    It signals your intent as a Host application to do some work to create a
    file in relation to this Entity. This Entity does not need to exist yet
    (see @ref entity_reference) or it may be a parent Entity that you are about
    to create a child of or some other similar relationship (it actually
    doesn't matter really, as this Entity will ultimately have been determined
    by interaction with the Manager, and it will have returned you something
    meaningful).

    It should be called before register() if you are about to create media or
    write to files. If the file or data already exists, then preflight is not
    needed. It will return a working Entity that can be resolved/etc... in
    order to determine a working path that the files should be written to.

    This call is designed to allow sanity checking, placeholder creation or any
    other sundry preparatory actions to be carried out by the Manager. In the
    case of file-based Entites, the Manage may even use this opportunity to
    switch to some temporary working path or some such.

    \note Its vital that the \ref Context is well configured here, in
    particular the 'ref python.Context.Context.retention "Context.retention".
    See @ref examples_save, but the importance of using the working Entity,
    rather than the initial Entity is essential to proper behaviour.

    @return python.Entity.Entity or None, A working @ref Entity, that the you
    should resolve to determine the path to write media too. This may or may
    not be the same as the input reference. It should be resolved to get a
    working file path before writing any files.

    @exception python.exceptions.InvalidEntityReference If the Entity is not
    recognised by the Manager.

    @exception python.exceptions.PreflightError if some fatal exception happens
    during preflight, this Exception indicates the process should be aborted.

    @exception python.exceptions.RetryableError If any non-fatal error occurs
    that means the call can be re-tried.

    @see preflightMultiple
    @see register
    @see registerMultiple

    """
    entityRef = self.__manager.preflight(self.__reference, spec, context)
    return Entity(entityRef, self.__manager) if entityRef else None


  @debugApiCall
  @auditApiCall("Entity methods")
  def preflightMultiple(self, specs, context):
    """

    A batch version of preflight, taking an array of specs, instead of a single
    Specification, and returning an array of Entities.

    @note It is advisable to only call this if the Manager has set the
    kSupportsBatchOperations bit in the managementPolicy bitfield for the
    applicable EntitySpecification.

    """
    targetRefs = [ self.__reference for s in specs ]
    entityRefs = self.__manager.preflightMultiple(targetRefs, specs, context)
    return [ Entity(e, self.__manager) if e else None for e in entityRefs ]


  @debugApiCall
  @auditApiCall("Entity methods")
  def register(self, stringData, spec, context, metadata=None):
    """

    Register should be used to register a new Entity either when originating new
    data within the application process, or referencing some existing file,
    media or information.

    @note The registration call is applicable to all kinds of Manager, as long
    as the @ref python.constants.kIgnored bit is not set in response to a @ref
    python.Manager.Manager.managementPolicy for the Specification of Entity you
    are intending to publish. In this case, the Manager is saying it doesn't
    handle that Specification of Entity, and it should not be registered.

    As the Entity has (ultimately) come from the Manager (either in response to
    delegation of UI/etc... or as a return from another call), then it can be
    assumed that the Manager will understand what it means for you to call
    'register' on this Entity with the supplied Specification. The conceptual
    meaning of the call is:

    "I have this Entity (self in this case), and I would like to register a new
    Entity to it with this Specification, to hold the supplied stringData. I
    trust that this is ok, and you will give me back the Entity that represents
    the result of this."

    It is up to the manager to understand the correct result for the particular
    Specification in relation to this Entity. For example, if you received this
    Entity in response to browsing for a target to 'kWriteMultiple'
    ShotSpecifications, then the Manager should have returned you an Entity that
    you can then call register() on multiple times with a ShotSpecification
    without error. Each resulting Entity should then reference the newly created
    Shot.

    @warning When registering files, it should never be assumed that the
    resulting Entity will resolve to the same path. Managers may freely
    relocate, copy move or rename files as part of registration.

    @param stringData str, The @ref primary_string for this Entity. It is the
    string the resulting Entity will resolve to. In the case of file-based
    Entites, this is the file path, and may be further modified by Managers
    that take care of relocating or managing the storage of files. The API
    defines that in the case of paths representing file sequences, frame tokens
    should be left un-subsituted, in a sprintf compatible format, eg. "%04d",
    rather than say, the #### based method. If your application uses hashes, or
    some other scheme, it should be converted to/from the sprintf format as
    part of your integration.

    @param spec python.specifications.Specfication the EntitySpecification for
    the new registration.

    @see python.specifications
    @see registerMultiple
    @see preflight
    @see preflightMultiple

    """
    entityRef = self.__manager.register(stringData, self.__reference, spec,
        context, metadata=metadata)
    return Entity(entityRef, self.__manager) if entityRef else None


  @debugApiCall
  @auditApiCall("Entity methods")
  def registerMultiple(self, strings, specs, context):
    """

    A batch version of register - taking equal length arrays of strings and
    specs, returning a list of Entities

    @note It is advisable to only call this if the Manager has set the
    kSupportsBatchOperations bit in the managementPolicy bitfield for the
    applicable EntitySpecification.

    """
    targetRefs = [ self.__reference for s in strings ]
    entityRefs = self.__manager.registerMultiple(strings, targetRefs, specs, context)
    return [ Entity(e, self.__manager) if e else None for e in entityRefs ]


  @debugApiCall
  @auditApiCall("Entity methods")
  def preflightItem(self, item, context):
    """

    An alternate form of preflight that takes an Item derived class and takes
    advantage of its toSpecfication() methods to make the standard preflight
    call.

    Return type and exceptions as per \ref preflight.

    @see preflight
    @see registerItem

    """
    entityRef = self.__manager.preflight(self.__reference, item.toSpecification(), context)
    return Entity(entityRef, self.__manager) if entityRef else None


  @debugApiCall
  @auditApiCall("Entity methods")
  def registerItem(self, item, context):
    """

    An alternate form of register that takes an Item derived class and takes
    advantage of its getString() and toSpecfication() methods to make the
    standard preflight call.

    Return type and exceptions as per \ref register.

    @see register
    @see preflightItem

    """
    # Manager implements the metadata extended signature that takes care of
    # calling setMetadata.
    entityRef = self.__manager.register(item.getString(), self.__reference,
        item.toSpecification(), context, item.toMetadata())
    return Entity(entityRef, self.__manager) if entityRef else None

  ## @}

