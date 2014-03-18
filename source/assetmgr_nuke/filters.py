import FnAssetAPI
import nuke

def assetAPIFilenameValidator(filenameOrRef):

  ## @todo This doesn't work at present as it gets called with the
  ## filtered (ie: resolved) file name, rather than the reference

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return True

  manager = session.currentManager()
  if not manager:
    return True

  if not manager.isEntityReference(filenameOrRef):
    return True

  context = session.createContext()
  context.access = context.kWrite
  try:
    # Resolve the entity, and check it returns some string
    resolved = manager.resolveEntityReference(filenameOrRef, context)
    FnAssetAPI.logging.debug("validateFilename resolved %r to %r" % (filenameOrRef, resolved))
    return bool(resolved)
  except FnAssetAPI.exceptions.BaseEntityException as e:
    # If the manager excepts, then we probably shouldn't be writing
    # to this entity.
    FnAssetAPI.logging.warning("That Asset cannot be written to - %s" % e)
    return False


# Nuke will call the filenameFilter *a lot*.
# For now, we use a persistent resolve context so that a manager can have some
# sensible scope to cache resolves in per-nuke, should it so desire.
__persistentResolveContext = None

def assetAPIFilenameFilter(filenameOrRef):

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    return filenameOrRef

  manager = session.currentManager()
  if not manager or not manager.isEntityReference(filenameOrRef):
    return filenameOrRef

  global __persistentResolveContext
  if not __persistentResolveContext:
    # Sadly, we don't know much about the context at present, we make this
    # persistent so the manager has a suitable scope for caching
    # resolves if it wishes
    context = session.createContext()
    context.access = context.kOther
    __persistentResolveContext = context

  resolved = filenameOrRef

  try:
    resolved = manager.resolveEntityReference(filenameOrRef,
        __persistentResolveContext)

    # We have to fix up the frame expansion ourselves, as otherwise, Nuke
    # thinks its un-changing, and doesn't update with time. Fortunately we just
    # have to handle the sprintf case, as # is not supported in the AssetAPI.
    if '%' in resolved:
      resolved = resolved % nuke.frame()

    FnAssetAPI.logging.debug("filenameFilter resolved %r to %r" % (filenameOrRef, resolved))

  except FnAssetAPI.exceptions.BaseEntityException as e:
    FnAssetAPI.logging.warning("Failed to resolve '%r' - %s" % (filenameOrRef, e))

  return resolved

