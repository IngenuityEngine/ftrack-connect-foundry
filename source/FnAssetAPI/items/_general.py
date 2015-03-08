from .Item import Item
from .propertyGroups import *
from .. import specifications
from ..constants import *

import os


__all__ = ['FileItem']


class FileItem(Item, FilesystemProperties):

  _type = "file"
  _primaryProperty = kField_FilePath

  ## @todo Sanitisation of the file path to ensure any sequence listing is in a
  ## sprintf compatible form (ie: no ###)

  def toSpecification(self, spec=None):

    if not spec:
      spec = specifications.FileSpecification()

    # Call the base class to populate generic properties
    Item.toSpecification(self, spec)

    # Populate hints we'll use the constants for robustness
    if self.path:

      # If there is a frame token, set enumerated to True
      setattr(self, kField_FileIsEnumerated, "%" in self.path)

      base, ext = os.path.splitext(self.path)

      if ext:
        ext = ext[1:] if ext.startswith(".") else ext
        setattr(spec, kField_FileExtensions, (ext,))

      directory = os.path.dirname(self.path)
      if directory:
        setattr(spec, kField_HintPath, directory)

      if base:
        filename = os.path.basename(base)
        if filename:
          setattr(spec, kField_HintFilename, filename)

    # Use the filenameHint for the nameHint if we don't have anything else
    if not getattr(spec, kField_HintName, None):
      filenameHint = getattr(spec, kField_HintFilename)
      if filenameHint:
        setattr(spec, kField_HintName, filenameHint)

    return spec

