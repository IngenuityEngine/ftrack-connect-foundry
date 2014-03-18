from .Specification import Specification, TypedProperty
from ..constants import *


__all__  = ['EntitySpecification', 'GroupingSpecification',
  'ProjectSpecification', 'ShotSpecification', 'FileSpecification',
  'ImageSpecification']


class EntitySpecification(Specification):
  """

  EntitySpecifications are used to 'type' a \ref entity. In their simplest
  form, the _type can be used as a simple string-matched filter. In more
  advanced cases, the other properties of the Specification may be useful to
  further refine selection. During registration, the Specification may also
  provide valuable information to the Manager to help it best represent the
  Hosts data.

  """
  _prefix = "core.entity"

  nameHint = TypedProperty(str, doc="A hint as to the name of the entity"
      +", used in cases where this is not implicit in the reference.")

  referenceHint = TypedProperty(str, doc="A hint for the entity reference, "
      +"useful for default browser path, etc... This may, or may not "
      +"ultimately be relevant. The Asset Management system should check its "
      +"applicability before using it, and may freely ignore it if it has "
      +"a better idea about a suitable reference.")

  thumbnailPath = TypedProperty(str, initVal="", doc="If a thumbnail was "+
      "requested for the registration, then this may be set to a path, "+
      "pointing to a thumbnail. If, for any reason, the thumbnail isn't "+
      "available, then this will be an empty string.")


class GroupingSpecification(EntitySpecification):
  _type = "group"

class ProjectSpecification(GroupingSpecification):
  _type = "group.project"

class ShotSpecification(GroupingSpecification):
  _type = "group.shot"



FileSpecification = type('FileSpecification', (EntitySpecification,),
{
  '__doc__' : """A base Specification for all file-based entities. Because in many
cases, the Asset Managment System itself may ultimately determine the final
name or path, we allow this Specification to provide 'hits' for these, on the
assumption that they may not necessarily be used. Additionally, We allow
all files to be sequences. Resolution of sequence tokens is handled
separately to this API.""",

  '_type' : "file",

  kField_HintPath : TypedProperty(str,
    doc="str, A hint for the directory that the file will reside in"),

  kField_HintFilename : TypedProperty(str,
    doc="A hint for the name of the file"),

  kField_FileExtensions : TypedProperty(list,
    doc="list, A list of extensions that are applicable"),

  kField_FileIsEnumerated: TypedProperty(bool,
    doc="If True, then the specification describes a file sequence, rather "+
      "than a single file"),

  kField_FrameStart : TypedProperty(int,
    doc="The starting frame number for the file, if a sequence"),

  kField_FrameEnd : TypedProperty(int,
    doc="The ending frame number for the file, if a sequence")

})


ImageSpecification = type('ImageSpecification', (FileSpecification,),
{

  '_type' : "file.image",

  kField_PixelColorspace : TypedProperty(str,
    doc="The OCIO colour space name that the pixel data is encoded in, eg: lin"),

  kField_PixelWidth : TypedProperty(int,
    doc="The width in pixels of the image"),

  kField_PixelHeight : TypedProperty(int,
    doc="The height in pixels of the image"),

  kField_PixelEncoding : TypedProperty(str,
    doc="The data format the image is encoded in, eg: exr, png, jpeg"),

  kField_PixelCompression : TypedProperty(str,
    doc="Specifics of any compression used, eg: for exr - zip or rle"),

  kField_PixelNumChannels : TypedProperty(int,
    doc="The number of channels in the image")

})



