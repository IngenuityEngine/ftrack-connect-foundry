from .propertyGroups import *
from .. import specifications

from ._general import FileItem


__all__ = ['ImageItem', 'ClipItem']


class ImageItem(FileItem, PixelProperties, EncodingProperties):

  _type = "file.image"

  def toSpecification(self, spec=None):

    if not spec:
      spec = specifications.ImageSpecification()

    # Call the base class to populate generic properties
    spec = FileItem.toSpecification(self, spec)

    return spec


class ClipItem(ImageItem, EditorialItemProperties):
  _type = "file.image.clip"

