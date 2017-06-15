import FnAssetAPI
from FnAssetAPI.decorators import ensureManager
from FnAssetAPI.specifications import DocumentLocale

from .. import specifications
from .. import commands
from .. import items
from .. import utils as cmdUtils

from . import widgets
from . import utils

import nuke

from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets


def showPrefs():
  s = FnAssetAPI.SessionManager.currentSession()
  prefsDialog = widgets.AssetPreferencesDialog()
  prefsDialog.setSession(s)
  prefsDialog.exec_()


def startAudit():
  FnAssetAPI.audit.auditCalls = True
  FnAssetAPI.audit.auditor().reset()

def stopAudit():
  FnAssetAPI.audit.auditCalls = False
  printAuditCoverage()

def printAuditCoverage():
  print FnAssetAPI.audit.auditor().sprintCoverage()



@ensureManager
def openPublishedScriptUI():

  # Because we have to clear the current script (due to the world of fork fun
  # with seemingly every other method, that results in the code being run on
  # the wrong script), if the user has changed the document, we need to ask
  # them to save, blah de blah.
  if nuke.Root().modified():
    action = utils.confirmClose()
    if action == "cancel":
      return ''
    elif action =="save":
      nuke.scriptSave()

  from FnAssetAPI.ui.dialogs import TabbedBrowserDialog

  session =  FnAssetAPI.SessionManager.currentSession()

  context = session.createContext()
  context.access = context.kRead
  context.locale = DocumentLocale()

  spec = specifications.NukeScriptSpecification()

  hint = cmdUtils.getTemporaryRootNodeData('entityReference')
  if hint:
    spec.referenceHint = hint

  browser = TabbedBrowserDialog.buildForSession(spec, context)
  browser.setWindowTitle(FnAssetAPI.l("Open {published} Script"))
  browser.setAcceptButtonTitle("Open")

  if not browser.exec_():
    return ''

  selection = browser.getSelection()

  if not selection:
    return ''

  return commands.openPublishedScript(selection[0], context=context)


def _getScriptOpenOptions():

  l = FnAssetAPI.l

  msgBox = QtWidgets.QMessageBox()
  msgBox.setText(l("{published} Scripts can't be opened directly."))
  msgBox.setInformativeText("This is to avoid changing the asset itself by "
      +"saving. Would you like to Save a Copy or import the nodes?")

  saveAs = msgBox.addButton("Save As...", msgBox.AcceptRole)
  imp = msgBox.addButton("Import", msgBox.NoRole)

  # Had some issues with StandardButton .vs. AbstractButton
  msgBox.addButton("Cancel", msgBox.RejectRole)

  msgBox.exec_()
  button = msgBox.clickedButton()

  if button == saveAs:
    return 'saveas'
  elif button == imp:
    return 'import'
  else:
    return ''



@ensureManager
def versionUpAndRePublish():

  l = FnAssetAPI.l

  # If we know the entity ref, we can re-publish
  entityRef = cmdUtils.getTemporaryRootNodeData('entityReference', None)
  if not entityRef:
    FnAssetAPI.logging.error(l("Sorry, unable to determine which {asset} this "+
        "script belongs to, please manually {publish} first."))
    return ''

  session =  FnAssetAPI.SessionManager.currentSession()

  context = session.createContext()
  context.access = context.kWrite
  context.locale = DocumentLocale()

  return commands.publishScript(entityRef, versionUp=True)


@ensureManager
def publishScriptUI():

  from FnAssetAPI.ui.dialogs import TabbedBrowserDialog

  session =  FnAssetAPI.SessionManager.currentSession()

  context = session.createContext()
  context.access = context.kWrite
  context.locale = DocumentLocale()

  item = items.NukeScriptItem()
  try:
    item.path = nuke.scriptName()
  except RuntimeError:
    item.path = None

  spec = item.toSpecification()

  # First we have to see what the management policy of the manager is
  manager = session.currentManager()
  policy = manager.managementPolicy(spec, context)

  if policy == FnAssetAPI.constants.kIgnored:
    raise RuntimeError("The current asset management system doesn't handle Nuke Scripts (%s)" % policy)

  managesPath = policy & FnAssetAPI.constants.kWillManagePath

  l = FnAssetAPI.l

  # If it doesn't manage the path, make sure the document has a path already
  if not managesPath and not item.path:
    raise RuntimeError(l("Please save your script first before "
      +"it can be {published}"))

  ## @todo See Hiero - where we try to find a hint from refs used in the scene,
  ## and set it as the referenceHint in the spec, instead of setting the selection
  hint = cmdUtils.getTemporaryRootNodeData('entityReference')
  if hint:
    spec.referenceHint = hint

  browser = TabbedBrowserDialog.buildForSession(spec, context)
  browser.setWindowTitle(
      l("{publish} Script") if managesPath else l("{publish} Existing Script"))
  browser.setAcceptButtonTitle(l("{publish}"))

  if hint:
    browser.setSelection(hint)

  if not browser.exec_():
    return None

  selection = browser.getSelection()
  if not selection:
    return None

  entityRef = selection[0]

  return commands.publishScript(entityRef, context, versionUp=False)



