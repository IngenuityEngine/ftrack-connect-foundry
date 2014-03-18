import math
import FnAssetAPI

from . import object as objectUtils

import hiero.core

def getTrackItemIdentifiers(trackItems):

  identifiers = []

  for t in trackItems:

    if not t: continue

    parent = t.parent()
    # We should'nt be in this situation, but probably need to think more about
    # just ignoring this here ;)
    if not parent: continue

    ref = ( t.guid(), parent.guid() )
    identifiers.append(ref)

  return identifiers


def getTrackItemsFromIdentifiers(identifiers, sequence):

  # Presently identifiers are (itemGuid, trackGuid) tuples
  # Will return a list of the same length, with 'None' if no match was found

  trackItems = []

  tracks = getTracksInSequence(sequence)
  tracks = dict( (v.guid(),v) for v in tracks.values() )

  for i in identifiers:

    item = None
    trackGuid = i[1]
    itemGuid = i[0]

    filterFn = lambda ti : ti.guid() == itemGuid

    if trackGuid in tracks:
      items = tracks[trackGuid].items()
      matching = filter(filterFn, items)
      item = matching[0] if len(matching) else None

    trackItems.append(item)

  return trackItems


def getTracksInSequence(sequence):

  tracks = {}

  for a in sequence.audioTracks():
    tracks[a.name()] = a
  for v in sequence.videoTracks():
    tracks[v.name()] = v

  return tracks



def getMatchingAndOverlappingTrackItems(trackItems, targetTrack):

  existing = targetTrack.items()
  if not existing:
    return ({}, {})

  matching = {}
  overlapped = {}

  for t in trackItems:
    for e in existing:
      if trackItemTimingssMatch(t, e):
        matching[t] = e
        break
      if trackItemTimingsOverlap(t, e):
        overlapped.setdefault(t, []).append(e)

  return (matching, overlapped)



def trackItemTimingssMatch(a, b):

  if a.timelineIn() == b.timelineIn() and a.timelineOut() == b.timelineOut():
    return True

  return False


def trackItemTimingsOverlap(a, b):

  inA = a.timelineIn()
  inB = b.timelineIn()
  outA = a.timelineOut()
  outB = b.timelineOut()

  # There may be quicker ways to do this, but
  # my brain isn't working today, not one bit.
  if inA < inB < outA : return True
  if inA < outB < outA : return True
  if inB < inA < outB : return True
  if inB < outA < outB : return True

  return False


kTimingOption_numbering = 'numbering'
kTimingOption_customNumberingStart = 'customNumberingStart'
kTimingOption_handles = 'handles'
kTimingOption_customHandleLength = 'customHandleLength'
kTimingOption_includeRetiming = 'includeRetiming'
kTimingOption_clampToPositive = 'clampToPositive'
kTimingOption_includeSourceTimecode = 'includeSourceTimecode'
kTimingOption_includeInTimecode = 'includeInTimecode'

kTimingOptions_numbering = ('clip', 'custom')
kTimingOptions_handles = ('none', 'custom', 'clip', 'customClip')

kTimingOptionDefaults = {
  kTimingOption_numbering : 'clip',
  kTimingOption_customNumberingStart : 1001,
  kTimingOption_handles : 'none',
  kTimingOption_customHandleLength : 12,
  kTimingOption_clampToPositive : True,
  kTimingOption_includeRetiming : True,
  kTimingOption_includeInTimecode : False,
  kTimingOption_includeSourceTimecode : False
}


def filterToTimingOptions(opts):
  timingOpts = {}
  for k,v in opts.items():
    if k in kTimingOptionDefaults:
      timingOpts[k] = v
  return timingOpts


def timingsFromTrackItem(trackItem, options):

  """
  @param opts Options to control how timings are extracted
  opts = {
    'numbering' : ( 'clip', 'custom' ), # clip
    'customNumberingStart' : 1001,
    'handles' : ( 'none', 'custom', 'clip', 'customClip' ), # none
    'customHandleLength' : 12,
    'includeRetiming' : True,
    'clampToPositive' : True
  }
  """

  # Ensure we have some sensible, known defaults
  opts = dict(kTimingOptionDefaults)
  opts.update(options)

  start = end = in_ = out = 0

  clip = objectUtils.clipFromTrackItem(trackItem)
  if not clip:
    FnAssetAPI.logging.debug(("No clip available for %s - clip based timings "+
        "will be ignored") % trackItem)

  numbering = opts[kTimingOption_numbering]
  if numbering == 'custom':
    # If we're using a custom start frame, override the clip's start frame number
    start = opts[kTimingOption_customNumberingStart]
  elif numbering == 'clip' and clip:
    # If we have a clip, use its frame numbers
    start = clip.timelineOffset()
    # Make sure we factor in the in point of the TrackItem, its relative
    # The floor is to account for re-times
    start += math.floor(trackItem.sourceIn())

  handles = opts[kTimingOption_handles]
  try:
    customHandleLength = int(opts[kTimingOption_customHandleLength])
  except ValueError:
    pass

  editLength = trackItem.timelineOut() - trackItem.timelineIn()
  if opts[kTimingOption_includeRetiming]:
    # If its a single frame clip then don't include retiming, as it'll be '0',
    # which though correct, isnt helpfull here.
    if clip.duration() != 1:
      editLength = math.ceil(editLength * trackItem.playbackSpeed())


  # We want to anchor the 'in' point to the chosen starting frame number, and
  # subtract handles as necessary rather than shifting the edit start frame.
  # Start off with no handles.
  in_ = start

  # The 'length' of the shot is always the edit length of the track item
  out = in_ + editLength

  # No handles on the end either to start with
  end = out

  # Apply handles based on clip length (floor to take into account retimes)
  if handles in ('clip', 'customClip') and clip:
    start -= math.floor(trackItem.sourceIn())
    end = start + clip.duration()

  # Add any custom handles
  if handles in ('custom', 'customClip'):
    start -= customHandleLength
    end += customHandleLength

  # Ensure we don't go out of range if we're asked to clamp
  if opts[kTimingOption_clampToPositive]:
    start = max(0, start)
    in_ = max(0, in_)
    out = max(0, out)
    end = max(0, end)

  return start, end, in_, out


