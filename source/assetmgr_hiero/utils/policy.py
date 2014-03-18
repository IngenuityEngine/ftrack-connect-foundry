import FnAssetAPI

from .. import specifications


def projectPolicy(forWrite=False, context=None, entityRef=None):
  """
  @specUsage FnAssetAPI.specifications.HieroProjectSpecification
  @localeUsage FnAssetAPI.specifications.DocumentLocale
  """
  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return FnAssetAPI.constants.kIgnored

  spec = specifications.HieroProjectSpecification()
  if not context:
    context = FnAssetAPI.SessionManager.currentSession().createContext()

  with context.scopedOverride():
    context.local = FnAssetAPI.specifications.DocumentLocale()
    context.access = context.kWrite if forWrite else context.kRead
    return manager.managementPolicy(spec, context, entityRef=entityRef)


def clipPolicy(forWrite=False, locale=None, entityRef=None, context=None):
  """
  @specUsage FnAssetAPI.specifications.ImageSpecification
  """
  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return FnAssetAPI.constants.kIgnored

  spec = FnAssetAPI.specifications.ImageSpecification()

  if not context:
    context = FnAssetAPI.SessionManager.currentSession().createContext()

  with context.scopedOverride():
    context.access = context.kWrite if forWrite else context.kRead

    if locale:
      context.local = locale

    return manager.managementPolicy(spec, context, entityRef=entityRef)


def shotPolicy(forWrite=False, entityRef=None, context=None):
  """
  @specUsage FnAssetAPI.specifications.ShotSpecification
  """
  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return FnAssetAPI.constants.kIgnored

  spec = FnAssetAPI.specifications.ShotSpecification()

  if not context:
    context = FnAssetAPI.SessionManager.currentSession().createContext()

  with context.scopedOverride():
    context.access = context.kWrite if forWrite else context.kRead
    return manager.managementPolicy(spec, context, entityRef=entityRef)


