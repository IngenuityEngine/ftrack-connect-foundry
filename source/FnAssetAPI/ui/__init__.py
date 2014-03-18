import sys

try:
  import PySide
  sys.modules.setdefault('FnAssetAPI.ui.toolkit', PySide)
except ImportError:
  try:
    import PyQt
    sys.modules.setdefault('FnAssetAPI.ui.toolkit', PyQt)
  except ImportError:
    raise RuntimeError("Unable to determine the UI toolkit")

from .UISessionManager import UISessionManager


def setToolkit(module):
  sys.modules.setdefault('FnAssetAPI.ui.toolkit', module)

