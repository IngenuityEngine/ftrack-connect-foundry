import functools

from .SessionManager import SessionManager


__all__ = ['ensureManager', 'ensureSession']


##
# @namespace python.decorators
# Provides some simple decorators that can reduce the boilerplate in Host code
#

def ensureManager(function):
  """

  Ensures that there is a current Session and the Session has a Manager
  configured before calling the wrapped function.

  @exception RuntimeError If any of the above assertions fail

  """
  @functools.wraps(function)
  def _ensureManager(*args, **kwargs):

    session = SessionManager.currentSession()

    if not session:
      raise RuntimeError("No Asset Management Session")

    if not session.currentManager():
      raise RuntimeError("No Asset Management Manager selected")

    return function(*args, **kwargs)

  return _ensureManager


def ensureSession(function):
  """

  Ensures that a Session has been started before the wrapped function is
  called.

  @exception RuntimeError If no Session has been started

  """

  @functools.wraps(function)
  def _ensureSession(*args, **kwargs):

    session = SessionManager.currentSession()
    if not session:
      raise RuntimeError("No Asset Management Session")

    return function(*args, **kwargs)

  return _ensureSession


