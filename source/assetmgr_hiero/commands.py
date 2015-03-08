import FnAssetAPI
from FnAssetAPI.core.decorators import debugStaticCall
from FnAssetAPI.decorators import ensureManager
from FnAssetAPI.contextManagers import ScopedProgressManager

import hiero.core

from . import utils
from . import items

## @todo Verify policy in all relevant calls


@ensureManager
@debugStaticCall
def createShotsFromTrackItems(trackItems, targetEntity,
    adoptExistingShots=False, updateConflictingShots=False, context=None,
    trackItemOptions=None, linkToEntities=False, replaceTrackItemMeta=False,
    coalesseByName=True, batch=True):
  """

  This will create new Shots (via. a HieroShotTrackItem) in the current Asset
  Management System, under the supplied targetEntity.

  @param trackItems list, A list of hiero.core.TrackItems to create shots from.

  @param targetEnity Entity, An FnAssetAPI.Entity to create shots under

  @adoptExistingShots bool [False], If true, then any existing shots that match
  by name will be set in the HieroShotTrackItems returned by this call, for
  subsequent use. If false, then the only items associated with an Entity in
  the asset manager will be those used for newly created shots.

  @param updateConflictingShots bool [False], If True, then for shots
  in the asset system that match by name, but have different metadata, the
  properties of the corresponding TrackItem will be used to update the asset
  managed Entity.

  @param trackItemOptions dict {}, Options used when analysing the Hiero Track items
  (for example what timing method to use, etc...) \see
  utils.object.trackitemsToShotItems

  @param linkToEntities bool [False] If True, then each TrackItem will be
  linked to the resulting entity (new, or matched if adopeExistingShots is
  True).

  @param replaceTrackItemMeta bool [False] If True, and linkToEntities is also
  True, then when TrackItems are associated with Entites in the asset system,
  their metadata and timings will be updated to match too.

  @param coalesseByName bool [True] When enabled, TrackItems with identical names
  will be coalesced into a single shot in the asset system, with the union of
  the source TrackItem's timings. If False, multiple shots with the same name
  will be registered.

  @param batch bool [True] When set, will determine whether or not Hiero will
  use the batch version of FnAssetAPI calls to register assets when supported
  by the Manager.

  @return a list HieroShotTrackItems that were used to create the shots.

  """

  ## @todo Ensure only track items passed in?

  l = FnAssetAPI.l

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()
  if not manager:
    raise RuntimeError("No Asset Manager available")

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  # First check for duplicates
  duplicates = utils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    raise RuntimeError("Some supplied TrackItems have duplicate names (%s)" %
        ", ".join(duplicates))

  shotItems = utils.object.trackItemsToShotItems(trackItems, trackItemOptions,
      coalesseByName)

  new, existing, conflicting = utils.shot.analyzeHieroShotItems(shotItems,
      targetEntity, context=context, adopt=adoptExistingShots,
      checkForConflicts=updateConflictingShots)

  # See if we need to make thumbnails (but only for new shots)
  utils.thumbnail.setupThumbnails(new, context)

  with session.scopedActionGroup(context):

    if new:
      policy = manager.managementPolicy(new[0].toSpecification(), context)
      batch = batch and policy & FnAssetAPI.constants.kSupportsBatchOperations
      registration = utils.publishing.ItemRegistration(targetEntity, context, items=new)
      if batch:
        FnAssetAPI.logging.progress(0.5, l("Batch-{publishing} %d {shots}, please"
            +" wait...") % len(new))
        utils.publishing.registerBatch(registration, context)
        FnAssetAPI.logging.progress(1.0, "")
      else:
        utils.publishing.register(registration, session)
      if linkToEntities:
        # New Entities may have different names, etc... as they have been
        # conformed by the asset system so make sure this is re-applied to the
        # TrackItems.
        allEntites = [i.getEntity() for i in registration.items if i.getEntity()]
        manager.prefetch(allEntites, context)
        with context.scopedOverride():
          context.access = context.kReadMultiple
          with ScopedProgressManager(len(registration.items)) as progress:
            for i in registration.items:
              with progress.step("Checking for changes on %s" % i.nameHint):
                # The registration won't have re-read the entity, just associated it
                # So we need to read the data back from it, so that in the loop
                # below, it will update with the modified entity data
                i.readEntity(context)

    if conflicting and updateConflictingShots:
      utils.shot.updateEntitiesFromShotItems(conflicting, context)

  # Update the trackItems, as the ShotItems will now have an entity in them, so
  # we want to tag the track items with the entity ref, or timing changes etc...
  if linkToEntities:
    with ScopedProgressManager(len(shotItems)) as progress:
      for s in shotItems:
        # A misleading title, but it hopefully stops people getting upset that
        # were doing arguably pointless things here :)
        with progress.step("Cleaning up..."):
          ## @todo We might want to force this to off if there is more than one
          ## track item, and they dont share timings to start with.
          s.updateTrackItems(syncMeta=replaceTrackItemMeta)

  # shotItems will now have an entity in so this is a nice way of returning
  # that data in relation to the orig track items.
  return shotItems


