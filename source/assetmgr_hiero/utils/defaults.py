import hiero.core

import FnAssetAPI
from FnAssetAPI.core.decorators import debugStaticCall

from . import _utils
from . import entity as entityUtils
from . import tag as tagUtils

from .. import constants


kTrackItemTimingOptionsKey = "trackItemTimingsOptions"


def managerSpecificKey(key):
  """
  Produces a manager-localised key for persistent options, etc..
  """
  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return key

  identifier = manager.getIdentifier()
  # Hiero doesn't seem to like dots in tag names
  safeIdentifier = identifier.replace(".", "-")

  localizedKey = "%s_%s" % (key, safeIdentifier)
  return localizedKey


@debugStaticCall
def getDefaultParentEntityForProjects(projects, context):

  if not projects:
    return None

  projects = _utils.ensureList(projects)

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return None

  manager = session.currentManager()
  if not manager:
    return

  try:

    # 1) Check the last used parent (stored on the somewhere randomly in memory
    # so we don't dirty the document state)
    field = constants.kHieroField_defaultProjectParent
    ref = tagUtils.getTemporaryAssetTagField(projects[0], field, None)
    if ref:
      return session.getEntity(ref, context)

    # 2) Look on our projects to see if any have been published already
    # or if there are any entities in the project
    parent = entityUtils.getFirstParentOfSomeEntity(projects, context)
    if parent:
      return parent

    # 3) Ask the Asset Manager if it has any opinion
    with context.scopedOverride():
      context.access = context.kWriteMultiple
      spec = FnAssetAPI.specifications.HieroProjectSpecification()
      entity = manager.getDefaultEntity(spec, context)
      if entity:
        return entity

  except Exception as e:
    FnAssetAPI.logging.debug("Exception trying to find default parent "+
        "entity for Project: %s" % e)

  return None


@debugStaticCall
def setDefaultParentEntityForProjects(entity, projects):

  for p in projects:
    ref = entity.reference
    field = constants.kHieroField_defaultProjectParent
    tagUtils.setTemporaryAssetTagField(p, field, ref)


@debugStaticCall
def getDefaultParentEntityForClips(objs, context):

  if not objs:
    return None

  objs = _utils.ensureList(objs)

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return None

  manager = session.currentManager()
  if not manager:
    return

  try:

    # 1) Check the last used parent (stored on the project)
    project = objs[0].project() if hasattr(objs[0], 'project') else None
    sequence = objs[0].parentSequence() if hasattr(objs[0], 'parentSequence') else None
    for o in (sequence, project):
      if o:
        field = constants.kHieroField_defaultClipParent
        ref = tagUtils.getAssetTagField(o, field, None)
        if ref:
          return session.getEntity(ref, context)

    # 2) Look for some entity that we know about (prob a clip or a project)
    parent = entityUtils.getFirstParentOfSomeEntity(objs, context)
    if parent:
      return parent

    # 3) Finally ask the Asset Manager if it has any opinion
    with context.scopedOverride():
      context.access = context.kWriteMultiple
      spec = FnAssetAPI.specifications.ImageSpecification()
      entity = manager.getDefaultEntity(spec, context)
      if entity:
        return entity

  except Exception as e:
    FnAssetAPI.logging.debug("Exception trying to find default parent "+
        "entity for Clips: %s" % e)

  return None


@debugStaticCall
def setDefaultParentEntityForClips(entity, objs):

  if not objs:
    return

  objs = _utils.ensureList(objs)

  targetObj = None
  if hasattr(objs[0], 'parentSequence'):
    targetObj = objs[0].parentSequence()
  else:
    targetObj = objs[0].project() if hasattr(objs[0], 'project') else None
  if targetObj:
    ref = entity.reference
    field = constants.kHieroField_defaultClipParent
    tagUtils.setAssetTagField(targetObj, field, ref)


@debugStaticCall
def getDefaultParentEntityForShots(trackItemsOrSeq, context):

  if not trackItemsOrSeq:
    return None

  trackItems = _utils.ensureList(trackItemsOrSeq)

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return None

  manager = session.currentManager()
  if not manager:
    return

  try:

    # 1) Check the last used parent (stored on a sequence)
    sequence = trackItems[0]
    if isinstance(sequence, hiero.core.TrackItem):
      sequence = sequence.parentSequence()
    if sequence:
      field = constants.kHieroField_defaultShotParent
      ref = tagUtils.getAssetTagField(sequence, field, None)
      if ref:
        return session.getEntity(ref, context)

    # 2) Try and find a parent based on any entities in the selection
    shot = None
    relationship = FnAssetAPI.specifications.ParentGroupingRelationship()

    shotEntities = entityUtils.entitiesFromObjs(trackItems, sparse=False)
    if shotEntities:
      shot = shotEntities[0]

    if not shot:
      # see if we have any clip entities, and get a parent of one of them
      # This is not necessarily a 'shot' (but does it matter?)
      clipEntities = entityUtils.someEntitiesFromObjs(trackItems,
          includeChildren=True, includeParents=False, sparse=False)

      if clipEntities:
        # We need an additional query for grouping parent here as we want the
        # parent of the *shot* the clip is in not the parent of the clip.
        shots = clipEntities[0].getRelatedEntities([relationship,], context)[0]
        if shots:
          shot = shots[0]

    if shot:
      # For now, we'll be lazy and get the parent of the first shot
      parents = shot.getRelatedEntities([relationship,], context)[0]
      if parents:
        return parents[0]

    # 3) Finally see if the manager has any opinion
    with context.scopedOverride():
      context.access = context.kWrite
      spec = FnAssetAPI.specifications.ShotSpecification()
      entity = manager.getDefaultEntity(spec, context)
      if entity:
        return entity

  except Exception as e:
    FnAssetAPI.logging.debug("Exception trying to find default parent "+
        "entity for Clips: %s" % e)

  return None


@debugStaticCall
def setDefaultParentEntityForShots(entity, trackItemsOrSeq):

  if not trackItemsOrSeq:
    return

  trackItems = _utils.ensureList(trackItemsOrSeq)

  sequence = trackItems[0]
  if isinstance(sequence, hiero.core.TrackItem):
    sequence = sequence.parentSequence()

  if sequence:
    ref = entity.reference
    field = constants.kHieroField_defaultShotParent
    tagUtils.setAssetTagField(sequence, field, ref)



@debugStaticCall
def setDefaultsInObjTag(obj, key, options):
  """
  Stores the supplied options in a tag on the object using the supplied key.
  """

  tagName = "%s_%s" % (tagUtils.kAssetTag, key)
  tag = tagUtils.getNamedTag(obj, tagName, create=True)
  if not tag:
    return

  data = tag.metadata()
  if not data.readOnly():
    for k,v in options.items():
      # Hiero presently only supports string data
      data.setValue(k, repr(v))


@debugStaticCall
def getDefaultsFromObjTag(obj, key):

  opts = {}

  tagName = "%s_%s" % (tagUtils.kAssetTag, key)
  tag = tagUtils.getNamedTag(obj, tagName)
  if not tag:
    return opts

  data = tag.metadata()
  for k,v in data.dict().items():
    # Hiero adds its own metadata
    if k.startswith('tag.'): continue
    # Hiero only supports string data so we repr'd on the way in
    try:
      opts[k] = eval(v)
    except NameError:
      # It was a string, and its lost its quotes...
      opts[k] = v

  return opts


