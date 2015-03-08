import FnAssetAPI

import nuke
import nukescripts

from .. import specifications
from .. import constants

from . import utils

_uiComponents = {}
_uiToRemove = []


## Return init wrapping function for widget class.
def getWrappedInitFn(widgetCls):

  def initWrappingFn(*args, **kwargs ):
    # We need to call configure after we construct it
    widget = widgetCls(*args, **kwargs)
    FnAssetAPI.ui.UISessionManager.currentSession().configureWidget(widget)
    return widget

  return initWrappingFn


# Set up the UI elements that we always keep around even when there is no
# manager
def buildStaticUI():

  # We had to make this menu dynamic as we can't rename it
  menu = _buildAssetMenu(nuke.menu('Nuke'))
  _uiComponents['assetMenu'] = menu


# Populate Nuke with anything relating to the manager currently selected,
# this should be called after anything that changes the current manager in the
# session. Maybe we need some signals here?
def bootstrapManagerUI():

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  # Adjust the title of the Asset Management menu, unfortunately, we need to
  # remake it rather than just being able to rename it
  nukeMenu = nuke.menu('Nuke')
  if nukeMenu.findItem(_uiComponents['assetMenu'].name()):
    nukeMenu.removeItem(_uiComponents['assetMenu'].name())
  _uiComponents['assetMenu'] = _buildAssetMenu(nukeMenu, manager)

  ## @todo Remove other UI elements if the new manager is different

  if not manager:
    return

  kCreatePanel = FnAssetAPI.ui.widgets.attributes.kCreateApplicationPanel

  managerWidgets = session.getManagerWidgets()
  for identifier,cls in managerWidgets.iteritems():

    if kCreatePanel & cls.getAttributes():

      widgetCls = session.getManagerWidget(identifier, instantiate=False)
      exposedClsName = identifier.replace(".", "_")

      # In nuke we need to leave the callable in an accessible namespace
      globals()[exposedClsName] = getWrappedInitFn(widgetCls)

      nukescripts.panels.registerWidgetAsPanel(
          "%s.%s" % (__name__, exposedClsName),
          widgetCls.getDisplayName(),
          widgetCls.getIdentifier())

  # Check the right menu items are available
  _addScriptMenuItems(session, manager)

  # Allow the manager to put things into the AssetMenu
  ## @todo How do we make sure we delete these?
  locale = FnAssetAPI.specifications.AssetMenuLocale()

  context = session.createContext()
  context.locale = locale
  context.access = context.kOther

  uiDelegate = session.getUIDelegate()
  uiDelegate.populateUI(_uiComponents['assetMenu'], None, context)



# Seemingly no (obvious) way to rename a menu in nuke so we'll rebuild the
# menu each time
def _buildAssetMenu(parentMenu, manager=None):

  menuName = "Asset Management"
  if manager:
    menuName = manager.getDisplayName()

  menu = parentMenu.addMenu(menuName)

  moduleName =  ".".join(__name__.split(".")[:-1])

  method = "%s.actions.showPrefs()" % moduleName
  menu.addCommand(constants.kNukMenu_Preferences, method)

  if FnAssetAPI.audit.auditCalls:
    auditMenu = menu.addMenu("API Audit")
    method = "%s.actions.startAudit()" % moduleName
    auditMenu.addCommand("Restart", method)
    method = "%s.actions.stopAudit()" % moduleName
    auditMenu.addCommand("Stop", method)
    method = "%s.actions.printAuditCoverage()" % moduleName
    auditMenu.addCommand("Print", method)

  return menu


def _addScriptMenuItems(session, manager):

  # File Menu
  fileMenu = nuke.menu("Nuke").findItem("File")
  if not fileMenu:
    return

  global _uiComponents

  # Why oh why is everything so complicated, why can't we alter a menu items
  # text after it has been created?

  ## @todo removed deletion of items as its crashing like a mo-fo

  #openItem = _uiComponents.get('openPublishedScriptMenuItem', None)
  #if openItem and fileMenu.findItem(openItem.name()):
  #  fileMenu.removeItem(openItem.name())

  #publishItem = _uiComponents.get('publishScriptMenuItem', None)
  #if publishItem and fileMenu.findItem(publishItem.name()):
  #  fileMenu.removeItem(publishItem.name())

  #republishItem = _uiComponents.get('republishScriptMenuItem', None)
  #if republishItem and fileMenu.findItem(republishItem.name()):
  #  fileMenu.removeItem(republishItem.name())

  #topSeparator = _uiComponents.get('fileMenuTopSeparator', None)
  #if topSeparator and fileMenu.findItem(topSeparator.name()):
    #fileMenu.removeItem(topSeparator.name())

  #bottomSeparator = _uiComponents.get('fileMenuBottomSeparator', None)
  #if bottomSeparator and fileMenu.findItem(bottomSeparator.name()):
    #fileMenu.removeItem(bottomSeparator.name())

  # Find out if the script publish menu items should be available

  scriptSpec = specifications.NukeScriptSpecification()
  c = session.createContext()

  c.access = c.kRead
  scriptReadPolicy = manager.managementPolicy(scriptSpec, c)
  c.access = c.kWrite
  scriptWritePolicy = manager.managementPolicy(scriptSpec, c)

  scriptRead = scriptReadPolicy != FnAssetAPI.constants.kIgnored
  scriptWrite = scriptWritePolicy != FnAssetAPI.constants.kIgnored

  l = FnAssetAPI.l

  if not ( scriptRead or scriptWrite ):
    return

  ## @todo Find this properly
  startingIndex = 7

  _uiComponents['fileMenuBottomSeparator'] = fileMenu.addSeparator(index=startingIndex)

  moduleName =  ".".join(__name__.split(".")[:-1])

  # Replace the existing version up script command with one that also
  # version-ups the Write node file paths.
  fileMenu.addCommand("Save New &Version", "fnassetmgr.foundry.assetmgr.plugins.nuke.onScriptVersionUp()", "#+S")
  versionUpMethod = "%s.utils._script_version_all_up()" % moduleName
  versionUpTitle = "Save New &Version"
  item = fileMenu.addCommand(versionUpTitle, versionUpMethod)

  repubScriptMethod = "%s.actions.versionUpAndRePublish()" % moduleName
  repubTitle = l(constants.kNukeMenu_RePublishScript)
  item = fileMenu.addCommand(repubTitle, repubScriptMethod, index=startingIndex)
  _uiComponents['republishScriptMenuItem'] = item

  pubScriptMethod = "%s.actions.publishScriptUI()" % moduleName
  pubTitle = l(constants.kNukeMenu_PublishScript)
  item = fileMenu.addCommand(pubTitle, pubScriptMethod, index=startingIndex)
  _uiComponents['publishScriptMenuItem'] = item

  openScriptMethod = "%s.actions.openPublishedScriptUI()" % moduleName
  openTitle = l(constants.kNukeMenu_OpenPublishedScript)
  item = fileMenu.addCommand(openTitle, openScriptMethod, index=startingIndex)
  _uiComponents['openPublishedScriptMenuItem'] = item

  _uiComponents['fileMenuTopSeparator'] = fileMenu.addSeparator(index=startingIndex)



