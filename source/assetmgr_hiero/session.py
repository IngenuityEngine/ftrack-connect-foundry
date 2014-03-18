import os

import FnAssetAPI
import hiero.core


__all__ = [
  'restoreAssetAPISessionSettings',
  'saveManagerSessionSettings',
  'saveAssetAPISettings'
]


def restoreAssetAPISessionSettings(session):

  # See if we have anything stored in the application prefs
  appSettings = hiero.core.ApplicationSettings()

  if 'FOUNDRY_ASSET_LOGGING_SEVERITY' not in os.environ:
    # Recall Logging Severity
    try:
      loggingSeverity = int(appSettings.value(FnAssetAPI.constants.kSetting_LoggingSeverity, -1))
    except ValueError:
      loggingSeverity = -1

    if loggingSeverity > -1:
      FnAssetAPI.logging.displaySeverity = loggingSeverity
      FnAssetAPI.logging.info("Setting Logging Severity to: '%s'" % FnAssetAPI.logging.kSeverityNames[loggingSeverity])
  else:
    FnAssetAPI.logging.debug("Not restoring preferred Logging Severity as FOUNDRY_ASSET_LOGGING_SEVERITY is set")

  # If we have a stored preferred manager, then well set the session up with that
  managerIdentifier = appSettings.value(FnAssetAPI.constants.kSetting_ManagerIdentifier, None)
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

  # Manager
  manager = session.currentManager()
  identifier = manager.getIdentifier() if manager else ''
  appSettings = hiero.core.ApplicationSettings()
  appSettings.setValue(FnAssetAPI.constants.kSetting_ManagerIdentifier, identifier)
  FnAssetAPI.logging.info("Setting default Asset Manager to: %s" % identifier)

def saveAssetAPISettings():

  appSettings = hiero.core.ApplicationSettings()

  # Logging Severity
  severity = FnAssetAPI.logging.displaySeverity
  appSettings.setValue(FnAssetAPI.constants.kSetting_LoggingSeverity, severity)
  FnAssetAPI.logging.info("Setting default Logging Severity to '%s'" % FnAssetAPI.logging.kSeverityNames[severity])




