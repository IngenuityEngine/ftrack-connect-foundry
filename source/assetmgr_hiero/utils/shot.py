import FnAssetAPI
from FnAssetAPI.contextManagers import ScopedProgressManager

import hiero.core

from . import publishing as publishingUtils
from . import entity as entityUtils
from . import object as objectUtils
from . import defaults as defaultsUtils


def analyzeHieroShotItems(hieroShotItems, parentEntity, context=None,
    adopt=False, checkForConflicts=True):
  """
  @param adopt bool [False] if True, then any existing, matching shots will be
  set as the entity in the corresponding ShotItem.
  """

  # We're looking for:
  #   - new shots
  newShots = []
  #   - existing shots
  existingShots = []
  #   - existing shots with different timings
  conflictingShots = []

  if not parentEntity:
    return hieroShotItems, [], []

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    raise RuntimeError("No Asset Management session is available")

  manager = session.currentManager()
  if not manager:
    raise RuntimeError("No Asset Management system is available")

  if not context:
    context = session.createContext()

  # Set the context to read
  context.access = context.kRead

  # Ensure the target parent entity exists, if it doesn't, this might not be an
  # issue, ans the parent entity ref may be speculative in some systems and
  # it'll be happy creating it on the fly....
  if not parentEntity.exists(context):
    FnAssetAPI.logging.debug("analyzeHieroShotItems: Skipping check for "+
        "existing shots under %s as it doesn't exist (yet)." % parentEntity)
    return hieroShotItems, [], []

  existingEntities = checkForExistingShotEntities(hieroShotItems, parentEntity, context)
  # Warn the manager we're about to do a bunch of lookups
  entities = [e for e in existingEntities if e]
  if entities:
    manager.prefetch(entities, context)

  if not existingEntities:
    return hieroShotItems, [], []

  with ScopedProgressManager(len(hieroShotItems)) as progress:

    for s,e in zip(hieroShotItems, existingEntities):

      if checkForConflicts:
        progress.startStep("Checking timings for '%s'" % s.code)

      if not e:
        newShots.append(s)
      elif checkForConflicts and checkForForConflict(s, e, context):
        conflictingShots.append(s)
        if adopt:
          s.setEntity(e)
      else:
        existingShots.append(s)
        if adopt:
          s.setEntity(e)

      if checkForConflicts:
        progress.finishStep()

  return newShots, existingShots, conflictingShots


def entitiesFromTrackItems(trackItems, context=None, searchClips=False,
    parentEntity=None):
  """

  Converts the supplied trackItems in to a non-sparse list of Entities.

  @param searchClips bool [False] If True, then the TrackItem's clips will
  first be searched for an entity reference. This takes prescience over looking
  up the track item by name under a parent Entity. This is usually the desired
  behaviour for example, to allow info on a specific version to be shown,
  rather than just the shot as a whole.

  @param parentEntity FnAssetAPI.Entity If supplied TrackItems will be matched
  by name against shots under this Entity. If this is None, Hiero will attempt
  to find a default entity using the last used shot parent \see
  utils.defaults.getDefaultParentEntityForShots. If no parent Entity can be
  found, this check will be silently ommitted

  @return list [FnAssetAPI.Entity] A non-sparse list of Entities or None, the
  same length as the supplied list of TrackItems.

  """

  entities = [None] * len(trackItems)

  # If we're searching clips, they take precedence, so first look for
  # entities based on them
  if searchClips:
    for i in range(len(trackItems)):
      entity = None
      c = objectUtils.clipFromTrackItem(trackItems[i])
      if c is not None:
        entity = entityUtils.anEntityFromObj(c)
      entities[i] = entity

  # If we can find a parent then we can look for a matching shot under that
  if not parentEntity:
    parentEntity = defaultsUtils.getDefaultParentEntityForShots(
      trackItems, context)

  # Make sure we actually have some un-mapped TrackItems - entities is always
  # len(trackItems) but may have None values.
  if parentEntity and [ True for e in entities if e is None ]:
    ## @todo This could be more efficient if we filtered out trackitems we
    ## already have matched to a clip. Revisit if it becomes a notable slowdown.
    shotItems = objectUtils.trackItemsToShotItems(trackItems)
    shotEntities = entitiesFromShotItems(shotItems, parentEntity, context)
    # Fill in any blanks in the entities list
    entities = [ s if (s and e is None) else e for e,s in zip(entities, shotEntities) ]

  return entities



