## This file contains several utilities to simplify the publishing of assets.
## As we always endeavour to separate out UI code and processing code, to
## simplify scripting and batch operations, it can be useful to have all
## pre-processing functions to create a 'work list', and then a headless
## function to perform the actual work.
## Then dialogs an build, and display the resulting work list, without actually
## performing any actions. This allows UIs to give meaningful feedback on what
## will really happen, as options are changed.

## @todo Promote to core API?
## @todo Now we have batch registration some of this needs a little rethink

import FnAssetAPI
from FnAssetAPI.exceptions import UserCanceled

import types


class DummyContextManager(object):
  def __enter__(self, *args, **kwargs): pass
  def __exit__(self, *args, **kwargs): pass


class ItemRegistration(object):
  """

  This class can be used to store a list of registrations that need to be made
  to to the asset manager.

   Once passed to assetUtils.register() then the 'entities' property will be
   a list of corresponding entities from the asset manager.

  @param targetEntity Entity, The entity that will register the item(s)

  @param context Context, The context to be used for any registrations

  @param items list, [optional] An initial list of Item classes that need to be
  registered.

  """

  def __init__(self, targetEntity, context, items=None):
    super(ItemRegistration, self).__init__

    self.targetEntity = targetEntity
    self.context = context
    self.items = items if items else []


def register(itemRegistrations, session=None, skipRegistrationErrors=False,
    allowContextOverrides=True):
  """

  Register one or more ItemRegistration objects.

  @param itemRegistrations list object, A list, of single ItemRegistration
  object.

  @param progressCallback callable, If not none, will be called to update
  progress. The value will be normalised to be between 0 and 1, regardless of
  the number of items, it will be called with the progress value, and the Item
  that is being registered.

  """
  _go(itemRegistrations, _register_workFn, "Registering %s", session,
      skipRegistrationErrors, allowContextOverrides)



class ItemCreation(object):
  """

  This class can be used to store a list of preflight+registrations that need
  to be made to to the asset manager

   Once passed to assetUtils.preflight() then the 'entities' property will be
   a list of corresponding entities from the asset manager.

  @param targetEntity Entity, The entity that will register the item(s)

  @param callback callable, The work function, that will be called with each
  Item, and respective preflight entity, after preflight, and before
  postflight. It is expected that this callback will return an item that can be
  passed to registerItem. If no callback is specified, and the item has a
  'createAsset' function, then that will be called instead.

  @param context Context, The context to be used for any registrations

  @param items list, [optional] An initial list of item classes that need to be
  registered.

  """

  def __init__(self, targetEntity, callback, context, items=None):
    super(ItemCreation, self).__init__

    self.callback = callback
    self.targetEntity = targetEntity
    self.context = context
    self.items = items if items else []
    self.entities = []


def create(itemCreations, session=None, skipRegistrationErrors=False,
    allowContextOverrides=True):
  """

  Register one or more ItemCreation objects.

  @param itemCreation list object, A list, of single ItemCreation objects.

  @param progressCallback callable, If not none, will be called to update
  progress. The value will be normalised to be between 0 and 1, regardless of
  the number of items, it will be called with the progress value, and the Item
  that is being registered.

  """
  _go(itemCreations, _create_workFn, "Creating %s", session,
      skipRegistrationErrors, allowContextOverrides)



def process(mixed, session=None, skipRegistrationErrors=False,
    allowContextOverrides=True):
  """

  Calls create or register on the supplied list of tasks.

  @param mixed list, A list of ItemCreations or ItemRegistrations to be
  processed.

  """
  if not isinstance(mixed, types.ListType):
    mixed = [mixed, ]

    for i in mixed:
      if isinstance(i, ItemCreation):
        create(i, session, skipRegistrationErrors, allowContextOverrides)
      elif isinstance(i, ItemRegistration):
        register(i, session, skipRegistrationErrors, allowContextOverrides)
      else:
        raise RuntimeError("Unknown item %s" % i)


def processBatch(mixed, context, manager=None, session=None):

  if not isinstance(mixed, types.ListType):
    mixed = [mixed, ]

  creations = []
  registrations = []
  for i in mixed:
    if isinstance(i, ItemCreation):
      creations.append(i)
    elif isinstance(i, ItemRegistration):
      registrations.append(i)
    else:
      raise RuntimeError("Unknown item %s" % i)

  if creations:
    createBatch(creations, context, manager, session)
  if registrations:
    registerBatch(registrations, context, manager, session)



def _register_workFn(item, task):
  return task.targetEntity.registerItem(item, task.context)


def _create_workFn(item, task):
  workingEntity = task.targetEntity.preflightItem(item, task.context)
  if task.callback:
    workingItem = task.callback(item, workingEntity)
  elif hasattr(item, 'createAsset'):
    workingItem = item.createAsset(workingEntity, task.context)
  return workingEntity.registerItem(workingItem, task.context)



