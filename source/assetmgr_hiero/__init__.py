# This is loads the functions Hiero calls from C into the module namespace
# If this module does not map to hiero.asset, then it should be set using
#
#    import <thisModule>
#    import sys
#    sys.setdefault('hiero.asset', <thisModule>)
#
# {
from _c_linkage import resolveIfEntityReference
from _c_linkage import isEntityReference
from _c_linkage import setupAssetCallback
from _c_linkage import assetManagerIconFilePath
# }

import FnAssetAPI
import hiero.core

# We have issues with API auditing and C objects going away, so we'll set this
# so when people do use auditing, it doesn't explode
FnAssetAPI.audit.reprArgs = True

# Certain features or imports shouldnt be available in player/batch/etc...
# {
inPlayer = hiero.core.isHieroPlayer()
## @todo When we support a 'batch' mode, then this needs to be updated.
inUI = True
# }


# Hook up event listeners, and relays into the Asset Event Manager
from . import events
events.registerEvents()


# Mangle the VersionScanner so that we can use Assetised versioning
from . import versioning
versioning.registerOverrides()


# Mangle the NukeExporter to emit signals, etc...
if not inPlayer:
  from . import export
  export.registerPresets()


# Start a session with the asset API, this will load any plug-ins etc... but
# won't actually initialize any particular asset system
# {

# Ensure we don't initialize any asset API UI if we're headless
if inUI:
  import FnAssetAPI.ui
  sessionManager = FnAssetAPI.ui.UISessionManager
else:
  sessionManager = FnAssetAPI.SessionManager

from .HieroHost import HieroHost
from . import session

host = HieroHost()
apiSession = sessionManager.startSession(host)
session.restoreAssetAPISessionSettings(apiSession)
# }

if inUI:
  from . import ui

