import sys

import QtExt

sys.modules.setdefault('FnAssetAPI.ui.toolkit', QtExt)

# try:
#   import PySide
#   
# except ImportError:
#   try:
#     import PyQt
#     sys.modules.setdefault('FnAssetAPI.ui.toolkit', PyQt)
#   except ImportError:
#     raise RuntimeError("Unable to determine the UI toolkit")

from .UISessionManager import UISessionManager


def setToolkit(module):
  sys.modules.setdefault('FnAssetAPI.ui.toolkit', module)

