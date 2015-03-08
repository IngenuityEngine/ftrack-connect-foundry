import types
import functools
import os


__all__ = ['auditor', 'auditCall', 'auditApiCall', 'auditCalls', 'captureArgs',
    'reprArgs']


##
# @namespace python.audit
# This module permits auditing of the use of the various API calls during a
# series of oparations.
# @envvar **FOUNDRY_ASSET_API_AUDIT** *int* [0] If non-zero API calls will be
# audited by default
# @envvar **FOUNDRY_ASSET_API_AUDIT_ARGS** *int* [0] If non-zero args will be
# captured during audit, if auditing is disabled, this has no effect.

## Will hold the singleton Auditor object
__auditor = None

## When set to True, decorated calls will be audited. When False, minimal
## additional code is run, to minimise performance impact. This should always
## be False by default.
auditCalls = os.environ.get('FOUNDRY_ASSET_API_AUDIT', "0") != "0"

## If True, the args for each invocation of a function will be recorded, to
## aide debugging
captureArgs = os.environ.get('FOUNDRY_ASSET_API_AUDIT_ARGS', "0") != "0"

## Some hosts have issues with us holding onto objects. Setting this to True
## will ensure that we repr the objects whilst they are still alive.
reprArgs = False


def auditor():
  """

  Returns a singleton Auditor, created on demand.

  @see python.core.Auditor

  """
  global __auditor
  if not __auditor:
    from .core.Auditor import Auditor
    __auditor = Auditor()
  return __auditor


## @name Decorators
## @{

def auditCall(function):
  """

  A decorator to log a method, as long as auditCalls is True, with no other
  special logic.

  """
  @functools.wraps(function)
  def _auditCall(self, *args, **kwargs):

    if auditCalls:

      a = auditor()

      arg = __prepareArgs(args, kwargs)
      a.addMethod(function, arg=arg)

    return function(self, *args, **kwargs)

  # Store the original function on the method for other decorators
  _auditCall.func_wrapped = function

  return _auditCall if auditCalls else function


def auditApiCall(group=None, static=False):
  """

  A decorator to log a method as long as auditCalls is True, parsing the
  methods args and kwargs with an understanding of the various objects used in
  the FnAssetAPI. This of this as being analogous to 'statefull packet
  inspection'.

  If auditCalls is False, functions will not be wrapped so docstrings are not
  obfuscated and the call stack isn't bloated. Because wrapping happens when
  the Class is parsed, for auditing to ever be enabled, it has to be set by the
  environment variable so that it's true before other classes are loaded from
  their modules. Otherwise, its too late to turn it on once the import has
  completed.

  @param group str, an optional group name to log the call under @ref
  python.core.Auditor.Auditor.addMethod

  """
  def _wrapAuditApiCall(function):

    # We deliberately don't wrap the function if its disabled as it
    # a) obfuscates docstrings
    # b) adds unnecessarily to the call stack
    if not auditCalls:
      return function

    @functools.wraps(function)
    def _auditApiCall(*args, **kwargs):

      if auditCalls:
        a = auditor()

        instance = None
        if not static and args:
          instance = args[0]

        arg = __prepareArgs(args if static else args[1:], kwargs)
        a.addMethod(function, obj=instance, group=group, arg=arg)

        for arg in args:
          __auditObj(a, arg)
        for arg in kwargs.values():
          __auditObj(a, arg)

      return function(*args, **kwargs)

    # Store the original function on the method for other decorators
    _auditApiCall.func_wrapped = function

    return _auditApiCall

  return _wrapAuditApiCall


## @}


def __auditObj(a, obj):
  """

  Performs additional auditing of the supplied argument, including inspection
  of lists/dicts, and the various properties of a Context.

  @param a Auditor, The Auditor to receive data

  """

  # Here to prevent cyclic dependencies
  from . import specifications
  from . import items
  from . import Context

  # Look inside sequence types / dicts
  if isinstance(obj, (types.ListType, types.TupleType)):
    for o in obj:
      __auditObj(a, o)
    return

  elif isinstance(obj, dict):
    for o in obj.values():
      __auditObj(a, o)
    return

  if isinstance(obj, specifications.Specification):
    # If its a spec, just add the spec class
    a.addClass(obj, group="Specifications")

  elif isinstance(obj, Context):
    # If its a Context, add the context, and its options
    a.addClass(obj)
    a.addObj('Context.%s' % obj.access, group="Context Access")
    a.addObj('Context.%s' % obj.kRetentionNames[obj.retention],
        group="Context Retention")
    if obj.locale:
      a.addClass(obj.locale, group="Locales")

  elif isinstance(obj, items.Item):
    a.addClass(obj)


def __prepareArgs(args, kwargs):

  arg = None

  if captureArgs and (args or kwargs):
    arg = (args, kwargs)
    if reprArgs:
      arg = repr(arg)

  return arg

