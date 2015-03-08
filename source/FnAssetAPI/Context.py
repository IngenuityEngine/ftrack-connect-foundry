from .specifications import LocaleSpecification
from .constants import kSupportedMetadataTypes
from .contextManagers import ScopedContextOverride


__all__ = ['Context']


class Context(object):
  """

  The Context object is used to convey information about the calling
  environment to a @ref Manager. It encapsulates several key access
  properties, as well as providing additional information about the @ref Host
  that may be useful to the @ref Manager to decorate or extend the metadata
  associated with the stored @ref Entity.

  A Manager will also use this information to ensure it presents the
  correct UI, or behaviour.

  The Context is passed to many calls in this API, and it may, or may not need
  to be used directly.

  """

  ##
  # @name Access Pattern
  # @{
  kRead = "read"
  kReadMultiple = "readMultiple"
  kWrite = "write"
  kWriteMultiple = "writeMultiple"
  kOther = "other"
  ## @}

  __validAccess = ( kRead, kReadMultiple, kWrite, kWriteMultiple, kOther )


  ##
  # @name Data Retention
  # @{

  ## Data will not be used
  kIgnored = 0
  ## Data will be re-used during a particular action
  kTransient = 1
  ## Data will be stored and re-used for the session
  kSession = 2
  ## Data will be permanently stored in the document
  kPermanent = 3

  kRetentionNames = [ "ignored", "transient", "session", "permanent" ]
  ## @}


  def __init__(self, access=kRead, retention=kTransient, locale=None,
      managerOptions=None, managerState=None, actionGroupDepth=0):

    super(Context, self).__init__()

    self.__access = access
    self.__retention = retention
    self.__locale = locale

    self.__managerOptions = managerOptions if managerOptions else {}
    self.__managerState = managerState

    self.__actionGroupDepth = actionGroupDepth


  def __getManagerInterfaceState(self):
    return self.__managerState

  def __setManagerInterfaceState(self, state):
    self.__managerState = state

  managerInterfaceState = property(__getManagerInterfaceState, __setManagerInterfaceState)


  def __getManagerOptions(self):
    """

    The manager options may contain custom locale data specific to your
    implementation. You should never attempt to set this your self, it will not
    be preserved in many situations by many hosts. Instead, the host will ask
    you for this information on occasions that it can be suitable propagated to
    other API calls. This will be generally be done using a @ref
    python.ui.widgets.ManagerOptionsWidget.

    """
    return self.__managerOptions

  def __setManagerOptions(self, options):

    if not isinstance(options, (dict, None)):
      raise ValueError("The managerOptions must be a dict (not %s)" % type(options))

    for key,value in options.items():
     if type(value) not in kSupportedMetadataTypes:
        raise ValueError(("Manager Options '%s' is not of a "+
          "supported type '%s' must be %s")
          % (key, type(value), kSupportedMetadataTypes))

    self.__managerOptions = options

  managerOptions = property(__getManagerOptions, __setManagerOptions)


  def __getActionGroupDepth(self):
    return self.__actionGroupDepth

  def __setActionGroupDepth(self, depth):
    self.__actionGroupDepth = depth

  actionGroupDepth = property(__getActionGroupDepth, __setActionGroupDepth)


  def __getAccess(self):
    """

    This covers what the @ref Host is intending to do with the data. For example,
    when passed to resolveEntityReference, it infers if the @ref Host is about
    to read or write. When configuring a BrowserWidget, then it will hint as to
    whether the Host is wanting to choose a new file name to save, or open an
    existing one.

    """
    return self.__access

  def __setAccess(self, access):
    if access not in self.__validAccess:
      raise ValueError, "'%s' is not a valid Access Pattern (%s)" \
          % (access, ", ".join(self.__validAccess))
    self.__access = access

  access = property(__getAccess, __setAccess)


  def __getRetention(self):
    """

    This is a concession to the fact that it's not always possible to fully
    implement the spec of this API. For example, @ref
    python.Manager.Manager.register "Manager.register()" can return an
    @ref entity_reference that points to the newly published @ref Entity.
    This is often not the same as the reference that was passed to the call.
    The Host is expected to store this new reference for future use. For
    example in the case of a Scene File added to an 'open recent' menu. A
    Manager may rely on this to ensure a reference that points to a specific
    version is used in the future.
    In some cases - such as batch rendering of an image sequence, it may not be
    possible to store this final reference, due to constraints of the
    distributed natured of such a render. Often, it is not actually of
    consequence.
    To allow the @ref Manager to handle these situations correctly, Hosts are
    required to set this property to reflect their ability to persist this
    information.

    """
    return self.__retention

  def __setRetention(self, retention):
    r = -1
    if isinstance(retention, basestring):
      if retention in self.kRetentionNames:
        r = self.kRetentionNames.index(retention)
    else :
      r = int(retention)
    if r < self.kIgnored or r > self.kPermanent:
      raise ValueError, "%i (%s) is not a valid Retention (%s)" \
          % (r, retention, ", ".join(range(self.kPermanent+1)))
    self.__retention = r

  retention = property(__getRetention, __setRetention)


  def __getLocale(self):
    """

    In many situations, the Specification of the desired @ref Entity itself is
    not entirely sufficient information to realize many functions that a @ref
    Manager wishes to implement. For example, when determining the final file
    path for an Image that is about to be published - knowing it came from a
    render catalog, rather than a 'Write node' from a comp tree could result in
    different behaviour.

    The Locale uses a @ref python.specifications.LocaleSpecification to
    describe in more detail, what specific part of a @ref Host is requesting an
    action. In the case of a file browser for example, it may also include
    information such as whether or not multi-selection is required.

    """
    return self.__locale

  def __setLocale(self, locale):
    if locale is not None and not isinstance(locale, LocaleSpecification):
      raise ValueError, "Locale must be an instance of %s (not %s)" \
        % (LocaleSpecification, type(locale))
    self.__locale = locale

  locale = property(__getLocale, __setLocale)


  def __str__(self):
    data = (
      ('access',  self.__access),
      ('retention', self.kRetentionNames[self.__retention]),
      ('locale', self.__locale),
      ('managerOptions', self.__managerOptions),
      ('managerState', self.__managerState),
      ('actionGroupDepth', self.__actionGroupDepth)
    )
    kwargs = ", ".join(["%s=%r" % (i[0],i[1]) for i in data])
    return "Context(%s)" % kwargs

  def __repr__(self):
    return str(self)


  def scopedOverride(self):
    """

    Returns a context manager that will revert any changes made to the
    Context made during its scope upon exit.

    This is provided as a convenience to avoid having to know/worry about where
    the implementation mechanism lives.

    Should be used in a 'with' statement, for example:

    @code
    # Make a write context
    context.access = kWrite

    # Temporarily set to read
    with context.scopedOverride():
      context.access = context.kRead
      ... do read-type things...

    # Access is now 'write' again
    ...
    @endcode

    @return python.contextManagers.ScopedContextOverride

    """

    return ScopedContextOverride(self)


  def isForRead(self):
    """

    @return bool, True if the context is any of the 'Read' based access
    patterns. If the access is unknown (context.kOther), then False is
    returned.

    """
    return self.__access in (self.kRead, self.kReadMultiple)


  def isForWrite(self):
    """

    @return bool, True if the context is any of the 'Write' based access
    patterns. If the access is unknown (context.kOther), then False is
    returned.

    """
    return self.__access in (self.kWrite, self.kWriteMultiple)


  def isForMultiple(self):
    """

    @return bool, True if the context is any of the 'Multiple' based access
    patterns. If the access is unknown (context.kOther), then False is
    returned.

    """
    return self.__access in (self.kReadMultiple, self.kWriteMultiple)




