from ..SessionManager import SessionManager
from .UISession import UISession


__all__ = ['UISessionManager']


class UISessionManager(SessionManager):
  """

  An extension of the @ref python.SessionManager that adds utility for managing
  User Interface aspects of @ref Manager interaction. This should always be
  used whenever an application is running in a mode that has a user-facing GUI.

  """

  ## @todo Do we need some signals here to make it easier for UI's to track the
  ## current manager for de-registration, etc...?

  _sessionClass = UISession





