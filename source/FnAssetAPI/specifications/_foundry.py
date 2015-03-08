from . import FileSpecification


__all__ = ['HieroProjectSpecification', 'NukeScriptSpecification']


## @name Entities
## @{

class HieroProjectSpecification(FileSpecification):
  _type = FileSpecification._type + ".hrox"

  def __init__(self, data=None):
    super(HieroProjectSpecification, self).__init__(data)

    self.extensions = ['hrox',]
    self.enumerated = False


class NukeScriptSpecification(FileSpecification):
  _type = FileSpecification._type + ".nukescript"

  def __init__(self, data=None):
    super(NukeScriptSpecification, self).__init__(data)

    self.extensions = ['nk',]
    self.enumerated = False

## @}
