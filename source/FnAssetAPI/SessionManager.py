from .Session import Session

from .audit import auditApiCall


__all__ = ['SessionManager']


class SessionManager(object):
  """

  A @ref Host facing convenience class to simplify a Hosts interactions with a
  @ref Manager. It is intended to be used as a singleton manager of the
  associated state, and @ref Manager instances within any single interaction
  session.

  It takes care of the following upon initialization:
   @li Connecting a Host's logging into the @ref python.logging mechanism (if
   the host has a 'log' function).
   @li Instantiating and configuring a @ref python.ManagerFactory

  """

  _instance = None
  _sessionClass = Session

  @classmethod
  @auditApiCall("Session")
  def startSession(cls, host, makeCurrent=True):
    """

    Constructs a new SessionManager, and stores it as a singleton. Any further
    calls to @ref currentSession() will then return this instance. Multiple calls to
    startSession() will each create a new instance, and store that as the
    'current' session from the point of view of @ref currentSession().

    @return SessionManager

    """
    session = cls._sessionClass(host)

    if makeCurrent:
      cls._instance = session
      # If we're a derived class (ie: UISessionManager) Ensure we keep track of
      # this instance in this base class too in case someone accesses it that
      # way. This means non-ui code can use this class, even if a UI has
      # initialized the session via UISessionManager.
      SessionManager._instance = cls._instance

    return session


  @classmethod
  @auditApiCall("Session")
  def currentSession(cls, requireManager=False):
    """

    @return SessionManager, if one has been instantiated by @ref
    startSession(), else None

    @param requireManager bool, If True, None will be returned if there is a
    current session, but it has not been initialized with a manager yet.

    """
    session = cls._instance
    if session and requireManager and not session.currentManager():
      return None

    return session


  @classmethod
  @auditApiCall("Session")
  def currentManager(cls):
    """

    @return The current Sessions's manager, or None if there is no session, or
    no manager has been set for the session.

    """
    manager = None
    session = cls.currentSession()
    if session:
      manager = session.currentManager()
    return manager


