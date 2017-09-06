from QtExt import QtGui, QtWidgets

import FnAssetAPI

import hiero.ui

from .. import specifications


## @todo Clean up all the horrible action stuff

def findNamedSubMenu(name, menu):

  # For some reason we have to do some of these differently than others
  # This method avoids 'The underlying C object has been deleted' error
  # when the action python representation gets deleted too soon.

  namedMenu = None
  for c in menu.findChildren(QtWidgets.QMenu):
    if c.title() == name:
      namedMenu = c
      break

  # This method finds some actions that don't show up otherwise, but has the
  # python object problem, so it has to come second

  if not namedMenu:
    children = menu.actions()
    filtered = filter(lambda m : m.text() == name, children)
    namedMenu = filtered[0].menu() if filtered else None

  # Is this madness really necessary?

  return namedMenu


## @todo This should probably be done with Items instead
def browseForProject(title="Choose Project", button="Select",
    locale=None, locationHint=None, setLocation=False, context=None,
    parent=None):
  """
  @localeUsage FnAssetAPI.specifications.DocumentLocale
  @specUsage FnAssetAPI.specifications.HieroProjectSpecification
  """
  from FnAssetAPI.ui.dialogs import TabbedBrowserDialog

  if parent is None:
    parent = hiero.ui.mainWindow()

  session =  FnAssetAPI.SessionManager.currentSession()
  if not session:
    FnAssetAPI.logging.error("No Asset Management Session")
    return []

  if not context:
    context = session.createContext()

  context.retention = context.kPermanent

  if locale:
    context.locale = locale
  elif not context.locale:
    context.local = specifications.DocumentLocale()

  ## @todo Fill in with valid extensions, etc...
  spec = FnAssetAPI.specifications.HieroProjectSpecification()
  if locationHint:
    spec.referenceHint = str(locationHint)

  browser = TabbedBrowserDialog.buildForSession(spec, context, parent=parent)
  browser.setWindowTitle(title)
  browser.setAcceptButtonTitle(button)

  if locationHint and setLocation:
    browser.setSelection(locationHint)

  if browser.exec_():
    return browser.getSelection()
  else:
    return []



