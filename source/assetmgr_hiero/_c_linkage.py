import FnAssetAPI
from FnAssetAPI.core.decorators import debugStaticCall
from FnAssetAPI.decorators import ensureManager

import hiero.core
import items
import specifications

# NOTE: Any additions here need to be manually imported in __init__.py

@ensureManager
def resolveIfEntityReference(location):
  """

  Called by Hiero's internals to resolve an entity reference to a file path.
  Not for general use! This may go away, consider it "internal" hiero code.

  @param location the location to resolve to a file path

  @return the resolved location (optionally including range as start-end after filename)

  """
  session = FnAssetAPI.SessionManager.currentSession()
  if session:

    # We don't know much about the context
    # It'll also be interesting to see the performance hit here.
    # Ultimately, we want contexts to be cheap to create.
    context = session.createContext()
    context.access = context.kRead

    resolved = session.resolveIfReference(location, context)
    if resolved != location:
      FnAssetAPI.logging.debug("_c_linkage._resolveIfEntityReference() resolved %r to %r" % (location, resolved))
      return resolved

  return location

@ensureManager
def isEntityReference(location):
  """

  Called by Hiero's internals to find out if a location is an entity reference.
  Not for general use! This may go away, consider it "internal" hiero code.

  @param location the location to check

  @return true if the location is an entity reference, false if not

  """
  session = FnAssetAPI.SessionManager.currentSession()
  if session:

    # We don't know much about the context
    # It'll also be interesting to see the performance hit here.
    # Ultimately, we want contexts to be cheap to create.
    context = session.createContext()
    context.access = context.kRead

    resolved = session.resolveIfReference(location, context)
    if resolved != location:
      return True

  return False

@ensureManager
@debugStaticCall
def setupAssetCallback(asset):
  """

  When an internal data model object is created from an asset managed entity reference,
  the object is created on the file given by _resolveIfEntityReference() but the asset
  management system may have additional metadata that needs to be pushed onto the object
  to override what Hiero set by default or read from the file.
  This callback is called by Hiero's internals after creating the object from the file,
  before returning the created object to whoever called for it to be created.

  @param asset the object that was created

  @return None
    
  @localeUsage hiero.specifications.HieroClipLocale
  @itemUsage hiero.items.HieroClipItem

  """
  entityRef = ''
  if hasattr(asset, 'entityReference'):
    entityRef = asset.entityReference()

  if not entityRef:
    return

  session = FnAssetAPI.SessionManager.currentSession()

  context = session.createContext()
  context.access = context.kRead
  context.retention = context.kPermanent

  if type(asset) is hiero.core.Clip:

    context.locale = specifications.HieroClipLocale()
    context.locale.objects = [asset,]

    manager = FnAssetAPI.SessionManager.currentManager()

    if manager.entityExists(entityRef, context):

      entity = manager.getEntity(entityRef, context)

      item = items.HieroClipItem(asset)
      item.setEntity(entity, read=True, context=context)
      item.updateClip()

      FnAssetAPI.logging.debug(("_c_linkage._setupAssetCallback() Updated clip"
         +" %s from metadata in '%s'") % (asset, entityRef))


def assetManagerIconFilePath():
  """

  Called by Hiero's internals to get the path to an icon to use when decorating
  asset managed entities.

  Note that Hiero will use a built-in default "tick mark" icon if an empty string is returned
  or if this function does not exist.

  Not for general use! This may go away, consider it "internal" hiero code.

  @return a string with the file path of the icon (typically .png) to use.

  """
  iconfile = ''
  manager = FnAssetAPI.SessionManager.currentManager()
  if manager:
    import os
    iconfile = manager.getInfo().get( FnAssetAPI.constants.kField_SmallIcon, "")
    if not iconfile or not os.path.exists(iconfile):
      iconfile = manager.getInfo().get(FnAssetAPI.constants.kField_Icon, "")
  return iconfile
