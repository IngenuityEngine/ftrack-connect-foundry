
def registerUIEvents():

  import FnAssetAPI.Events
  manager = FnAssetAPI.Events.getEventManager()

  # Track the manager changing in a session
  manager.registerListener(manager.kManagerChanged, __assetManagerChanged)


def __assetManagerChanged(session, oldId, newId):
  # When the manager changes, we want to rebuild the UI
  from . import interface
  interface.bootstrapManagerUI()