def entitiesFromShotItems(shotItems, asShotsUnderEntity=None, context=None):
  """

  Finds entity references, if possible from the supplied shotItmes, the return
  array will be the same length as the supplied shotItems, so some items may be
  None if no valid entity was found. If a supplied shotItem has more than one
  entity, its value will be a list.

  \pram asShotsUnder Entity, an entity that should be considered a parent for
  shots. If supplied any clips in the items will be ignored and the items will
  be matched as shots under the supplied entity.

  """
  entities = []

  if asShotsUnderEntity:

    ## Look for shots that match under the supplied parent

    newShots, existingShots, conflictingShots = analyzeHieroShotItems(
        shotItems, asShotsUnderEntity, context, adopt=True,
        checkForConflicts=False)

    for s in shotItems:

      entity = None
      if s and s in existingShots:
        entity = s.getEntity()

      entities.append(entity)

  else:

    # See if we have managed clips in the shots
    for s in shotItems:

      itemEntities = []
      if s:
        clips = clipsFromHieroShotTrackItem(s)
        for c in clips:
          clipEntity = entityUtils.entityFromObj(c)
          if clipEntity:
            itemEntities.append(clipEntity)

      if itemEntities:
        entities.append(itemEntities[0] if len(itemEntities)==1 else itemEntities)
      else:
        entities.append(None)

  return entities


def getRelatedRefrencesForManagedHieroShotTrackItems(shotItems,
    relationshipSpecification, asShotsUnderEntity=None, context=None,
    resultSpec=None):
  """
  @specUsage FnAssetAPI.specifications.ImageSpecification

  """

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()

  entities = entitiesFromShotItems(shotItems,
        asShotsUnderEntity=asShotsUnderEntity, context=context)

  if not entities:
    return []

  # 'entities' is now an list of either an applicable entityRefrence or
  # None for each item. We need a list of entity refrences to ask the
  # Manager to remap using the relationship criteria. There may be some
  # 'None' entities (if they werent managed) so, we also make an
  # abbreviated list of only the items that can be remapped. In this list
  # they then have the same index as in their related reference in the
  # list returned from getRelatedReferences.

  entityRefs = []
  assetisedItems = []

  for e, i in zip(entities, shotItems):
    if e:
      entityRefs.append(e.reference)
      assetisedItems.append(i)

  if not entityRefs:
    raise RuntimeError("No matching assets found to build a track from.")

  if not context:
    context = session.createContext()

  context.access = context.kReadMultiple

  if not resultSpec:
    resultSpec = FnAssetAPI.specifications.ImageSpecification()

  # relatedRefs is a list, with a list of relations for each entity (in this case)
  relatedRefs = manager.getRelatedEntities(entityRefs,
      relationshipSpecification, context, resultSpec=resultSpec, asRefs=True)

  perItemDict = {}
  for item, refs in zip(assetisedItems, relatedRefs):

    if not refs: continue

    # (There should always be one as we made these items from trackItems)
    newRef = refs[0]

    if len(refs) != 1:
      FnAssetAPI.logging.info("Multiple referenced returned to build track"
          +" from for %s, using '%s'" % (item, newRef) )

    perItemDict[item] = newRef

  # Re-build an array of refs, except for all incoming shotitems, not just
  # the ones with entities.
  allItemRefs = []
  for i in shotItems:
    allItemRefs.append(perItemDict.get(i, None))
  return allItemRefs




def updateEntitiesFromShotItems(shotItems, context):

  oldLocale = context.locale
  context.access = context.kWriteMultiple

  with FnAssetAPI.SessionManager.currentSession().scopedActionGroup(context):
    with ScopedProgressManager(len(shotItems)) as progress:
      for s in shotItems:
        with progress.step("Updating '%s'" % s.code):
          if s.getEntity():
            s.updateEntity(context)

  context.locale = oldLocale


def checkForExistingShotEntities(shotItems, parentEntity, context):
  """

  Returns a list existing entities that match the supplied HieroShotTrackItems.

  @return A list, where each element correlates to the input shot item with the
  same index.

  @specUsage FnAssetAPI.specifications.ShotSpecification

  """

  specs = [s.toSpecification() for s in shotItems]

  existingShots = []

  # This call can take a single specification, or an array of specicfications
  # If its an array, then it will return an array of arrays
  resultSpec = FnAssetAPI.specifications.ShotSpecification()

  existing = parentEntity.getRelatedEntities(specs, context, resultSpec=resultSpec)
  if existing:

    i = 0
    for shotEntities in existing:

      existingShot = None
      if shotEntities:
        existingShot = shotEntities[0]

      if len(shotEntities) > 1:
        FnAssetAPI.warning(("Multiple matching related entity for %s under %s,"
          +" using the first one (%s)") % (shotItems[i], parentEntity, existingShot))

      existingShots.append(existingShot)

      i += 1

  return existingShots


