from ..core.properties import TypedProperty
from ..constants import *


__all__ = ['FilesystemProperties', 'TimingProperties', 'EditorialItemProperties',
  'PixelProperties', 'EncodingProperties', 'TitleProperties', 'AnnotationProperties']


"""

Property groups can be used when deriving from Item to introduce well-known
property names in a consistent fashion. Note, there primary inheritance for an
Item derived class should always be an Item class, additional inheritance of
from these groups should then follow.

"""


FilesystemProperties = type('FilesystemProperties', (object,),
{
    kField_FilePath : TypedProperty(str, order=1, doc="A Path to the main file or sequence"),
    kField_FileIsEnumerated: TypedProperty(bool, order=2, doc="Single file, or sequence"),

    kField_FrameStart : TypedProperty(int, order=3,
      doc="The starting (absolute) frame number for the item"),

    kField_FrameEnd : TypedProperty(int, order=4,
      doc="The ending (absolute) Frame number for the item")
})


TimingProperties = type('TimingProperties', (object,),
{
    kField_FrameStart : TypedProperty(int, order=5,
      doc="The starting (absolute) frame number for the item"),

    kField_FrameEnd : TypedProperty(int, order=6,
      doc="The ending (absolute) Frame number for the item")
})

EditorialItemProperties = type('EditorialItemProperties', (object,),
{

  kField_FrameIn : TypedProperty(int, order=7,
    doc="The in (absolute) Frame number for the item"),

  kField_FrameOut : TypedProperty(int, order=8,
    doc="The out (absolute) Frame number for the item"),

  kField_FrameRate : TypedProperty(float, order=9,
    doc="The frame rate associateed with the item"),

  kField_DropFrame : TypedProperty(bool, order=10,
    doc="Does the item use drop-frame timecode"),

  kField_FieldDominance : TypedProperty(str, order=11,
    doc="The Field Dominance - none, upper, lower")

})


PixelProperties = type('PixelProperties', (object,),
{
  kField_PixelColorspace : TypedProperty(str, order=12, doc="The colorspace pixel data is encoded in"),
  kField_PixelWidth : TypedProperty(int, order=13),
  kField_PixelHeight : TypedProperty(int, order=14),
  kField_PixelAspectRatio : TypedProperty(float, order=15),
  kField_PixelBitDepth : TypedProperty(int, order=16),
  kField_PixelNumChannels : TypedProperty(int, order=17),
})


EncodingProperties = type('EncodingProperties', (object,),
{
  kField_PixelEncoding : TypedProperty(str, order=18),
  kField_PixelCompression : TypedProperty(str, order=19)
})



class TitleProperties(object):
  displayName = TypedProperty(str, doc="A display name for the item")


class AnnotationProperties(object):
  notes = TypedProperty(str, doc="Notes on the item")