@ensureManager
@debugStaticCall
def publishClipsFromHieroShotItems(shotItems, publishSharedClips=False,
    sharedClipTargetEntity=None, replaceClips=False, customClipName=None,
    omitAssetisedClips=True, context=None, batch=True):
  """
  Publishes the Clips that form the source media, for the hiero.core.TrackItems
  represented by the supplied HieroShotTrackItems. Note, they must have
  suitable entities set in them in order to publish clips.

  @param publishSharedClips bool [False], If the same source media is used by more
  than one TrackItem, should it still be published.

  @param sharedClipTargetEntity Entity [None], if publishSharedClips is True,
  this specifies the Entity to receive the source media.

  @param replaceClips bool [False] If True, and publishClips is True, then the
  source media for the TackItems will be replaced with a Clip that points to
  the newly published asset.

  @prarm context Context [None] A Context to use for this command, if None, a
  new one will be created. Note: the Context will be modified by the command.

  @param batch bool [True] When set, will determine whether or not Hiero will
  use the batch version of FnAssetAPI calls to register assets when supported
  by the Manager.

  @return The list of Entites created

  """
  if not shotItems:
    return []

  l = FnAssetAPI.l

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  registrations, sharedClipsRegistration = utils.shot.clipRegistrationsFromHieroShotItems(
        shotItems, context, publishSharedClips, sharedClipTargetEntity,
        customClipName, omitAssetisedClips)

  if sharedClipsRegistration:
    registrations.append(sharedClipsRegistration)

  allItems = []
  for r in registrations:
    allItems.extend(r.items)
  # See if we need to make thumbs
  utils.thumbnail.setupThumbnails(allItems, context)

  if not allItems:
    return []

  with session.scopedActionGroup(context):
    policy = manager.managementPolicy(allItems[0].toSpecification(), context)
    batch = batch and policy & FnAssetAPI.constants.kSupportsBatchOperations
    if batch:
      numItems = len(registrations) + len(sharedClipsRegistration.items)
      FnAssetAPI.logging.progress(0.5,
          l("Batch-{publishing} %d Clips, please wait...") % numItems)
      utils.publishing.registerBatch(registrations, context)
      FnAssetAPI.logging.progress(1.0, "")
    else:
      utils.publishing.register(registrations)

  hieroClipItems = []

  for r in registrations:
    hieroClipItems.extend(r.items)

  if replaceClips and hieroClipItems:
    for i in hieroClipItems:
      i.updateClip()

  return hieroClipItems


@ensureManager
@debugStaticCall
def publishClips(clips, targetEntity, context=None, omitAssetisedClips=True,
    batch=True):
  """

  This will publish the supplied hiero.core.Clip objects to new assets under
  the supplied targetEntity.

  @param batch bool [True] When set, will determine whether or not Hiero will
  use the batch version of FnAssetAPI calls to register assets when supported
  by the Manager.

  """

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple if len(clips) > 1 else context.kWrite

  clipItems = utils.object.clipsToHieroClipItems(clips)

  if omitAssetisedClips:
    clipItems = filter(lambda i: not i.getEntity(), clipItems)

  if not clipItems:
    return clipItems

  policy = manager.managementPolicy(clipItems[0].toSpecification(), context)
  batch = batch and policy & FnAssetAPI.constants.kSupportsBatchOperations

  utils.thumbnail.setupThumbnails(clipItems, context)

  registration = utils.publishing.ItemRegistration(targetEntity, context)
  registration.items = clipItems

  l = FnAssetAPI.l

  with session.scopedActionGroup(context):
    if batch:
      FnAssetAPI.logging.progress(0.5, l("Batch-{publishing} %d Clips, please"
            +" wait...") % len(clipItems))
      utils.publishing.registerBatch(registration, context)
      FnAssetAPI.logging.progress(1.0, "")
    else:
      utils.publishing.register(registration)

  return clipItems