def checkForForConflict(shotItem, shotEntity, context):
  """
  @itemUsage hiero.items.HieroShotTrackItem
  """
  from ..items import HieroShotTrackItem

  with context.scopedOverride():

    context.locale = shotItem.toLocale()
    existingItem = HieroShotTrackItem()
    existingItem.setEntity(shotEntity, read=True, context=context)

  if existingItem.inFrame != shotItem.inFrame:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot inFrame: %r != %r" %
        (shotItem.code, existingItem.inFrame, shotItem.inFrame))
    return True

  if existingItem.outFrame != shotItem.outFrame:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot outFrame %r != %r" %
        (shotItem.code, existingItem.outFrame, shotItem.outFrame))
    return True

  if existingItem.startFrame != shotItem.startFrame:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot startFrame %r != %r" %
        (shotItem.code, existingItem.startFrame, shotItem.startFrame))
    return True

  if existingItem.endFrame != shotItem.endFrame:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot endFrame %r != %r" %
        (shotItem.code, existingItem.endFrame, shotItem.endFrame))
    return True

  if existingItem.inTimecode != shotItem.inTimecode:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot inTimecode %r != %r" %
        (shotItem.code, existingItem.inTimecode, shotItem.inTimecode))
    return True

  if existingItem.sourceTimecode != shotItem.sourceTimecode:
    FnAssetAPI.logging.debug("Shot conflict for %s: Existing shot sourceTimecode %r != %r" %
        (shotItem.code, existingItem.sourceTimecode, shotItem.sourceTimecode))
    return True

  return False


def analyzeHeiroShotItemClips(hieroShotItems, asItems=False):
  """
  @itemUsage hiero.items.HieroClipItem
  """
  from ..items import HieroClipItem

  clips = set()
  sharedClips = set()
  trackItems = {}

  clipItems = []
  sharedItems = []

  for s in hieroShotItems:
    itemClips = clipsFromHieroShotTrackItem(s)
    for c in itemClips:
      trackItems[c] = s
      if not c: continue
      if c in sharedClips: continue
      if c in clips:
        sharedClips.add(c)
        clips.remove(c)
      else:
        clips.add(c)

  if asItems:

    # Turn them into items, and set the track items, if applicable
    for c in clips:
      item = HieroClipItem(c)
      clipItems.append(item)

    for c in sharedClips:
      item = HieroClipItem(c)
      sharedItems.append(item)

    return clipItems, sharedItems

  else:

    return clips, sharedClips


# Creates ItemRegistrations for each source clip of the supplied
# HieroShotTrackItems, see publishClipsFromHieroShotTackItems for
# parameter documentation
def clipRegistrationsFromHieroShotItems(hieroShotItems, context, publishSharedClips,
    sharedClipTargetEntity, customClipName=None, omitAssetisedClips=True):
  """
  @itemUsage hiero.items.HieroClipItem
  """
  from ..items import HieroClipItem

  # This will hold an ItemRegistration for each shot
  shotRegistrations = []
  # This will hold a single ItemRegistration to the shared target entity, # if set
  otherRegistration = None

  # Pre-process shots to see if there are any shared clips
  uniqueClips, sharedClips = analyzeHeiroShotItemClips(hieroShotItems, asItems=False)

  publishedClips = set()

  for s in hieroShotItems:

    shotEntity = s.getEntity()
    if not shotEntity:
      FnAssetAPI.logging.debug("No Enitity found for ShotItem with code %s" % s.code)
      continue

    clips = clipsFromHieroShotTrackItem(s)
    if not clips:
      FnAssetAPI.logging.debug("No Clips found for ShotItem with code %s" % s.code)
      continue

    registration = publishingUtils.ItemRegistration(shotEntity, context)

    for clip in clips:

      shared = clip in sharedClips

      if shared and not publishSharedClips:
        FnAssetAPI.logging.debug(("Skipping media publish for Shot %s as it's Clip "
          +"is shared with another Shot") % s.code)
        continue

      hieroClipItem = HieroClipItem(clip)
      if omitAssetisedClips and hieroClipItem.getEntity():
        FnAssetAPI.logging.debug("Skipping %s as it is already published" % clip)
        continue

      if shared and sharedClipTargetEntity:

        # If its shared, we might have seen it before
        if clip in publishedClips:
          FnAssetAPI.logging.debug("Already created registration for %s, skipping..." % clip)
          continue

        # If it is shared, register it under the specified target entity
        if not otherRegistration:
          otherRegistration = publishingUtils.ItemRegistration(sharedClipTargetEntity, context)

        otherRegistration.items.append(hieroClipItem)
        publishedClips.add(clip)

      elif shared:
        FnAssetAPI.logging.warning("Publishing shared Clips to shots is not currently supported")
        continue

      else:

        #  Register it under the shotEntity

        # If we have a custom name, override the name hint as long as there is
        # only one clip in this shot
        if customClipName and len(clips)==1:
          hieroClipItem.nameHint = customClipName

        registration.items.append(hieroClipItem)

    if registration.items:
      shotRegistrations.append(registration)

  return shotRegistrations, otherRegistration


def clipsFromHieroShotTrackItem(item):
  trackItems = item.getTrackItems()
  if not trackItems:
    raise RuntimeError("Unable to determine the TrackItems from %s" % item)
  sources = []
  sourcesSet = set()
  for t in trackItems:
    source = t.source()
    ## @todo When will this return a MediaSource?
    if isinstance(source, hiero.core.Clip):
      if source not in sourcesSet:
        sources.append(source)
        sourcesSet.add(source)
  return sources


