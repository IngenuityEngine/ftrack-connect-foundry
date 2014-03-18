from . import logging
from . import constants

from .core.decorators import debugApiCall

from .Events import Events
from .Host import Host
from .ManagerFactory import ManagerFactory
from .Context import Context
from .contextManagers import ScopedActionGroup
from .exceptions import ManagerError, InvalidEntityReference

from .audit import auditApiCall


__all__ = ['Session']


class Session(object):
  """

  The Session is a Host-side controller object that manages interactions with a
  Manager. A Session should be constructed and persisted for each individual
  Manager you wish to communicate with. It simplifies and manages many common
  tasks that you may wish to perform as a host. For example:

    @li Initialising and configuring an instance of a Manager
    @li Creating and managing the lifetime of a Context
    @li Localising strings before presentation to the User
    @li Transaction management.

  As a general rule, a Session should be used in preference for these tasks
  rather than interacting with a Manager directly - as it removed much of the
  complexity/boilerplate and ensures things are done in a consistent fashion.

  The session also provides streamlined access to Entities or their Primary
  String reducing some of the code needed for simple cases.

  The Session class is suitable for all Hosts, but in cases where a UI is
  presented to the user, it may be desireable to use the UISession instead, as
  it permits access to a Managers widgets etc...

  @see python.SessionManager
  @see python.ui.UISessionManager
  @see python.ui.UISession

  """

  # This dict holds the default terminology for a session
  __terminology = {
    constants.kLocalizationKey_Asset : 'Asset',
    constants.kLocalizationKey_Assets: 'Assets',
    constants.kLocalizationKey_Shot : 'Shot',
    constants.kLocalizationKey_Shots : 'Shots',
    constants.kLocalizationKey_Publish : 'Publish',
    constants.kLocalizationKey_Publishing : 'Publishing',
    constants.kLocalizationKey_Published : 'Published',
    constants.kLocalizationKey_Manager : 'Asset Manager'
  }

  def __init__(self, host, makeLogHost=True):
    """

    When the Session is initialized a couple of things happen.

      @li Logging is connected to the supplied Host (if applicable)
      @li A PluginManager is initialized and scans for Manager plugins

    @param host python.Host The current Host instance (note: only a single
    currently active Host is supported, so if multiple sessions are created,
    they should all use the same Host instance).

    @param makeLogHost bool [True] When True, the supplied Host will be
    connected to the logging mechanism in the API. This is actually an API-wide
    change (ie: for any single interpreter, there is only one active logging
    target). This may not be ideal in the long term (if we want to support
    multiple hosts, but it seems like this is a far while away yet if ever).
    This is done by checking to see if the Host implements 'log'.

      @see useManager()
      @see currentManager()
      @see python.SessionManager.SessionManager.currentSession()

    """
    super(Session, self).__init__()

    if not isinstance(host, Host):
      raise ValueError, ("The supplied host must be a Host or derived "+\
          "class (%s)") % type(host)

    self._host = host

    # Presently, we require that there be a single host for any import of the
    # API module, so this doesn't cause us any issues. There is probably
    # something fundamentally flawed there though if/when we want to relax that.
    # We should probably make it so that it is tied to the manager when its
    # initialized, rather than having a global singleton for logging. The
    # session could take care of this when it initializes the manager. We'd
    # need to discourage/move away from any direct use of
    # FnAssetAPI.logging.log though. Maybe cross that bridge when it comes to
    # it, as it should be an easy replace in any implementation, and possible
    # to make it backwards compatible for a release if we ever get to the point
    # where it actually becomes an issue.
    if makeLogHost:
      if hasattr(host, 'log'):
        logging.logHost = host
      else:
        logging.log("The host %s has no 'log' method, skipping logging "+\
            "connection", logging.kDebug)

    self._managerId = None
    self._managerSettings = None

    self._manager = None

    self._factory = ManagerFactory()
    self._factory.scan()


  @auditApiCall("Session")
  def getHost(self):
    """

    @return Host, the Host that the session was started by.

    """
    return self._host


  @debugApiCall
  @auditApiCall("Session")
  def getRegisteredManagers(self):
    """

    @see python.ManagerFactory.managers()

    """
    return self._factory.managers()


  @auditApiCall("Session")
  def useManager(self, identifier, settings=None):
    """

    Configures the session to use the @ref Manager with the specified
    identifier. The managerChanged Event is trigged if the resulting Manager is
    different to the previous one.

    @param identifier str The Identifier for the desired manager, available
    from @ref getRegisteredManagers.

    @param settings dict [None], Any settings to pass to the managed before calling
    initialize. This will be shallow-copied and retained in order to support
    deferred initialization of the Manager.

    @note The Manager not instantiated until @ref currentManager() is actually
    called. If the suppled identifier matches the current manager, then the
    call is ignored.

    """

    if identifier and not self._factory.managerRegistered(identifier):
      raise ManagerError, "Unknown Manager '%s'" % identifier

    # No need to do anything if its the same
    if identifier == self._managerId:
      return

    oldId = self._managerId if self._managerId else ''
    newId = identifier if identifier else ''

    self._managerId = identifier
    self._managerSettings = dict(settings) if settings else None
    self._manager = None

    # Make sure we emit the event indicating the manager has changed
    eventManager = Events.getEventManager()
    eventManager.managerChanged(self, oldId, newId)

    # Ensure we have the right terminology
    self._localize()


  def currentManager(self):
    """

    @return Manager, an instance of the Manager that has been set for this
    session using @ref useManager(). This will be lazily constructed the first
    time this function is called, then retained.

    """
    if not self._managerId:
      return None

    # Cache this internally to avoid double initializations
    if not self._manager:
      self._manager = self._factory.instantiate(self._managerId)
      if self._managerSettings:
        self._manager.setSettings(self._managerSettings)
      self._manager.initialize()

    return self._manager


  @debugApiCall
  @auditApiCall("Session")
  def getEntity(self, entityReference, context=None, mustBeValid=False,
      mustExist=False, throw=False):
    """

    A convenience function to return an @ref Entity from the current manager.
    By default, for performance reasons, no checks are made to ensure the
    validity of the resulting entity. It simply constructs an Entity that wraps
    the reference and Manager instance. If sanity-checking is required the
    optional kwargs can be used to increase the robustness of this call.

    @param entityReference str The @ref entity_reference of the Entity to
    retrieve.

    @param context python.Context.Context [None] The context of the retrieval
    request, if None, once will be created with the default access of kRead and
    retention of kTransient.

    @param mustBeValid bool [False] If True, and the @ref entity_reference is
    not of a format recognised by the Session's current Manager None is
    returned instead of what is effectively an 'invalid' Entity.

    @param mustExist bool [False] If True, and the @ref entity_reference points
    to an Entity that does not exist, None will be returned instead of an
    Entity that points to the non-existent asset.

    @param throw bool [False] When True, the above two parameters will cause an
    exception to be raised, rather than None to be returned.

    @return Entity or None

    @exception InvalidEntityReference Thrown if mustBeValid is True, and the
    specified entityReference does not pass @ref
    python.Manager.isEntityReference.

    @exception InvalidEntityReference Thrown if mustExists is True, and the
    specified entityReference does not exists as per @ref
    python.Manager.entityExists

    """
    if not self.currentManager():
      return None

    if not context:
      context = self.createContext()

    if not self.currentManager().isEntityReference(entityReference, context):
      if (mustBeValid or mustExist) and throw:
        raise InvalidEntityReference, ("The supplied token is not an entity "+\
          "reference (%s)") % entityReference
      else:
        return None

    if mustExist and not self._manager.entityExists(entityReference, context):
      if throw:
        raise InvalidEntityReference, "The specified entity doesn't exist (%s)"\
          % entityReference
      else:
        return None

    return self._manager.getEntity(entityReference, context, throw=False)



  @auditApiCall("Session")
  def resolveIfReference(self, stringOrReference, context):
    """

    A convenience function to retrieve the @ref primiary_string for an Entity.
    It @ref resolves the supplied string if it is an @ref entity_reference,
    else returns the string unchanged. If more flexibility or sanity-checking
    is needed, this process can be done manually.

    If there is no Manager currently set for the Session, then the Input string
    will be returned.

    @param stringOrReference str A (UTF-8 encoded) ASCII string, that may hold
    an @ref entity_reference. If the current Manager returns True to @ref
    python.Manager.Manager.isEntityReference "isEntityReference" then the
    string will be resolved.

    @return str

    """

    manager = self.currentManager()

    if not manager:
      return stringOrReference

    if manager.isEntityReference(stringOrReference, context):
      return manager.resolveEntityReference(stringOrReference, context)

    return stringOrReference



  @auditApiCall("Session")
  def createContext(self, parent=None):
    """

    A convenience to create a new @ref Context, for the current @ref Manager.

    @param parent FnAssetAPI.Context If supplied, the new context will clone
    the supplied Context, and the Manager will be given a chance to migrate any
    meaningful state etc... This can be useful when certain UI elements
    need to 'take a copy' of a context in its current state. It is not linked
    to the parent's transaction if one has been created in the parent. The
    lifetime of any context's transactions are only ever controlled by the
    context that created them.

    """
    c = Context()

    # If we have a parent, copy its setup
    if parent:
      c.access = parent.access
      c.retention = parent.retention
      c.locale = parent.locale
      c.managerOptions = parent.managerOptions

    if self.currentManager():
      parentState = None
      if parent:
        parentState = parent.managerInterfaceState
      state = self.currentManager()._getInterface().createState(parentState)
      c.managerInterfaceState = state
    c.actionGroupDepth = 0

    return c

  ## @name Action Group Management
  ## @ref action_group Management.
  ## Manages an action group stack within the Context, which in turn takes care
  ## of correctly calling the ManagerInterface's transactional API.
  ## @{

  @debugApiCall
  @auditApiCall("Session")
  def scopedActionGroup(self, context):
    """

    @return A python context manager that pushes an action group on creation,
    and pops it when the scope is exit. Use with a 'with' statement, to
    simplify implementing action groups in a host. for example:

    @code
    with session.scopedActionGroup(context):
      for t in textures:
        publish(t)
    @endcode

    """
    return ScopedActionGroup(self, context)


  @debugApiCall
  @auditApiCall("Session")
  def pushActionGroup(self, context):
    """

    Push an ActionGroup onto the supplied Context. This will increase the depth
    by 1, and a @ref transaction started if necessary.

    @return int The new depth of the Action Group stack

    """
    if context.actionGroupDepth == 0:
      interface = self.currentManager()._getInterface()
      interface.startTransaction(context.managerInterfaceState)

    context.actionGroupDepth += 1
    return context.actionGroupDepth


  @debugApiCall
  @auditApiCall("Session")
  def popActionGroup(self, context):
    """

    Pops an ActionGroup from the supplied Context. This will decrease the depth
    by 1 and the current @ref transaction will be finished if necessary.

    @return int The new depth of the Action Group stack

    @exception RuntimeError If pop is called before push (ie: the stack depth
    is 0)

    """
    if context.actionGroupDepth == 0:
      raise RuntimeError("Action group popped with none on the stack")

    context.actionGroupDepth -= 1
    if context.actionGroupDepth == 0:
      interface = self.currentManager()._getInterface()
      interface.finishTransaction(context.managerInterfaceState)

    return context.actionGroupDepth


  @debugApiCall
  @auditApiCall("Session")
  def cancelActions(self, context):
    """

    Clears the current ActionGroup stack (if one has been started), cancelling
    the @ref transaction if one has been started.

    @return bool True if the current cancelled successfully and any actions
    performed since it began have been undone, or if there was nothing to
    cancel. Otherwise False - which indicates the Manager may not have been
    able to undo-unwind any actions that occurred since the first ActionGroup
    was pushed onto the stack.

    """
    status = True

    if context.actionGroupDepth == 0:
      return status

    interface = self.currentManager()._getInterface()
    status = interface.cancelTransaction(context.managerInterfaceState)

    context.actionGroupDepth = 0

    return status


  def actionGroupDepth(self, context):
    """

    @return int The current ActionGroup depth in the context.

    """
    return context.actionGroupDepth

  ## @}

  @auditApiCall("Session")
  def freezeManagerState(self, context):
    """

    Returns a serialized representation of the @ref manager_state held in the
    supplied Context, so that it can be distributed to other processes/etc...

    @warning From this point, the context should not be used further
    without first thawing the state back into the context.

    @return str an ASCII compatible string

    @see thawManagerState

    """
    ## @todo Ensure that other actions error after this point
    token = self.__managerInterface.freezeState(context.managerInterfaceState)
    return "%i_%s" % (context.actionGroupDepth, token)


  @auditApiCall("Session")
  def thawManagerState(self, token, context):
    """

    Restores the @ref manager_state in the supplied Context so that it
    represents the context as previously frozen.

    @param token str The string returned by @ref freezeManagerState

    @param context Context The context to restore the state into.

    @note It is perfectly legal to thaw the same context multiple times in
    parallel, as long as the ActionGroup depth is not changed - ie:
    push/pop/cancelActionGroup should not be called. This is because it quickly
    creates an incoherent state for the Manager.  The Host *must* guarantee
    that a given state has only been thawed to a single active Context before
    such actions are performed.

    @warning This call only handles the opaque @ref manager_state object, it
    does *not* restore other properties of the Context (ie: access/retention,
    etc...)

    """
    ## @todo Sanitise input
    depth, managerToken = token.split('_', 1)
    context.actionGroupDepth = int(depth)
    state = self.__managerInterface.thawState(managerToken)
    context.managerInterfaceState = state


  @auditApiCall("Session")
  def getSettings(self):
    """

    A convenience for persisting a session. It retrieves all session settings,
    and the manager's settings in one dictionary. The @ref
    python.constants.kSetting_ManagerIdentifier key is used to hold the
    identifier of the active manager.

    @return dict

    """
    settings = {}

    manager = self.currentManager()
    if manager:
      settings.update(manager._getInterface().getSettings())

    settings[constants.kSetting_ManagerIdentifier]  = self._managerId
    return settings


  @auditApiCall("Session")
  def setSettings(self, settingsDict):
    """

    A convenience to restore the settings for a Session, the @ref
    python.constants.kSetting_ManagerIdentifier key is used to determine which
    Manager to instantiate. All other keys are passed to the Manager prior to
    initialization. If the Manager Identifier key is not present, no manager
    will be restored.

    """

    managerIdentifier  = settingsDict.get(constants.kSetting_ManagerIdentifier, None)
    if managerIdentifier:
      settingsDict = dict(settingsDict)
      del settingsDict[constants.kSetting_ManagerIdentifier]
    self.useManager(managerIdentifier, settingsDict)


  @auditApiCall("Session")
  def localizeString(self, sourceStr):
    """

    Substitutes any valid localizable tokens in the input string with those
    appropriate to the current Manager. These tokens are as per python format
    convention, using the constants defined in @ref python.constants under
    kLocalizationKey_*. For example:

      @li "{publish} to {manager}..."

    @param sourceStr a UTF-8 ASCII string to localize.

    @return str The input string with all applicable terms localized, and the
    braces ({}) removed from any unknown tokens.

    """
    try:
      # Make sure we dont abort if there is an unknown string
      sourceStr = sourceStr.format(**self.__terminology)
    except KeyError:
      pass
    return sourceStr.translate(None, "{}")


  @auditApiCall("Session")
  def getLocalizedString(self, key, default=''):
    """

    Returns the localized version of the supplied key, @ref python.constants
    under kLocalizationKey_*

    @return str or the supplied default if the key is unkown.

    """
    return self.__terminology.get(key, default)


  def _localize(self):

    self.__terminology = dict(Session.__terminology)

    # Get any custom strings from the manager that we should use in the UI,
    # this is to allow a consistent terminology across implementations of a
    # specific asset management system.

    manager = self.currentManager()
    if manager:
      manager.localizeStrings(self.__terminology)
      self.__terminology[constants.kLocalizationKey_Manager] = manager.getDisplayName()


