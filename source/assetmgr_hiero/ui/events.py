import hiero.core

from . import interface

def registerUIEvents():

  hiero.core.events.registerInterest("kShowContextMenu/kTimeline", interface.populateTimelineContextMenu)
  hiero.core.events.registerInterest("kShowContextMenu/kSpreadsheet", interface.populateTimelineContextMenu)
  hiero.core.events.registerInterest("kShowContextMenu/kBin", interface.populateBinContextMenu)

  # We additionally track selection in the UI module to reconfigure Actions
  hiero.core.events.registerInterest(
      hiero.core.events.EventType.kSelectionChanged, __hieroSelectionChangedUI)


  import FnAssetAPI.Events
  manager = FnAssetAPI.Events.getEventManager()

  # Track the manager changing in a session
  manager.registerListener(manager.kManagerChanged, __assetManagerChanged)


def __assetManagerChanged(session, oldId, newId):
  # When the manager changes, we want to rebuild the UI
  interface.bootstrapManagerUI()


def __hieroSelectionChangedUI(event):
  """
  Call when the Hiero selection changes, update any actions as neccesary.
  """

  selection = event.sender.selection()
  interface.updateActionState(selection)

