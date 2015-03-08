import os

##
# @class logging
# The logging module should be used for all logging within API. It will be
# mapped back to the most appropriate display mechanism for the current Host.
#
# @envvar **FOUNDRY_ASSET_LOGGING_SEVERITY** *int* The default logging
# severity - this will may be reset by a Host, but this can be useful to allow
# inspection of the initialisation of the @ref python.ManagerFactory, etc...

##
# @name Log Severity
# @{

kDebugAPI = 6
kDebug = 5
kInfo = 4
kProgress = 3
kWarning = 2
kError = 1
kCritical = 0

## A mapping of severity levels to readable labels
kSeverityNames = [ 'critical', 'error', 'warning', 'progress', 'info',
  'debug', 'debugAPI']

## @}

##
# @name Logging Host
# If this points to an object that implements log(msg, severity), then it will
# all logging will be relayed there instead of stdout.
logHost = None


## @name Display Severity
# Messages logged with a severity greater or equal to this will be displayed.
displaySeverity = kWarning

if "FOUNDRY_ASSET_LOGGING_SEVERITY" in os.environ:
  try:
    displaySeverity = int(os.environ["FOUNDRY_ASSET_LOGGING_SEVERITY"])
  except ValueError:
    pass

##
# @name Logging (unrelated to licensed forestry)
# @{

def log(message, severity):
  """

  Logs the message to @ref logHost if specified, otherwise stdout/stderr.

  @param message str, A UTF-8 ASCII string.

  @param severity int, One of the FnAssetAPI.logging log severity constants

  """
  if severity > displaySeverity:
    return

  if logHost and hasattr(logHost, 'log'):
    logHost.log(message, severity)
  else:
    _log(message, severity)


def progress(decimalProgress, message=""):
  """

  Logs the supplied progress to @ref logHost if specified otherwise
  stdout/stderr. If the logHost doesn't implement progress, it will be sent
  through the standard log call with kProgress severity.

  @param decimalProgress float, Normalised progress between 0 and 1, if set to
  a value less than 0 it will be considered cancelled, if greater than one,
  complete.

  @param message str, A UTF-8 ASCII string message to display with the
  progress. If None is supplied, it is assumed that there is no message and the
  previous message may remain. Set to an empty string if it is desired to
  always clear the previous message.

  @return bool, True if progress has been cancelled since the last call.

  @exception python.exceptions.UserCanceled If supported by the logging host,
  then the UserCanceled exception may be raised if the user pro-actively cancels
  an action whilst it is still in progress.

  """
  if logHost and hasattr(logHost, 'progress'):
    return logHost.progress(decimalProgress, message)
  else:
    return _progress(decimalProgress, message)


def _log(message, severity, color=True, noRemap=False):
  """

  A utility logging function to log to sys.stderr/stdout. This may be called by
  Hosts etc... if they wish to simply customise the standard API logging
  coloration and remapping handling.

  @param message str, A UTF-8 ASCII string.

  @param severity int, One of the FnAssetAPI.logging log severity constants

  @param color bool [True] Make a vague attempt to colour the output using
  terminal escape codes.

  @param noRemp bool [False] Some applications remap the std outputs. When set,
  logging will attempt to write to the 'real' sys.stderr and sys.stdout instead
  of the remapped outputs. If these have been closed, it will fall back to the
  remapped outputs.

  """
  severityStr = "[%s]" % kSeverityNames[severity]
  msg = "%11s: %s\n" % (severityStr, message)
  import sys
  try:
    if severity < kWarning:
      o = sys.__stderr__ if noRemap else sys.stderr
      o.write(__colorMsg(msg, severity) if color else msg)
    else:
      o = sys.__stdout__ if noRemap else sys.stdout
      o.write(__colorMsg(msg, severity) if color else msg)
  except IOError as e:
    # In some occasions, the real std outs may have been closed (for example in
    # osx somewhere, when an app is launched in the GUI and uses something like
    # py2app. So, we try to fall back on the facaded outs instead.
    if noRemap:
      _log(message, severity, color=color, noRemap=False)
    else:
      raise e


def _progress(decimalProgress, message):
  """

  A convenience for logging progress messages with a percentage display.

  @param decimalProgress float, A progress measure normalized between 0 and 1

  """
  msg = "%3d%% %s" % (int(100*decimalProgress),
      message if message is not None else "")
  log(msg, kProgress)
  return False


def __colorMsg(msg, severity):

  end = '\033[0m'
  color = '\033[0;3%dm'

  if severity == kDebug:
    return "%s%s%s" % ( color % 2, msg, end )
  if severity == kDebugAPI:
    return "%s%s%s" % ( color % 6, msg, end )
  if severity == kWarning:
    return "%s%s%s" % ( color % 3, msg, end )
  if severity < kWarning:
    return "%s%s%s" % ( color % 1, msg, end )

  return msg


## @}

##
# @name Convenience
# Calls that map to standard python logging names for convenience.
# @{

def debug(message):
  """

  Shorthand for logging a message with kDebug severity.

  """
  log(message, kDebug)


def info(message):
  """

  Shorthand for logging a message with kInfo severity.

  """
  log(message, kInfo)


def warning(message):
  """

  Shorthand for logging a message with kWarning severity.

  """
  log(message, kWarning)


def error(message):
  """

  Shorthand for logging a message with kError severity.

  """
  log(message, kError)


def exception(message):
  """

  Shorthand for logging a message with kError severity.

  """
  log(message, kError)


def critical(message):
  """

  Shorthand for logging a message with kCritical severity.

  """
  log(message, kCritical)

## @}

