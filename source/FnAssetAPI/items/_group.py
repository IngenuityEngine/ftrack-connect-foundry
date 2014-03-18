from .Item import Item
from .propertyGroups import * 
from .. import specifications
from ..core.properties import TypedProperty


__all__ = ['ShotItem']


class ShotItem(Item, TimingProperties, EditorialItemProperties):

  _type = "group.shot"
  _primaryProperty = "code"

  code = TypedProperty(str, doc="The short, machine safe name for the shot")

  def toSpecification(self, spec=None):
    if not spec:
      spec = specifications.ShotSpecification()
    spec.nameHint = self.nameHint if self.nameHint else self.code
    ## @todo shouldn't we be calling the Item.toSpecification() of the base class here?
    return spec


