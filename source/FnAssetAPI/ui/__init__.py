import sys

import QtExt

sys.modules.setdefault('FnAssetAPI.ui.toolkit', QtExt)
from .UISessionManager import UISessionManager

def setToolkit(module):
  sys.modules.setdefault('FnAssetAPI.ui.toolkit', module)

