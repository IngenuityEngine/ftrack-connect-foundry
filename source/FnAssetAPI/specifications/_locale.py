from .Specification import Specification, TypedProperty


__all__ = ['LocaleSpecification', 'DocumentLocale', 'ExportLocale',
 'TimelineLocale', 'TimelineItemLocale', 'TimelineTrackLocale', 'ClipBinLocale',
 'ClipLocale', 'MenuLocale', 'AssetMenuLocale', 'FileMenuLocale',
 'ContextMenuLocale']


class LocaleSpecification(Specification):
  """

  LocaleSpecifications are used by a Host to define which part of the
  application is interacting with the Manager. For example, the DocumentLocale
  should be used when dealing with scene files, projects, etc... This
  information is generally useful to Managers as it allows them to better
  handle the resulting Entity data.

  """
  _prefix = "core.locale"


class DocumentLocale(LocaleSpecification):
  _type = "document"

  action = TypedProperty(str, doc="Because a new version is usually achieved "+
      "publishing again to the same source entity reference, it is ambigious "+
      "as to whether or not the intent is 'save new version' or 'overwrite'. "+
      "Some asset managers support both (some don't), the action property "+
      "should be set to the suitable type by the Host to ensure that an "+
      "Manager return a suitable @ref entity_reference. "+
      "@see FnAssetAPI.constants")


class ExportLocale(LocaleSpecification):
  _type = "export"


class TimelineLocale(LocaleSpecification):
  _type = "timeline"

class TimelineItemLocale(TimelineLocale):
  _type = TimelineLocale._type + ".item"

class TimelineTrackLocale(TimelineLocale):
  _type = TimelineLocale._type + ".track"


class ClipBinLocale(LocaleSpecification):
  _type = "clipbin"

class ClipLocale(LocaleSpecification):
  _type = "clip"


class MenuLocale(LocaleSpecification):
  _type = "menu"

class AssetMenuLocale(MenuLocale):
  _type = MenuLocale._type + ".asset"

class FileMenuLocale(MenuLocale):
  _type = MenuLocale._type + ".file"

class ContextMenuLocale(MenuLocale):
  _type = MenuLocale._type + ".contextual"



