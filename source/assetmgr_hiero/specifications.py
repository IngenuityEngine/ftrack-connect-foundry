from FnAssetAPI.specifications import ExportLocale
from FnAssetAPI.specifications import TimelineLocale, TimelineItemLocale
from FnAssetAPI.specifications import ClipLocale, ClipBinLocale
from FnAssetAPI.specifications import ContextMenuLocale

from FnAssetAPI.specifications.Specification import TypedProperty as P

__all__ = [
  'HieroExportLocale',
  'HieroNukeScriptExportLocale',
  'HieroTimelineLocale',
  'HieroBinLocale',
  'HieroTrackItemLocale',
  'HieroClipLocale',
  'HieroTimelineContextMenuLocale',
  'HieroBinContextMenuLocale',
  'HieroProjectSpecification'
]

## @name Locales
## @{

class HieroExportLocale(ExportLocale):
  _type = ExportLocale._type + ".hiero"
  role = P(str, doc="The discipline the script is being exported for")
  scope = P(str, doc="The scope, for example Shot, Track, etc...")
  objects = P(object, doc="The objects relating to the item being exported")


class HieroNukeScriptExportLocale(HieroExportLocale):
  _type = HieroExportLocale._type + ".nukescript"


class HieroTimelineLocale(TimelineLocale):
  _type = TimelineLocale._type + ".hiero"
  objects = P(object, doc="The relevant timeline objects")
  discipline = P(str, doc="The type of activity the track represents")


class HieroBinLocale(ClipBinLocale):
  _type = ClipBinLocale._type + ".hiero"
  objects = P(object, doc="The relevant bin items")


class HieroTrackItemLocale(TimelineItemLocale):
  _type = TimelineItemLocale._type + ".hiero"
  objects = P(object, doc="The relevant hiero.core.TrackItems")


class HieroClipLocale(ClipLocale):
  _type = ClipLocale._type + ".hiero"
  objects = P(object, doc="The relevant hiero.core.Clips")


class HieroTimelineContextMenuLocale(ContextMenuLocale):
  _type = ContextMenuLocale._type + ".timeline"
  event = P(object, doc="The Hiero event object")


class HieroBinContextMenuLocale(ContextMenuLocale):
  _type = ContextMenuLocale._type + ".bincontext"
  event = P(object, doc="The Hiero event object")

## @}


## @todo clean up code that uses these
from FnAssetAPI.specifications import HieroProjectSpecification



