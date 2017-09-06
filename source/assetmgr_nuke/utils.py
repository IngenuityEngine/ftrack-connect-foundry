from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets
import FnAssetAPI
import nuke

from . import filters


class KnobChangedAggregator(object):
  """
  Nuke currently communicates selection with a knobChanged event, and the
  'selected' knob. So we have to keep track of which are selected during a drag
  as we don't get any 'list of nodes' type notifications... :(
  """

  def __init__(self):
    super(KnobChangedAggregator, self).__init__()
    self.__selectedNodes = set()
    self.__lastSelection = None

  def knobChanged(self):

    knob = nuke.thisKnob()
    if knob.name() != 'selected':
      return

    node = nuke.thisNode()

    # Prune any that were selected, that arent selected any more
    toRemove = []
    for n in self.__selectedNodes:
      if not n['selected'].getValue():
        toRemove.append(n)

    for t in toRemove:
      self.__selectedNodes.remove(t)

    # Add in our current selection
    if knob.getValue():
      self.__selectedNodes.add(node)
    else:
      if node in self.__selectedNodes:
        self.__selectedNodes.remove(node)

    self.nodesChanged()


  def nodesChanged(self):

    entityRefs = set()
    for n in self.__selectedNodes:
      entityRefs.update(entitiesFromNode(n, asRefs=True))

    # Ask anyone else who is interested if they want to contribute
    # Copy the list of selected nodes to prevent them messing with it
    ## @todo Document this
    manager = FnAssetAPI.Events.getEventManager()
    manager.blockingEvent(True, 'entityReferencesFromNukeNodes',
        list(self.__selectedNodes), entityRefs)

    if entityRefs != self.__lastSelection:
      FnAssetAPI.Events.selectionChanged(list(entityRefs))

    self.__lastSelection = entityRefs


__knobChangedAggregator = KnobChangedAggregator()


def registerEvents():

   # Hook the event manager up
  import FnAssetAPI.Events
  manager = FnAssetAPI.Events.getEventManager()
  manager.setMainThreadExecFn(nuke.executeInMainThreadWithResult)
  manager.run()

  global __knobChangedAggregator
  for c in ("Read", "Write", "Group"):
    nuke.addKnobChanged(__knobChangedAggregator.knobChanged, nodeClass=c)

  manager.registerListener(manager.kSelectionChanged, debugSelectionChanged)

  # Track the manager changing in a session, so we can persist its ID and
  # update menus etc...
  manager.registerListener(manager.kManagerChanged, __assetManagerChanged)



def debugSelectionChanged(selection):
  FnAssetAPI.logging.debug("Selected Entities: %r" % selection)



def entitiesFromNode(node, asRefs=False):

  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return []

  entities = []
  for k in node.knobs().values():
    if isinstance(k, nuke.File_Knob):
      v = k.getValue()
      if manager.isEntityReference(v):
        if asRefs:
          entities.append(v)
        else:
          entities.append(manager.getEntity(v))

  return entities


## Decorators #################################################################

def ensureManager(function):
  def _ensureManager(*args, **kwargs):
    session = FnAssetAPI.SessionManager.currentSession()
    if not session:
      raise RuntimeError("No Asset Management Session")
    if not session.currentManager():
      raise RuntimeError("No Asset Management Manager selected")
    return function(*args, **kwargs)
  return _ensureManager


## @name Manager Changed
## @{

def __assetManagerChanged(s, oldId, newId):
  # Make sure we save the session settings now we have a new manager
  from . import session
  session.saveManagerSessionSettings(s)

## @}



def registerFilters():

  nuke.addFilenameFilter(filters.assetAPIFilenameFilter)

  ## @todo Presently, this doesn't work as it gets called after filenameFilter
  nuke.addValidateFilename(filters.assetAPIFilenameValidator)


def getSetting(name, default=None):

  settings = QtCore.QSettings("uk.co.foundry", "core.asset.nuke")
  return settings.value(name, default)


def setSetting(name, value):

  settings = QtCore.QSettings("uk.co.foundry", "core.asset.nuke")
  settings.setValue(name, value)


def rootNodeAssetKnob(create=True):

  assetTab = nuke.root().knobs().get("Assets")
  if not assetTab and create:
    assetTab = nuke.Tab_Knob("Assets")
    nuke.Root().addKnob(assetTab)
  return assetTab



def storeRootNodeData(field, value):

  assetKnob = rootNodeAssetKnob()
  key =  'FnAssetAPI_%s' % field
  root = nuke.root()
  knob = root.knobs().get(key)
  if not knob:
    knob = nuke.String_Knob(key, field)
    root.addKnob(knob)
  knob.setValue(str(value))


def getRootNodeData(field, default=None):

  assetKnob = rootNodeAssetKnob()
  key =  'FnAssetAPI_%s' % field
  root = nuke.root()
  knob = root.knobs().get(key)
  if not knob:
    return default
  return knob.value()



__nonPersistentTagData = {}

def getTemporaryRootNodeData(field, default=None):
  """

  Version of getRootNodeData for fields that are stored only in memory, and so are
  lost when the application closes.

  """

  global __nonPersistentTagData

  # We don't want to keep a refcount on the root object, not sure if this is
  # stable....
  obj = id(nuke.root())

  objDict = __nonPersistentTagData.get(obj, None)
  if not objDict:
    return default
  return objDict.get(field, default)



def storeTemporaryRootNodeData(field, value):
  """

  Version of setRootNodeData that stores fields in memory, and so are
  lost when the application closes.

  """
  global __nonPersistentTagData

  # We don't want to keep a refcount on the root object, not sure if this is
  # stable....
  obj = id(nuke.root())

  objDict = __nonPersistentTagData.setdefault(obj, {})
  objDict[field] = value


