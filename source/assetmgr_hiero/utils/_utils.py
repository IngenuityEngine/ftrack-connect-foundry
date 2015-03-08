import traceback
import types

import FnAssetAPI

## This package is for small snippets that don't belong in any of the other
## categories.

## @name Decorators
## @{

def logExceptions(function):
  """

  A decorator that will catch exceptions, and log them as critical severity
  errors through the FnAssetAPI.logging module. This can be useful for
  outer-level functions that should always provide meaningful feedback to the
  user, rather than just raising.

  The critical severity of the logged message ensures that it will be
  presented as a blocking, modal alert.

  @see HieroHost.log

  """

  def _logExceptions(*args, **kwargs):
    try:
      return function(*args, **kwargs)
    except Exception as e:
      # If its the 'UserCanceled' exception, we can silently eat it.
      if isinstance(e, FnAssetAPI.exceptions.UserCanceled):
        return None
      if FnAssetAPI.logging.displaySeverity == FnAssetAPI.logging.kDebugAPI:
        traceback.print_exc()
      FnAssetAPI.logging.critical(e)
      return None

  return _logExceptions

## @}


## @name Misc
## @{

def ensureList(itemOrList):
  """

  Ensures that the supplied object is a list. If it is, it its passed through.
  If it is not a list or a tuple, it is wrapped in a list.

  """
  if isinstance(itemOrList, (types.ListType, types.TupleType)):
    return itemOrList
  else:
    return [itemOrList,]


def listHasItems(listOfLists):
  """

  Some of the batched calls return lists of lists. This means that a return
  value of [ [], [], [], ], say from @ref
  python.Manager.getRelatedEntities, is hard to easily detect using a
  boolean cast, as the outer list is not empty. This function checks that some
  item in the outer list casts to True.

  @return False if all elements of the list cast to False, else True

  """
  if not listOfLists:
    return False
  haveSomething = False
  for l in listOfLists:
    if l:
      haveSomething = True
      break
  return haveSomething

## @}

