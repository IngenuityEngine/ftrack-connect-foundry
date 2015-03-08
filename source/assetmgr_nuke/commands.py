import FnAssetAPI
from FnAssetAPI.decorators import ensureManager

from . import utils
from . import items
from . import specifications

import nuke
import nukescripts

## @todo Standardise use of Entities/References

@ensureManager
def openPublishedScript(entityRef, context=None):

  ## @todo Scripts should be read-only if gathered from the asset system.
  ## Ideally, we need some knowledge in Nuke, that realises it was opened from
  ## an entity reference so that it update the behaviour or version up/etc...
  ## So, for now, we'll just make a new script an import the nodes

  ## @todo Nuke doesnt seem to call filenameFilters on scriptReadFile
  session = FnAssetAPI.SessionManager.currentSession()
  if not context:
    context = session.createContext()

  # We also have the issue that if you open a script, whilst one is already
  # loaded in nuke, it will fork, and the rest of this code will run in the
  # wrong process... Unfortunately if you just use nuke.scriptClose() this it
  # also makes a new process, and runs the rest of this code in the old nuke,
  # before it dies. Amazing. As this is a batch script, we cant confirm, so we
  # just blow away the current script before hand with clear.
  # The UI version of this call will check the state first
  with context.scopedOverride():

    context.access = context.kRead
    context.locale = FnAssetAPI.specifications.DocumentLocale()

    path = session.resolveIfReference(entityRef, context)

    # If we clear the script, then we'll still be in this process, so we can
    # tag it, otherwise, we fork and tag the old scipt not the one we opened.
    nuke.scriptClear()
    nuke.scriptOpen(path)

  # Store where we imported this from
  # We use the temp data as not to mess with the document state
  utils.storeTemporaryRootNodeData('entityReference', entityRef)

  return entityRef


def publishScript(entityRef, context=None, versionUp=False, tagScript=True):

  item = items.NukeScriptItem()
  try:
    item.path = nuke.scriptName()
  except RuntimeError:
    item.path = None

  specification = item.toSpecification()

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  # First we have to see what the management policy of the manager is
  policy = manager.managementPolicy(specification, context)
  if policy == FnAssetAPI.constants.kIgnored:
    raise RuntimeError("The current asset management system doesn't handle Nuke Scripts (%s)" % policy)

  managesPath = policy & FnAssetAPI.constants.kWillManagePath

  # We only need to save a new version if we're not using a path-managing asset
  # system.
  if versionUp and not managesPath:
    nukescripts.script_version_up()
    item.path = nuke.scriptName()

  if not context:
    context = session.createContext()

  entity = None

  with context.scopedOverride():

    context.access = context.kWrite
    context.locale = FnAssetAPI.specifications.DocumentLocale()
    if versionUp:
      context.locale.action = FnAssetAPI.constants.kDocumentAction_SaveNewVersion
    else:
      context.locale.action = FnAssetAPI.constants.kDocumentAction_Save

    with session.scopedActionGroup(context):

      entity = session.getEntity(entityRef, context, mustExist=False)

      # Switch on if its a tracking asset manager, or one that determines paths,
      if managesPath:
        entity = _writeScriptAsset(item, entity, context)
      else:
        entity = _publishScript(item, entity, context)

  if entity and tagScript:
    # We use the temp store as not to mess with the document state
    utils.storeTemporaryRootNodeData('entityReference', entity.reference)

  return entity.reference if entity else ''



@ensureManager
def _writeScriptAsset(item, entity, context):
  """
  Writes a script for asset managers that manage the path.
  """

  workingEntity = entity.preflightItem(item, context)

  workingPath = workingEntity.resolve()
  if not workingPath:
    raise RuntimeError("Entity failed to provide a working path %s" % entity)

  nuke.scriptSave(filename=workingPath)

  item.path = workingPath

  return workingEntity.registerItem(item, context)



@ensureManager
def _publishScript(item, entity, context):
  """
  Registers a script in-place for asset managers that don't manage paths.
  """

  ## @todo There is assorted peril here as this may be the same
  # file that is already being used by a previous version of an asset
  # but, if its not a path managing asset system, what can we do?

  return entity.registerItem(item, context)


