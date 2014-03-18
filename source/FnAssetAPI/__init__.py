from . import items
from .Manager import Manager
from .Entity import Entity
from .Events import Events
from .Host import Host
from .QtHost import QtHost
from .ManagerFactory import ManagerFactory
from .SessionManager import SessionManager
from .Context import Context

# A convenience to localizing a string if a session is available,
# cleans up any remaning {} if there wasn't one.
def l(string):
  session = SessionManager.currentSession()
  if session:
    string = session.localizeString(string)
  return string.translate(None, "{}")

