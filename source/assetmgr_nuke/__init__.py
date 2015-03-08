import FnAssetAPI

from . import utils

utils.registerEvents()

# Register our filters for resolving, etc... disabled due to filenameFilter bug
#utils.registerFilters()

import nuke
initUI = nuke.env["gui"]

# Start a session with the asset API, this will load any plug-ins etc... but
# won't actually initialize any particular asset system

# Ensure we don't initialize any asset API UI if we're headless
if initUI:
  import FnAssetAPI.ui
  sessionManager = FnAssetAPI.ui.UISessionManager
else:
  sessionManager = FnAssetAPI.SessionManager

from .NukeHost import NukeHost
from . import session

host = NukeHost()
apiSession = sessionManager.startSession(host)
session.restoreAssetAPISessionSettings(apiSession)

if initUI:
  from . import ui

