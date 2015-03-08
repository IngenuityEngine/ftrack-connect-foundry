import FnAssetAPI

import hiero.core
from PySide import QtGui

from .. import specifications
from . import actions
from . import utils


__all__ = [
  'createStaticActions',
  'reconfigureActions',
  'updateActionState',
  'buildStaticUI',
  'bootstrapManagerUI',
  'populateBinContextMenu',
  'populateTimelineContextMenu'
]


# We keep track of ui components so they don't get deleted due to a lack of
# refcounts, etc...
__actions = {}

# We also might need to delete UI elements when the manager changes
__uiToRemove = []



# Create any actions that we always use throught the UI
def createStaticActions(parent):

  a = {}

  a['prefsAction'] = actions.AssetPreferencesAction(parent=parent)

  a['openPublishedProjectAction'] = actions.OpenPublishedProjectAction(parent=parent)
  a['publishProjectAction'] = actions.PublishProjectAction(parent=parent)

  a['generateShotsAction'] = actions.GenerateShotsAction(parent=parent)
  a['updateShotsAction'] = actions.UpdateShotsAction(parent=parent)
  a['publishShotClipsAction'] = actions.PublishShotsClipsAction(parent=parent)

  a['buildAssetTrack'] = actions.BuildAssetTrackAction(parent=parent)
  a['refreshAssetTrack'] = actions.RefreshAssetTrackAction(parent=parent)

  a['publishClipsAction'] = actions.PublishClipsAction(parent=parent)
  a['importClipsAction'] = actions.ImportClipsAction(parent=parent)
  a['linkSequenceAction'] = actions.LinkSequenceToGroupingAction(parent=parent)

  if FnAssetAPI.audit.auditCalls:
    a['auditStartAction'] = actions.StartAuditAction(parent=parent)
    a['auditStopAction'] = actions.StopAuditAction(parent=parent)
    a['auditPrintAction'] = actions.PrintAuditAction(parent=parent)

  return a



def reconfigureActions(session):

  global __actions

  # We set the properties for the action when we made it, so we can just call
  # this instead
  for a in __actions.values():
    session.configureAction(a)
    # Many any that care re-check the manager too
    if hasattr(a, 'managerChanged'):
      a.managerChanged()


def updateActionState(selection=None):

  global __actions

  for a in __actions.values():
    if hasattr(a, 'setSelection'):
      a.setSelection(selection if selection else [])


# Set up any Hiero UI items that we'll always keep around
def buildStaticUI():

  global __actions

  menu = QtGui.QMenu("Asset Management")
  __actions['assetMenu'] = menu
  _addAssetMenuItems(menu)

  helpmenu = hiero.ui.findMenuAction("Help")
  hiero.ui.menuBar().insertMenu(helpmenu, menu)

  filemenuaction = hiero.ui.findMenuAction("File")
  if filemenuaction:
    filemenu = filemenuaction.menu()
    __extendFileMenu(filemenu)

  clipmenuaction = hiero.ui.findMenuAction("Clip")
  if clipmenuaction:
    clipmenu = clipmenuaction.menu()
    __extendClipMenu(clipmenu)

  timelinemenuaction = hiero.ui.findMenuAction("Timeline")
  if timelinemenuaction:
    timelinemenu = timelinemenuaction.menu()
    if timelinemenu:
      __extendTimelineMenu(timelinemenu)


def _addAssetMenuItems(menu):

  global __actions

  menu.addAction(__actions['prefsAction'])

  # If auditing has been enabled by the env var, then these items might be useful
  if 'auditStartAction' in  __actions:
    auditSubMenu = QtGui.QMenu("API Audit")
    auditSubMenu.addAction(__actions['auditStartAction'])
    auditSubMenu.addAction(__actions['auditStopAction'])
    auditSubMenu.addAction(__actions['auditPrintAction'])
    menu.addMenu(auditSubMenu)

  return menu


def __extendFileMenu(filemenu):

  global __actions

  openclips = hiero.ui.findMenuAction("Import Clips...")
  if openclips:
    filemenu.insertSeparator(openclips)
    filemenu.insertAction(openclips, __actions['openPublishedProjectAction'])
    filemenu.insertAction(openclips, __actions['publishProjectAction'])
    filemenu.insertSeparator(openclips)
    filemenu.insertAction(openclips, __actions['importClipsAction'])


def __extendClipMenu(clipmenu):

  reconnect = hiero.ui.findMenuAction("Reconnect Media...")
  if reconnect:
    clipmenu.insertAction(reconnect, __actions['publishClipsAction'])
    clipmenu.insertSeparator(reconnect)


def __extendTimelineMenu(timelinemenu):
  if timelinemenu:
    # TODO: timelinemenu is None in Nuke Studio - confirm bug with The Foundry
    # and discuss correct approach.
    timelinemenu.addSeparator()
    timelinemenu.addAction(__actions['generateShotsAction'])
    timelinemenu.addAction(__actions['updateShotsAction'])
    timelinemenu.addAction(__actions['publishShotClipsAction'])
    timelinemenu.addSeparator()
    timelinemenu.addAction(__actions['linkSequenceAction'])


