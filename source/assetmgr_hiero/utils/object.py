import hiero.core


def getAllBinItems(item, binItems):
   if isinstance(item, hiero.core.BinItem):
     binItems.append(item)
   elif isinstance(item, hiero.core.Bin):
     for child in item.items():
       getAllBinItems(child, binItems)


def binItemsToObjs(items, objCls):

  objs = []

  if items:

    binItems = []
    for i in items:
      getAllBinItems(i, binItems)

    for b in binItems:
      item = b.activeItem()
      if isinstance(item, objCls):
        objs.append(item)

  return objs


def objsFromSelection(selection, objCls):

  objs = []
  objSet = set()

  for s in selection:

    if s in objSet:
      continue

    if isinstance(s, objCls):
      objs.append(s)
      objSet.add(s)

    elif isinstance(s, (hiero.core.BinItem, hiero.core.Bin)):
      itemObjs = binItemsToObjs(s, objCls)
      for i in itemObjs:
        if i not in objSet:
          objs.append(i)
          objSet.add(i)

  return objs



def clipsToHieroClipItems(clips):
  """
  @itemUsage hiero.items.HieroClipItem
  """
  from ..items import HieroClipItem

  clipItems = []

  if clips:
    for c in clips:
      i = HieroClipItem(c)
      clipItems.append(i)

  return clipItems


def trackItemsToShotItems(trackItems, options=None, coalesseByName=False):
  """
  @itemUsage hiero.items.HieroShotTrackItem
  """
  from ..items import HieroShotTrackItem

  shots = []

  if coalesseByName:

    itemsByName = {}
    trackItemsByName = {}

    # Go over the track items, and group by name, giving us a list of
    # TrackItems that use the same shot name
    for t in trackItems:
      name = t.name()
      if name not in itemsByName:
        item = HieroShotTrackItem()
        shots.append(item)
        itemsByName[name] = item
        trackItemsByName.setdefault(name, [])
      trackItemsByName[name].append(t)

    # Set the grouped TrackItems into the representative item
    for name, item in itemsByName.items():
      item.setTrackItems(trackItemsByName[name], options=options)

  else:
    # If we're not collating, we just turn each TrackItem into an Item
    for t in trackItems:
      shot = HieroShotTrackItem(t, options=options)
      shots.append(shot)

  return shots


def clipFromTrackItem(trackItem):

  source = trackItem.source()
  ## @todo When will this return a MediaSource?
  if not isinstance(source, hiero.core.Clip):
    return None
  return source


def projectsFromSelection(selection):

  projects = set()
  for s in selection:
    if not hasattr(s, 'project'): continue
    projects.add(s.project())
  return list(projects)


def checkForDuplicateItemNames(items, returnItems=False, allowConsecutive=False):

  names = set()
  duplicates = set()

  lastName = None

  for i in items:
    name = i.name()
    if name in names and not (allowConsecutive and name==lastName):
      duplicates.add(i if returnItems else i.name())
    names.add(name)
    lastName = name

  return sorted(list(duplicates))


def trackItemsFromSelection(sel, videoOnly=True):

  toTrackItem = lambda i : isinstance(i, hiero.core.TrackItem)
  toTrack = lambda i : isinstance(i, hiero.core.TrackBase)

  def filterToVideoTrackItems(item):
    track = item.parentTrack()
    if track and isinstance(track, hiero.core.VideoTrack):
      return True
    return False

  trackItems = filter(toTrackItem, sel)
  tracks = filter(toTrack, sel)

  # We only support a single track, or a list of track items
  # The setSelection validation should ensure this is the case
  if len(tracks) and not trackItems:
    trackItems = tracks[0].items()

  if videoOnly:
    trackItems = filter(filterToVideoTrackItems, trackItems)

  return trackItems




