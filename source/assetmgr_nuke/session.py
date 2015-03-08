import os
import FnAssetAPI

from . import utils

__all__ = [
  'restoreAssetAPISessionSettings',
  'saveManagerSessionSettings',
  'saveAssetAPISettings'
]


def restoreAssetAPISessionSettings(session):

  # Restore the users logging preferences
  try:
    loggingSeverity = int(utils.getSetting(FnAssetAPI.constants.kSetting_LoggingSeverity, -1))
  except ValueError:
    loggingSeverity = -1

  if 'FOUNDRY_ASSET_LOGGING_SEVERITY' not in os.environ:
   if loggingSeverity > -1:
    FnAssetAPI.logging.displaySeverity = loggingSeverity
    FnAssetAPI.logging.info("Setting Logging Severity to '%s'" %
        FnAssetAPI.logging.kSeverityNames[loggingSeverity])
  else:
    FnAssetAPI.logging.debug("Not restoring preferred Logging Severity as FOUNDRY_ASSET_LOGGING_SEVERITY is set")


  # Restore the Manager if we have one
  managerIdentifier = utils.getSetting(FnAssetAPI.constants.kSetting_ManagerIdentifier)
  if managerIdentifier and managerIdentifier != 'None':

    FnAssetAPI.logging.info("Initialising Asset Management API with stored identifier: %s" %
      managerIdentifier)

    try:

      sessionSettings = {}
      sessionSettings[FnAssetAPI.constants.kSetting_ManagerIdentifier] = managerIdentifier
      ## @todo Restore any manager specific settings
      session.setSettings(sessionSettings)

    except FnAssetAPI.exceptions.ManagerError as e:
      FnAssetAPI.logging.error("Error restoring the preferred Asset Manager: %s" % e)



def saveManagerSessionSettings(session):

  # Store the current manager in the app defaults so we can restore it the
  # next time we load
  manager = session.currentManager()
  identifier = manager.getIdentifier() if manager else ''
  utils.setSetting(FnAssetAPI.constants.kSetting_ManagerIdentifier, identifier)

  FnAssetAPI.logging.info("Setting default Asset Manager to: %s" % identifier)


def saveAssetAPISettings():

  loggingSeverity = FnAssetAPI.logging.displaySeverity
  utils.setSetting(FnAssetAPI.constants.kSetting_LoggingSeverity, loggingSeverity)

  FnAssetAPI.logging.info("Setting default Logging Severity to '%s'" % FnAssetAPI.logging.kSeverityNames[loggingSeverity])



