import FnAssetAPI
from FnAssetAPI.items import FileItem, ImageItem

from . import specifications


__all__ = ['NukeScriptItem']

class NukeScriptItem(FileItem):
  _type = FileItem._type + ".nukescript"

  def toSpecification(self):
    spec = specifications.NukeScriptSpecification()
    super(NukeScriptItem, self).toSpecification(spec)
    return spec



