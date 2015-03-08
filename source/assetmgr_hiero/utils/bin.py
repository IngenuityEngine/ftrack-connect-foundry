import FnAssetAPI
from FnAssetAPI.decorators import ensureManager

import hiero.core

from .. import specifications
from . import entity as entityUtils


@ensureManager
def findOrCreateClipInBin(entityRef, bin, context=None, session=None):
  """

  Takes the supplied @ref entity_reference and searches the contents of the
  supplied bin. If any Bin Item holds a clip with the entity reference as an
  existing Version, that clip will be returned instead.

  If no existing clips match the reference, then a new clip will be created and
  configured to reference that Entity.

  @return hiero.core.Clip The resultant new or matching clip.

  """

  # First look for an existing clip in the bin
  for binItem in bin.clips():
    matches = findVersionsMatchingRefs([entityRef,], binItem)
    if matches:
      return matches[0]

  # If we can't find one, make one

  if not session:
    session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()
    context.access = context.kRead

  entity = session.getEntity(entityRef, context)
  # We don't need to use a HieroClipItem here as hiero understands entity
  # references when constructing a clip
  clip = hiero.core.Clip(entityRef)
  # This ensures that its added under the right version if applicable
  addClipToBinOrVersion(clip, bin, entity, context)

  return clip


@ensureManager
def addClipToBinOrVersion(clip, parentBin, entity=None, context=None):
  """

  If the supplied clip is another version of an existing ProjectItem within the
  parentBin, then it will be added as a new Version accordingly.
  If it is a 'new' clip, then it will be added to the supplied parentBin.

  @param entity FnAssetAPI.Entity, The Entity that the clip has been created
  from. If this is not supplied, attempts will be made to recover the entity
  from the clip. If one can't be found, it will just add the clip to parentBin.

  @localeUsage hiero.specifications.HieroBinLocale

  """

  if not context:
    context = FnAssetAPI.SessionManager.currentSession().createContext()

  if not entity:
    entity = entityUtils.entityFromObj(clip)

  existingClip = None

  if entity:
    with context.scopedOverride():

      context.retention = context.kTransient
      context.access = context.kRead
      context.locale = specifications.HieroBinLocale()

      otherVersions = entity.getVersions(context, asRefs=True, asList=True)


      # See if any of the clips in the parent bin use
      for binItem in parentBin.clips():
        matches = findVersionsMatchingRefs(otherVersions, binItem)
        if matches:
          existingClip = matches[0]
          break

  if existingClip:
    binItem = existingClip.binItem()
    addClipAsVersion(clip, binItem, otherVersions)
  else:
    parentBin.addItem(hiero.core.BinItem(clip))


def addClipAsVersion(clip, binItem, entityVersionsList):
  """

  Adds the supplied clip to the supplied bin item as a new Version. It takes
  care that the clip is placed at the right index in the bin so that versions
  are correctly sorted. This is done by comparing all other Versions already
  present to the supplied entityVersionList to determine the correct index.

  @param entityVersionsList list, This should be a sorted list of the entity
  references for every version of the entity the clip is representing. Such a
  list can be retrieved from Entity.getVersions(asRefs=True, asList=True)

  @return hiero.core.Version, the newly created Version object

  """

  ref = clip.entityReference()

  # see which our index is
  versionIndex = entityVersionsList.index(ref)
  targetBinIndex = -1

  # Try to find the closed version that already exists in the bin
  binIndex = 0
  for v in binItem.items():

    c = v.item()
    if not c or not hasattr(c, 'entityReference'):
      continue

    ref = c.entityReference()
    try:
      clipIndex = entityVersionsList.index(ref)
      if clipIndex >= versionIndex:
        targetBinIndex = binIndex
        break
    except:
      pass

    binIndex += 1

  version = hiero.core.Version(clip)
  binItem.addVersion(version, targetBinIndex)
  return version


def findVersionsMatchingRefs(entityRefs, binItem):
  """

  Finds Clips under a BinItem that represent the supplied list of entity refs.

  @param binItem hiero.core.BinItem, The BinItem that holds a number of
  Versions. The function only looks at the immediate items of the binItem, and
  does not recurse in the case of a binItem holding a bin.

  @return list of hiero.core.Clips that match, in order of the suppied refs.
  Note, the return is not sparse.

  """

  matches = []

  for version in binItem.items():
    clip = version.item()
    if clip and hasattr(clip, 'entityReference'):
      ## @todo Stop once we've found all of them?
      if clip.entityReference() in entityRefs:
        matches.append(clip)

  return matches