@ensureManager
@debugStaticCall
def importClips(entityReferences, target=None, context=None):
  """

  Creates Clips that reference media in the supplied entity references.

  @param target Bin [None], If specified, Clips will be created under the
  specified Bin, otherwise at the to level of the Project.

  @itemUsage hiero.items.HieroClipItem

  """
  if not entityReferences:
    return

  if not target:
    target = hiero.core.projects()[-1].clipsBin()

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return

  if not context:
    context = session.createContext()

  with session.scopedActionGroup(context):

    context.access = context.kReadMultiple
    context.retention = context.kPermanent

    clips = []

    for r in entityReferences:

      entity = session.getEntity(r, context, mustExist=True)
      clipItem = items.HieroClipItem()
      clipItem.setEntity(entity, read=True, context=context)

      try:
        hieroClip = clipItem.toClip()
      except FnAssetAPI.exceptions.BaseException as e:
        FnAssetAPI.logging.error(e)
        continue

      if not hieroClip:
        FnAssetAPI.logging.error("Unable to retrieve a hiero.core.Clip for the "
            +"asset %s" % clipItem)
        continue

      clips.append(hieroClip)

      target.addItem(hiero.core.BinItem(hieroClip))

    return clips



@ensureManager
@debugStaticCall
def publishProjects(projects, targetEntity, context=None, batch=True):
  """

  @localeUsage FnAssetAPI.specifications.DocumentLocale

  @param batch bool [True] When set, will determine whether or not Hiero will
  use the batch version of FnAssetAPI calls to register assets when supported
  by the Manager.

  """

  l = FnAssetAPI.l

  projects = utils.ensureList(projects)

  policy = utils.policy.projectPolicy()
  if policy == FnAssetAPI.constants.kIgnored:
    raise RuntimeError("The Asset Management System doesn't manage projects")

  batch = batch and policy & FnAssetAPI.constants.kSupportsBatchOperations

  session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  with session.scopedActionGroup(context):

    context.access = context.kWriteMultiple if len(projects) > 1 else context.kWrite
    context.locale = FnAssetAPI.specifications.DocumentLocale()
    ## @TODO implement the appropriate action, once we have a sensible way
    ## to determine whether this is 'new version' or 'save'.

    projectItems = []

    for p in projects:
      ## @todo Should we prompt here? And only if its dirty...
      ## @todo We don't need the save right here if it's path managed since
      ## createAsset() takes care of that.
      # Make sure the project on disk is up to date
      p.save()
      item = items.HieroProjectItem(p)
      projectItems.append(item)

    if policy & FnAssetAPI.constants.kWillManagePath:
      # We set the callback to None as HieroProjectItems implement createAsset
      task = utils.publishing.ItemCreation(targetEntity, None, context)
    else:
      task = utils.publishing.ItemRegistration(targetEntity, context)
    task.items = projectItems
    if batch and len(projects) > 1:
      FnAssetAPI.logging.progress(0.5, l("Batch-{publishing} %d Projects, please"
            +" wait...") % len(projects))
      utils.publishing.processBatch(task, context, session=session)
      FnAssetAPI.logging.progress(1.0, "")
    else:
      utils.publishing.process(task, session)

    # Store the entity refs back on the project
    for i in projectItems:
      i.updateProject()

    return projectItems


@ensureManager
@debugStaticCall
def openPublishedProject(entityRef, lock=False, context=None):
  """

  @localeUsage FnAssetAPI.specifications.DocumentLocale

  """
  session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  with session.scopedActionGroup(context):
    with context.scopedOverride():

      context.access = context.kRead
      context.retention = context.kPermanent
      context.locale = FnAssetAPI.specifications.DocumentLocale()

      entity = session.getEntity(entityRef, context, mustExist=True)

      ## @todo ideally we'd just be able to pass the reference to the project
      path = entity.resolve(context)

  project = hiero.core.openProject(path)

  if project:

    # Make sure we track the original entity ref
    # We use the temp asset tag as it doesn't mess with the document state
    utils.tag.setTemporaryAssetTagField(project, 'entityReference', entity.reference)

    if lock:
      project.setEditable(False)

  return project



