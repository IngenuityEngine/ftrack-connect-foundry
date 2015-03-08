import FnAssetAPI.QtHost
import nuke


class NukeHost(FnAssetAPI.QtHost):

  def __init__(self):
    super(NukeHost, self).__init__()


  def getIdentifier(self):
    return "uk.co.foundry.nuke"


  def getDisplayName(self):
    return "Nuke"


  def getDocumentReference(self):
    return nuke.root().name()


  def inUI(self):
    import nuke
    return bool(nuke.env.get("gui", ''))


  def mainWindow(self):
    return None


  def getEntityReferencesForItem(self, item, allowRelated=False):

    import utils

    entities = utils.entitiesFromNode(item)
    return [ e.reference for e in entities ]


