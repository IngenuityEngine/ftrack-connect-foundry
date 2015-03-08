import FnAssetAPI
from FnAssetAPI.decorators import ensureManager

import hiero.core

from _utils import ensureList

from . import object as objectUtils
from . import tag as tagUtils


def entityFromObj(obj):

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return None

  ref = None
  entity = None

  if hasattr(obj, 'entityReference'):
    ref = obj.entityReference()

  else:
    ref = tagUtils.getAssetTagField('entityReference', None)

  if ref:
    entity = session.getEntity(ref, mustBeValid=True)

  return entity


def entitiesFromObjs(objs, sparse=True):

  entities = []
  for o in objs:
    entity = entityFromObj(o)
    if entity or sparse:
      entities.append(entity)
  return entities


def someEntitiesFromObjs(objs, includeChildren=True, includeParents=False,
    sparse=True):

  entities = []
  for o in objs:
    entity = anEntityFromObj(o, includeChildren, includeParents)
    if entity or sparse:
      entities.append(entity)
  return entities


def anEntityFromObj(obj, includeChildren=True, includeParents=False):

  """

  Attempts to get some entity that relates to the object, it could be a child
  or a parent, there is no guarantee of the relationship.

  @param includeChildren Bool, if True, entities will be search for underneath
  the object, if the object has no entity. Children are searched before
  parents if both options are True.

  @param includeParents bool, if True, enities will be searched for on parents
  of the object if the object has no entity. Parents are searched after
  children if both options are True.

  """

  entity = entityFromObj(obj)

  # If requested, look at children of the object if needed
  if not entity and includeChildren:

    while obj and not entity:

      if isinstance(obj, hiero.core.TrackBase):
        entity = anEntityFromTrack(obj)
        obj = None

      elif isinstance(obj, hiero.core.BinItem) or isinstance(obj, hiero.core.Bin):
        entity = anEntityFromBin(obj)
        obj = None

      elif isinstance(obj, hiero.core.Project):
        obj = obj.clipsBin()

      elif isinstance(obj, hiero.core.TrackItem):
        obj = objectUtils.clipFromTrackItem(obj)

      else:
        obj = None

      if obj:
        entity = entityFromObj(obj)


  # If requested, look at ancestors of the object if needed
  if not entity and includeParents:

    while obj and not entity:

      # Lets assume a Clip is the deepest unit we will have
      if isinstance(obj, hiero.core.SequenceBase):
        obj = obj.project()
      elif isinstance(obj, hiero.core.TrackItem):
        obj = obj.parent()
      elif isinstance(obj, hiero.core.TrackBase):
        obj = obj.parent()
      else:
        obj = None

      if obj:
        entity = entityFromObj(obj)

  return entity


def getFirstParentOfSomeEntity(objs, context, includeParents=True,
    includeChildren=True):

  objs = ensureList(objs)

  entities = someEntitiesFromObjs(objs, includeParents=True,
      includeChildren=True, sparse=False)

  if entities:
    relationship = FnAssetAPI.specifications.ParentGroupingRelationship()
    parents = entities[0].getRelatedEntities([relationship,], context)[0]
    return parents[0] if parents else None


def anEntityFromTrack(track):

  trackItems = track.items()
  for t in trackItems:
    clip = objectUtils.clipFromTrackItem(t)
    entity = entityFromObj(clip)
    if entity: return entity

  return None



def anEntityFromBin(binOrBinItem):

  ## @todo This will need updating if we ever put refs on bins

  binItems = []
  objectUtils.getAllBinItems(binOrBinItem, binItems)
  clips = objectUtils.binItemsToObjs(binItems, hiero.core.Clip)

  for c in clips:
    entity = entityFromObj(c)
    if entity: return entity

  return None


@ensureManager
def getParentGroupings(objs, context):

  refs = []
  relationship = FnAssetAPI.specifications.ParentGroupingRelationship()

  # Because there might not be an entity for any supplied obj, and we can't
  # pass 'None' as an entity to the refs call we need to keep track of where
  # the results will be

  ## @todo This is a common pattern, and perhaps should be abstracted in the
  ## Manager layer?

  indexMap = {}

  i = 0
  for o in objs:
    entity = getParentGrouping(objs[i])
    if entity:
      refs.append(entity.reference)
      indexMap[o] = i
      i += 1

  manager = FnAssetAPI.SessionManager.currentManager()

  # This should be guaranteed to be the same length as refs by the impl
  groupings = manager.getRelatedEntities(refs, relationship, context, asRefs=True)

  parents = []
  for o in objs:
    index = indexMap.get(o, None)
    groups = groupings[index] if index is not None else []
    parents.append(groups[0] if groups else None)

  # We want entities back, the manager calls return refs
  toEntity = lambda r: manager.getEntity(r, context)
  parents = map(toEntity, parents)

  return parents


def getParentGrouping(obj, context):

  entity = anEntityFromObj(obj, includeChildren=True, includeParents=True)
  if not entity:
    return None

  relationship = FnAssetAPI.specifications.ParentGroupingRelationship()
  groupings = entity.getRelatedEntities([relationship,], context)

  if not groupings:
    return None

  # This should only ever be one, so lets quietly ignore any others for now
  return groupings[0][0] if groupings[0] else None


