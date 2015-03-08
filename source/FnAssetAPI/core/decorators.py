import functools
import inspect
import os

from .Timer import Timer

from .. import logging


__all__ = ['debugCall', 'debugApiCall', 'debugStaticCall']


## @class decorators
## Assorted decorators to help with API development. For the sake of
## optimisation, and help(fn) still making sense, then they may be disabled by
## default.
##
## @envvar **FOUNDRY_ASSET_API_DEBUG** *int* [1] when non-zero, debug decorators
## will be enabled, allowing API calls to be monitored and timed using the
## kDebug and kDebugAPI logging severity displays

enableDebugDecorators = os.environ.get("FOUNDRY_ASSET_API_DEBUG", "1") != "0"


def debugCall(function):
  """

  Use as a decorator to trace usage of the decorated function though the kDebug
  logging severity. This should only be used on bound methods.

  @see debugStaticCall

  """

  # Early out if we're not enabled
  if not enableDebugDecorators:
    return function

  # Because some of our decorators get chained, let see if we have the
  # original function, otherwise we just log the decorator, which is
  # useful to neither man nor beast (only our decorators bother to set this).
  debugFn = function
  if hasattr(function, 'func_wrapped'):
    debugFn = function.func_wrapped

  @functools.wraps(function)
  def _debugCall(*args, **kwargs):
    return __debugCall(function, debugFn, logging.kDebug, *args, **kwargs)

  # Ensure the docstring is updated so the help() messages are meaningful,
  # otherwise, we obscure the signature of the underlying function
  params = inspect.formatargspec(*inspect.getargspec(debugFn))
  sig = "(Debug) %s%s" % (debugFn.__name__,  params)
  d = function.__doc__
  _debugCall.__doc__ = "%s\n%s" % (sig, d) if d else sig

  return _debugCall


def debugApiCall(function):

  # See notes in debugCall

  # Early out if we're not enabled
  if not enableDebugDecorators:
    return function

  debugFn = function
  if hasattr(function, 'func_wrapped'):
    debugFn = function.func_wrapped

  @functools.wraps(function)
  def _debugApiCall(*args, **kwargs):
    return __debugCall(function, debugFn, logging.kDebugAPI, *args, **kwargs)

  params = inspect.formatargspec(*inspect.getargspec(debugFn))
  sig = "(DebugAPI) %s%s" % (debugFn.__name__,  params)
  d = function.__doc__
  _debugApiCall.__doc__ = "%s\n%s" % (sig, d) if d else sig

  return _debugApiCall



def debugStaticCall(function):
  """

  An alternate decorator only for use with static calls that consequently have
  no special first argument (self or cls).

  @see debugCall

  """

  # See notes in debugCall

  debugFn = function
  if hasattr(function, 'func_wrapped'):
    debugFn = function.func_wrapped

  @functools.wraps(function)
  def _debugStaticCall(*args, **kwargs):

    if logging.displaySeverity >= logging.kDebug:

      allArgs = [repr(a) for a in args]
      allArgs.extend(["%s=%r" % (k,v) for k,v in kwargs.iteritems()])

      msg = "-> %s( %s )" % (
          debugFn.__name__, ", ".join(allArgs))
      logging.debug(msg)

      result = "<exception>"
      try:
        with Timer() as timer:
          result = function(*args, **kwargs)
      finally:
        msg = "<- %s [%s] %r" % (debugFn.__name__,
            timer, result)
        logging.debug(msg)

      return result

    else:
      return function(*args, **kwargs)

  params = inspect.formatargspec(*inspect.getargspec(debugFn))
  sig = "(Debug) %s%s" % (debugFn.__name__,  params)
  _debugStaticCall.__doc__ = "%s\n%s" % (sig, debugFn.__doc__) if debugFn.__doc__ else sig

  return _debugStaticCall if enableDebugDecorators else function



def __debugCall(function, traceFn, severity, self, *args, **kwargs):

    # function and traceFn are provided so that when the function is wrapped,
    # traceFn is printed to the log, but function (usually the wrapper) is
    # still executed.

    # Debugging can be disabled on-the-fly if the object has a _debugCalls
    # attribute who's value casts to False
    enabled = self._debugCalls if hasattr(self, '_debugCalls') else True
    if enabled and logging.displaySeverity >= severity:

      allArgs = [repr(a) for a in args]
      allArgs.extend(["%s=%r" % (k,v) for k,v in kwargs.iteritems()])

      msg = "-> %x %r.%s( %s )" % (
          id(self), self, traceFn.__name__, ", ".join(allArgs))
      logging.log(msg, severity)

      result = "<exception>"
      try:
        with Timer() as timer:
          result = function(self, *args, **kwargs)
      finally:
        msg = "<- %x %r.%s [%s] %r" % (id(self), self, traceFn.__name__,
            timer, result)
        logging.log(msg, severity)

      return result

    else:
      return function(self, *args, **kwargs)




