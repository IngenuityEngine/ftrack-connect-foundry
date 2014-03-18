import FnAssetAPI
from FnAssetAPI.core.EventManager import EventManager, DelayedEventProcessor

import hiero.core

from . import utils
from . import session

__all__ = [
  'registerEvents',
]

kComputeEventName = '_computeHieroSelection'


def registerEvents():

  # Hook the asset system event manager up

  import FnAssetAPI.Events
  manager = FnAssetAPI.Events.getEventManager()

  # Because our compute loop is somewhat heavy, we add in a new rate limited
  # event, that is rate limited to compute the selection
  computeSelectionProc = DelayedEventProcessor()
  computeSelectionProc.setDelay(0.6)
  manager.addEventProcessor(kComputeEventName, computeSelectionProc)
  manager.registerListener(kComputeEventName, __computeHieroSelection)

  # The asset system requires a 'run in main thread' method if you want to use
  # its own built-in event loop thread, fortunately we have one
  manager.setMainThreadExecFn(__execInMain)
  manager.run()

  # Selection Changed
  hiero.core.events.registerInterest(
      hiero.core.events.EventType.kSelectionChanged, __hieroSelectionChanged)

  # Make it easy to debug what the manager selected
  manager.registerListener(manager.kSelectionChanged, __debugAssetSelectionChanged)

  # Track the manager changing in a session, so we can persist its ID and
  # update menus etc...
  manager.registerListener(manager.kManagerChanged, __assetManagerChanged)


def __execInMain(method, args, kwargs):
  # We have to unpack the args...
  return hiero.core.executeInMainThreadWithResult(method, *args, **kwargs)



## @name Selection Changed
## @{


def __debugAssetSelectionChanged(selection):
  # Make it easier to see what we ended up submitting in our event
  FnAssetAPI.logging.debug("Selected Entities: %r" % (selection,))


# Because we don't want do send an event if the selection hasn't changed
__lastSelection = None


# A this event occurs a lot, deffer our processing using the standard deffered
# kComputeSelectionChanged event in the AssetAPI.
def __hieroSelectionChanged(event):

  selection = event.sender.selection()
  m = FnAssetAPI.Events.getEventManager()
  m.queueEvent(kComputeEventName, selection)


# Listens to the kComputeSelectionChanged event so we don't do this work too
# often when the selection is changing rapidly
def __computeHieroSelection(selection):
  """
  Call when the Hiero selection changes, it will filter through it for anything
  we know how to map back to an entity.
  """

  # Run away if we don't have an asset manager set
  if not FnAssetAPI.SessionManager.currentManager():
    return

  global __lastSelection

  entityRefs = set()

  ## @todo make a context properly
  context = None

  # If we fail to find an entity based on the clip in a track item, we look for
  # them as shots under a parent, if we have one.
  trackItems = []

  for s in selection:

    ## @todo Document this mapping, and how Hiero stores entity refs

    entity = None

    if isinstance(s, hiero.core.TrackItem):
      # TrackItems are handled separately so that we can look for parent shots,
      # etc...
      trackItems.append(s)

      continue

    # If its a BinItem, we want the thing inside it...
    elif isinstance(s, hiero.core.BinItem):
      s = s.activeItem()

    entity = utils.entity.anEntityFromObj(s, includeChildren=True)

    if entity:
      entityRefs.add(entity.reference)

  # Now look en-mass for track items as shots, we don't care about options as
  # we're ignoring timings for now
  trackItemEntities = utils.shot.entitiesFromTrackItems(trackItems, context,
      searchClips=True)
  entityRefs.update([ e.reference for e in trackItemEntities if e ])

  # Ask anyone else who is interested if they want to contribute
  # Copy the list of selected nodes to prevent them messing with it
  eventManager = FnAssetAPI.Events.getEventManager()
  eventManager.blockingEvent(True, 'entityReferencesFromHieroObjects',
      list(selection), entityRefs)

  if entityRefs != __lastSelection:
    refs = list(entityRefs)
    # We need to make sure this event won't be delayed. There is a standard
    # delay on the main selection changed event for rate-limiting, but we can
    # bypass this as we already throttled our compute process....
    event = EventManager.Event(FnAssetAPI.Events.kSelectionChanged, refs)
    setattr(event, DelayedEventProcessor.kBypassAttribute, True)
    eventManager.queueEvent(event)

  __lastSelection = entityRefs

## @}


## @name Manager Changed
## @{

def __assetManagerChanged(s, oldId, newId):
  # Make sure we save the session settings now we have a new manager
  session.saveManagerSessionSettings(s)

## @}