def populateTimelineContextMenu(event):
  """
  @localeUsage hiero.specifications.HieroTimelineContextMenuLocale
  """
  global __actions

  if not (hasattr(event, "menu") and event.menu) or not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which gives a selection.
      return

  session = FnAssetAPI.SessionManager.currentSession()
  if not session.currentManager():
    return

  managerName = session.currentManager().getDisplayName()
  submenu = QtGui.QMenu(managerName)
  session.configureAction(submenu, addIcon=True)

  selection = event.sender.selection()

  if not selection:
    view = hiero.ui.activeView()
    if view and hasattr(view, 'sequence'):
      sequence = view.sequence()
      if sequence:
        selection = [sequence,]

  generateShots = __actions['generateShotsAction']
  submenu.addAction(generateShots)

  updateShots = __actions['updateShotsAction']
  submenu.addAction(updateShots)

  publishClips = __actions['publishClipsAction']
  submenu.addAction(publishClips)

  publishShotClips = __actions['publishShotClipsAction']
  submenu.addAction(publishShotClips)

  # See if we have a Build Track menu
  allowBuildTrack = True
  buildTrackMenu = utils.findNamedSubMenu("Build Track", event.menu)
  if not buildTrackMenu:
    # If we didnt have the menu, then the build track actions shouldnt be there
    # (as Hiero's arent). But we make the 'refresh' action available as its new
    allowBuildTrack = False
    buildTrackMenu = QtGui.QMenu("Build Track")
    event.menu.addMenu(buildTrackMenu)
    # Add in our Build Track action

  ## @todo put this in the Build Track submenu not here
  ## @todo Check managementPolicy
  ## @todo Disable if the provider doesn't have the widget
  buildAssetTrack = __actions['buildAssetTrack']
  buildAssetTrack.reset()
  buildAssetTrack.setEnabled(allowBuildTrack)
  buildTrackMenu.addAction(buildAssetTrack)

  refreshAssetTrack = __actions['refreshAssetTrack']
  buildTrackMenu.addAction(refreshAssetTrack)

  event.menu.addSeparator()
  event.menu.addMenu(submenu)

  locale = specifications.HieroTimelineContextMenuLocale()
  locale.event = event

  context = session.createContext()
  context.locale = locale
  context.access = context.kOther

  uiDelegate = session.getUIDelegate()
  uiDelegate.populateUI(submenu, None, context)


def populateBinContextMenu(event):
  """
  @localeUsage hiero.specifications.HieroBinContextMenuLocale
  """
  global __actions

  if not hasattr(event, "menu") or not event.menu:
    return

  session = FnAssetAPI.SessionManager.currentSession()
  if not session.currentManager():
    return

  # Publish Clips
  publishClips = __actions['publishClipsAction']
  event.menu.addAction(publishClips)

  # Import Clips
  importClips = __actions['importClipsAction']

  importSubmenu = utils.findNamedSubMenu("Import", event.menu)
  if importSubmenu:
    importSubmenu.addAction(importClips)
  else:
    event.menu.addAction(importClips)

  # Link Sequence
  linkSeq = __actions['linkSequenceAction']
  event.menu.addAction(linkSeq)

  locale = specifications.HieroBinContextMenuLocale()
  locale.event = event

  context = session.createContext()
  context.locale = locale
  context.access = context.kOther

  uiDelegate = session.getUIDelegate()
  uiDelegate.populateUI(event.menu, None, context)

  event.menu.addSeparator()


# Populate Hiero with anything relating to the manager currently selected,
# this should be called after anything that changes the current manager in the
# session. Maybe we need some signals here?
def bootstrapManagerUI():
  """
  @localeUsage hiero.specifications.HieroBinContextMenuLocale
  """
  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  assetMenu = __actions['assetMenu']

  # Adjust the title of the Asset Management menu
  mainMenuName = "Asset Management"
  if manager:
    mainMenuName = manager.getDisplayName()
  assetMenu.setTitle(mainMenuName)

  # Remove any old elements and repopulate
  assetMenu.clear()
  _addAssetMenuItems(assetMenu)

  ## @todo Remove any other UI elements that the other manager may have made?

  if not manager:
    return

  mainWindow = hiero.ui.mainWindow()
  windowManager = hiero.ui.windowManager()

  kCreatePanel = FnAssetAPI.ui.widgets.attributes.kCreateApplicationPanel

  managerWidgets = session.getManagerWidgets()
  for identifier,cls in managerWidgets.iteritems():
    if kCreatePanel & cls.getAttributes():
      widget = session.getManagerWidget(identifier, parent=mainWindow)
      windowManager.addWindow(widget)
      __uiToRemove.append(widget)

  locale = FnAssetAPI.specifications.AssetMenuLocale()

  context = session.createContext()
  context.locale = locale
  context.access = context.kOther

  uiDelegate = session.getUIDelegate()
  uiDelegate.populateUI(assetMenu, None, context)

  # Check the enabled state for our static UI that may depend on manager
  # capabilities, etc...
  # Reset the icons for any actions that use them, when called with no flags,
  # it will look for any set by a previous call. this means we don't have to
  # worry about adding icons to actions that don't need them
  reconfigureActions(session)
  updateActionState(selection=[])

# Because many of the actions are used in static menus too, we make them at the
# beginning
__actions = createStaticActions(hiero.ui.mainWindow())