def _go(workList, workFn, message, session=None, skipRegistrationErrors=False,
    allowContextOverrides=True):
  """

  Register one or more ItemCreation objects.

  @param itemCreation list object, A list, of single ItemCreation objects.

  @param progressCallback callable, If not none, will be called to update
  progress. The value will be normalised to be between 0 and 1, regardless of
  the number of items, it will be called with the progress value, and the Item
  that is being registered.

  """

  if not isinstance(workList, types.ListType):
    workList = [workList, ]

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  # Calculate our progress normalisation
  numItems = 0
  for i in workList:
    numItems += len(i.items)
  numItems = float(numItems)
  thisItem = 0

  for task in workList:

    # Make sure we wrap an action group around the context if multiple items
    itemCount = len(task.items)
    with session.scopedActionGroup(task.context) if itemCount > 1 \
        else DummyContextManager():

      for item in task.items:

        thisItem += 1
        p = thisItem/numItems
        msg = message % item.getString()
        cancelled = FnAssetAPI.logging.progress(p, msg)
        if cancelled:
          raise UserCanceled

        # Allow the Item to override the locale for the context
        # This is to avoid having to clone a context, as that is BAD (as the
        # managerState should not be copied)
        customLocale = None
        if allowContextOverrides:
          if hasattr(item, 'toLocale'):
            customLocale = item.toLocale()
          contextLocale = task.context.locale
          if customLocale:
            task.context.locale = customLocale

        try:
          entity = workFn(item, task)
          item.setEntity(entity)
        except FnAssetAPI.exceptions.BaseEntityInteractionError, e:
          if skipRegistrationErrors:
            FnAssetAPI.logging.warning(e)
            continue
          else:
            FnAssetAPI.logging.progress(-1)
            raise

        finally:
          # Make sure we restore the context locale if we changed it
          if customLocale:
            task.context.locale = contextLocale


def publishBatch(workList, context, manager=None, session=None):

  # For now, this assumes that they're all of the same spec, so we only need to
  # check the policy once. It gets *very* boring otherwise

  if not isinstance(workList, types.ListType):
    workList = [workList, ]

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  if not manager:
    manager = session.currentManager()

  refItem = workList[0].items[0] if workList[0].items else None
  refSpec = refItem.toSpecification()
  if not refSpec:
    raise FnAssetAPI.exceptions.RegistrationError("Unable to determine the "
      +"Specification for the Items to be published (%s)" % refItem)

  with context.scopedOverride():

    context.access = context.kWriteMultiple

    managementPolicy = manager.managementPolicy(refSpec, context)

    if managementPolicy == FnAssetAPI.constants.kIgnored:
      raise FnAssetAPI.exceptions.RegistrationError(("The current Asset "+
          "Manager does not manage Assets of type %s in this context.")
          % refSpec.getType())

    if managementPolicy & FnAssetAPI.constants.kWillManagePath:
      fn = createBatch
    else:
      fn = registerBatch

    with session.scopedActionGroup(context):
      return fn(workList, context, manager, session)



def createBatch(workList, context, manager=None, session=None):

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  if not manager:
    manager = session.currentManager()

  if not isinstance(workList, types.ListType):
    workList = [workList, ]

  specs = []
  targets = []

  for task in workList:
    for i in task.items:
      specs.append(i.toSpecification())
      targets.append(task.targetEntity.reference)

  with session.scopedActionGroup(context):

    workingRefs = manager.preflightMultiple(targets, specs, context)

    strings = []

    for task in workList:
      for i in task.items:
        strings.append(i.getString())

    finalRefs = manager.registerMultiple(strings, workingRefs, specs, context)

  finalEntities = [FnAssetAPI.Entity(r, manager) if r else None for r in finalRefs]
  index = 0
  for task in workList:
    for i in task.items:
      i.setEntity(finalEntities[index])
      index += 1



def registerBatch(workList, context, manager=None, session=None):

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  if not manager:
    manager = session.currentManager()

  if not isinstance(workList, types.ListType):
    workList = [workList, ]

  strings = []
  specs = []
  targets = []

  for task in workList:
    for i in task.items:
      strings.append(i.getString())
      specs.append(i.toSpecification())
      targets.append(task.targetEntity.reference)

  with session.scopedActionGroup(context):
    finalRefs = manager.registerMultiple(strings, targets, specs, context)

  finalEntities = [FnAssetAPI.Entity(r, manager) if r else None for r in finalRefs]
  index = 0
  for task in workList:
    for i in task.items:
      i.setEntity(finalEntities[index])
      index += 1



def publishSingle(workFn, specification, targetEntity, context=None, session=None):

  """
  A helper function to call workFn for a single asset with the correct file
  path. None will be passed if it's not a path managing asset system, so it
  needs to know where to put it in that case.
  """

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  with context.scopedOverride():
    with session.scopedActionGroup(context):

      context.access = context.kWrite

      # Determine the management policy for the entity
      managementPolicy = session.currentManager().managementPolicy(
        specification, context, entityRef=targetEntity.reference)

      if managementPolicy == FnAssetAPI.constants.kIgnored:
        raise FnAssetAPI.exceptions.RegistrationError(("The current Asset "+
            "Manager does not manage Assets of type %s in this context.")
            % specification.getType(), targetEntity.reference)

      if managementPolicy & FnAssetAPI.constants.kWillManagePath:
        fn = createSingle
      else:
        fn = registerSingle

      return fn(workFn, specification, targetEntity, context)


def registerSingle(workFn, specification, targetEntity, context):

  path = workFn(None)
  if not path:
    raise FnAssetAPI.exceptions.RegistrationError("No path returned by the registration function %s"
        % workFn, targetEntity.reference)
  return targetEntity.register(path, specification, context)


def createSingle(workFn, specification, targetEntity, context):

  workingEntity = targetEntity.preflight(specification, context)

  workingPath = workingEntity.resolve()
  if not workingPath:
    raise RuntimeError("Entity failed to provide a working path %s" % targetEntity)

  workingPath = workFn(workingPath)

  finalEntity = workingEntity.register(workingPath, specification, context)
  return finalEntity

