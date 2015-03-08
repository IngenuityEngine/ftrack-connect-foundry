from FnAssetAPI.core.decorators import debugStaticCall
import hiero.core

# We want tag.assetmgr.id and tag.assetmgr.manager. Those don't show in Tags Editor, need direct children of "tag".
kAssetTag = "FnAssetAPI"

def getAssetTag(obj, create=False):
  """ Find a tag in an object with the AssetMgr's name.
  @param obj: Object to find the tag.
  @param create: If True, create the tag if none is found.
  @return: The AssetMgr tag. """

  return getNamedTag(obj, kAssetTag, create)


def getNamedTag(obj, name, create=False):

  if isinstance(obj, hiero.core.Project):
    return __getProjectAssetTag(obj, create)

  if not hasattr(obj, 'tags'):
    return None

  tags = obj.tags()
  for tag in tags:
    if tag.name() == name:
      return tag
  if create:
    tag = hiero.core.Tag(name)
    addedTag = obj.addTag(tag)
    return addedTag
  return None


def __getProjectAssetTag(project, create=False):

  tagsBin = project.tagsBin()

  for tag in tagsBin.items():
    if tag.name() == kAssetTag:
      return tag
  if create:
    tag = hiero.core.Tag(kAssetTag)
    tagsBin.addItem(tag)
    return tag
  return None


def getAssetTagField(obj, field, default=None):
  """ Find a tag in an object with the AssetMgr's name, and extract a field from its metadata
  @param obj: Object to find the tag.
  @param field: Metadata key. It will be prefixed with the kPrefix namespace.
  @return: The value if found, otherwise None. """
  tag = getAssetTag(obj)
  value = default
  if tag:
    metadata = tag.metadata()
    key = "tag.%s" % field
    if metadata.hasKey(key):
      value = metadata[field]
  return value


def setAssetTagField(obj, field, value):
  """ Find a tag in an object with the AssetMgr's name, and set a field in its metadata
  @param obj: Object to find the tag.
  @param field: Metadata key. It will be prefixed with the kPrefix namespace.
  @parm: The value to set. """
  tag = getAssetTag(obj, create=True)
  if tag:
    md = tag.metadata()
    if not md.readOnly():
      key = "tag.%s" % field
      md.setValue(key, value)


__nonPersistentTagData = {}

@debugStaticCall
def getTemporaryAssetTagField(obj, field, default=None):
  """

  Version of getAssetTagField for tags that are stored only in memory, and so are
  lost when the application closes.

  """

  global __nonPersistentTagData

  # We use guids if we can, instead of the obj to avoid incrementing refcounts
  if hasattr(obj, 'guid'):
    obj = obj.guid()

  objDict = __nonPersistentTagData.get(obj, None)
  if not objDict:
    return default
  return objDict.get(field, default)


@debugStaticCall
def setTemporaryAssetTagField(obj, field, value):
  """

  Version of setAssetTagField that stores tags in memory, and so are
  lost when the application closes.

  """
  global __nonPersistentTagData

  # We use guids if we can, instead of the obj to avoid incrementing refcounts
  if hasattr(obj, 'guid'):
    obj = obj.guid()

  objDict = __nonPersistentTagData.setdefault(obj, {})
  objDict[field] = value

