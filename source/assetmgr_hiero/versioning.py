import FnAssetAPI
import utils

from FnAssetAPI.core.decorators import debugStaticCall

from items import HieroClipItem
from specifications import HieroBinLocale

import hiero.core

## @todo When we have the 'inputString/path' thing in Hiero, we'll need to look
## at how to implement the other functions that used to be overridden in
## FnVersioning.py


def registerOverrides():

  from hiero.core.VersionScanner import VersionScanner

  if not hasattr(VersionScanner, '_default_findVersionFiles'):
    VersionScanner._default_findVersionFiles = VersionScanner.findVersionFiles
    VersionScanner.findVersionFiles = findVersionFiles

  if not hasattr(VersionScanner, '_default_filterVersion'):
    VersionScanner._default_filterVersion = VersionScanner.filterVersion
    VersionScanner.filterVersion = filterVersion

  if not hasattr(VersionScanner, '_default_createClip'):
    VersionScanner._default_createClip = VersionScanner.createClip
    VersionScanner.createClip = createClip

  if not hasattr(VersionScanner, '_default_insertClips'):
    VersionScanner._default_insertClips = VersionScanner.insertClips
    VersionScanner.insertClips = insertClips

  VersionScanner._entityVersions = []


def findVersionFiles(scannerInstance, version):
  """
  @localeUsage hiero.specifications.HieroBinLocale
  """
  session = FnAssetAPI.SessionManager.currentSession(requireManager=True)
  if not session:
    return scannerInstance._default_findVersionFiles(version)

  clip = version.item()

  entity = utils.entity.entityFromObj(clip)
  if not entity:
    return scannerInstance._default_findVersionFiles(version)

  context = session.createContext()
  context.access = context.kRead
  # Is this really permanent, I think the version items get kept around right?
  context.retention = context.kPermanent
  context.locale = HieroBinLocale()
  context.locale.objects = [version,]

  # Versions is a dict of keys as names, and values are references
  versions = entity.getVersions(context, includeMetaVersions=True, asRefs=True, asList=True)
  # We need this later
  scannerInstance._entityVersions = versions

  hieroOrderedVersions = versions[::-1]

  # Prune out any we already have
  binitem = version.parent()
  filteredRefs = filter(lambda v : scannerInstance.filterVersion(binitem, v),
      hieroOrderedVersions)

  return filteredRefs

@debugStaticCall
def filterVersion(scannerInstance, binitem, newVersionFile):

  manager = FnAssetAPI.SessionManager.currentManager()
  if manager and manager.isEntityReference(newVersionFile):

    # We have to see if anything else in the bin has this ref
    for version in binitem.items():
      item = version.item()
      if item and hasattr(item, 'entityReference'):
        if item.entityReference() == newVersionFile:
          return False

    return True

  else:
    return scannerInstance._default_filterVersion(binitem, newVersionFile)


## @todo This should just be in standard hiero when it makes a media
## source/clip from an entity reference. but presently the Hiero code makes a
## media source, not a clip
def createClip(scannerInstance, newFilename):

  manager = FnAssetAPI.SessionManager.currentManager()

  if manager and manager.isEntityReference(newFilename):
    return hiero.core.Clip(newFilename)
  else:
    return scannerInstance._default_createClip(newFilename)


def insertClips(scannerInstance, binItem, clips):

  entities = []
  nonEntities = []

  newVersions = []

  for c in clips:
    if hasattr(c, 'entityReference') and c.entityReference():
      entities.append(c)
    else:
      nonEntities.append(c)

  newVersions.extend(scannerInstance._default_insertClips(binItem, nonEntities))

  # We're going to insert the entity based clips at the end
  for c in entities:
    v = utils.bin.addClipAsVersion(c, binItem, scannerInstance._entityVersions)
    newVersions.append(v)

  # I don't think we need this any more, so lets not keep it around
  scannerInstance._entityVersions = []

  return newVersions













