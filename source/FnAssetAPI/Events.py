from .core.EventManager import EventManager, DelayedEventProcessor

from .audit import auditApiCall


__all__ = ['Events']


class Events(EventManager):
  """

  The Events class implements the core \ref python.core.EventManager
  "EventManager" to define some well-known events in an accessible form.

  The static event triggers here should be used in preference to manually
  queueing events where possible. This class also defines some constants for
  the names of these events for use when registering listeners etc...

  @see python.core.EventManager for details on how to configure the queue, send
  events etc...

  """

  ##
  # @name Well-known Events
  #
  ## @{

  kSelectionChanged = 'selectionChanged'
  kManagerChanged = 'managerChanged'

  ## @}

  def __init__(self):
    super(Events, self).__init__()
    self._setupDefaultEventProcessors()


  def _setupDefaultEventProcessors(self):

    # Map logging to the standard AssetAPI logger
    from . import logging
    self.logger = logging

    selectionChangedProc = DelayedEventProcessor()
    selectionChangedProc.setDelay(0.6)
    self.addEventProcessor(self.kSelectionChanged, selectionChangedProc)
    # Most things that listen to selection changed probably don't work very
    # well if they're not on the main thread, as they update UI
    ## @todo Any safe way to run UI updates on another thread as this blocks a lot?
    self.setRunOnMainThread(self.kSelectionChanged, True)

    # Manager changed will most likely map to some UI changes, and so should
    # happen on the main thread too
    self.setRunOnMainThread(self.kManagerChanged, True)

  @auditApiCall("Events")
  def queueEvent(self, eventOrType, *args, **kwargs):
    """

    @see python.core.EventManager.EventManager.queueEvent, implemented here to
    add API Auditing.

    """
    return super(Events, self).queueEvent(eventOrType, *args, **kwargs)

  @staticmethod
  @auditApiCall("Events", static=True)
  def selectionChanged(entityRefs):
    """

    Call to indicate the current selection has changed.

    @param entityRefs list[str], A list of the currently selected entity refs, or
    an empty list if nothing in the selection maps to an entity.

    @event **selectionChanged** *c(entityReferenceList)* Called whenever the
    user's selection has changed. This is pre-filtered to only contain @ref
    entity_reference "Entity References". The list will be empty if there are
    objects selected, but they do not map to an @ref Entity

    """
    m = Events.getEventManager()
    m.queueEvent(Events.kSelectionChanged, entityRefs)


  @staticmethod
  @auditApiCall("Events", static=True)
  def managerChanged(session, oldId, newId):
    """

    Call to indicate the manager for a session has changed. Identifiers are used
    over instances as managers are constructed lazily, whenever they are first
    used.

    @event **managerChanged** *c(session, oldId, newId)* Called when the Asset
    Manager for a session has changed.

    """
    m = Events.getEventManager()
    m.queueEvent(Events.kManagerChanged, session, oldId, newId)


  @classmethod
  @auditApiCall("Events")
  def getEventManager(cls):
    """

    Returns the active event manager that should be used for all event dispatch.

    """
    return cls.singletonInstance()