def timingsFromTrackItems(trackItems, options):
  """

    --|  D   |----    ---|    E     |---
     -|  A      |  C   |    B    |----------

  In this situation, we return the timings, based on the supplied options:

    @li If 'Source Clip' is used for numbering, they will be from clip A, which
        becomes the master TrackItem as it's starts the cut and is on the
        lowest track.
    @li 'in_' will be from clip A.
    @li 'out' will be the absolute timeline number of frames from clip E,
         using the numbering base of A.
    @li 'start' will include the handles from A.
    @li 'end' will be the handles from E as it ends the cut.

  """

  if not trackItems:
    raise ValueError("No TrackItems supplied")

  # Find the timings for the first/master item, so we can figure out the target
  # frame numberings etc... We know these have been supplied in chronological
  # order, starting with the item on the lowest track.
  first_start, first_end, first_in, first_out = \
      timingsFromTrackItem(trackItems[0], options)

  if len(trackItems) == 1:
    return first_start, first_end, first_in, first_out

  # We want to consider the absolute union in the context of the timeline,
  # instead of the union in Clip space so  Force the numbering options to be
  # relative to the 'in' frame number from the master track item. We use 'in'
  # not 'start' as start is variable including handles, in is anchored to the
  # users chosen source frame

  # Make sure we don't mutate the input dictionary
  relOpts = dict(options)
  relOpts[kTimingOption_numbering] = 'custom'
  relOpts[kTimingOption_customNumberingStart] = first_in

  # We need to figure out where they are positioned relative to each other. So
  # we find the start frame of the earliest TrackItem, and offset the others

  itemOffsets = {}

  itemStarts = dict( (t, t.timelineIn()) for t in trackItems )
  startOffset = sorted(itemStarts.values())[0]
  itemOffsets = dict( (t, s-startOffset) for (t, s) in itemStarts.items() )

  # Find all the timings for all TrackItems based on the 'in' frame from the
  # first item
  timingsMap = {}
  for t in trackItems:
    timings = timingsFromTrackItem(t, relOpts)
    # Make sure we apply the offset of each track item relative to the 1st
    offset = itemOffsets.get(t, 0)
    # Combine the relative position offset for this item
    timings = map(lambda i: i+offset, timings)
    timingsMap[t] = timings

  # Now figure out the final timings The start/in is always from the master
  start = first_start
  in_ = first_in

  # We initial base the cut end timings from the master item...
  out = first_out
  end = first_end

  # ...then look at all the remaining track items to find the one that ends
  # the cut, and use it's timings. They have already been offset back to
  # 'absolute' timeline space, and moved to match the correct frame numberings
  # based on the master clip.
  for t in trackItems[1:]:
    t_start, t_end, t_in, t_out = timingsMap[t]
    if t_out > out:
      out = t_out
      end = t_end

  return start, end, in_, out


def inTimecodeFromTrackItem(trackItem):

  seq = trackItem.parentSequence()
  if not seq:
    return ''

  frames = trackItem.timelineIn()
  rate = seq.framerate()
  drop = seq.dropFrame()
  offset = seq.timecodeStart()

  if drop:
    displayType = hiero.core.Timecode.kDisplayDropFrameTimecode
  else:
    displayType = hiero.core.Timecode.kDisplayTimecode

  tc = hiero.core.Timecode.timeToString(frames, rate, displayType, False, offset)
  return tc


def sourceTimecodeFromTrackItem(trackItem):

  clip = objectUtils.clipFromTrackItem(trackItem)
  if not clip:
    return ''

  ms = clip.mediaSource()

  frames = ms.timecodeStart()
  rate = clip.framerate()
  drop = clip.dropFrame()
  offset = trackItem.sourceIn()

  if drop:
    displayType = hiero.core.Timecode.kDisplayDropFrameTimecode
  else:
    displayType = hiero.core.Timecode.kDisplayTimecode

  tc = hiero.core.Timecode.timeToString(frames, rate, displayType, False, offset)
  return tc




