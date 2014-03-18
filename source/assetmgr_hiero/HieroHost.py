import FnAssetAPI.QtHost
import hiero.core


class HieroHost(FnAssetAPI.QtHost):

  def __init__(self):
    super(HieroHost, self).__init__()


  def getIdentifier(self):
    return "uk.co.foundry.hiero"


  def getDisplayName(self):
    return "Hiero"


  def getDocumentReference(self):
    ## @todo Tricky this one
    projects = hiero.core.projects()
    if projects:
      return projects[-1].path()
    return ""


  def getEntityReferencesForItem(self, item, allowRelated=False):

    import utils

    entity = utils.entity.entityFromObj(item)

    if not entity and allowRelated:
      entity = utils.entity.anEntityFromObj(item, includeChildren=True,
          includeParents=True)

    if entity:
      return [entity.reference,]

    return ['',]



  def inUI(self):
    return True


  def mainWindow(self):
    import hiero.ui
    return hiero.ui.mainWindow()

