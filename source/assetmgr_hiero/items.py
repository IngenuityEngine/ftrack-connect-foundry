import FnAssetAPI.items
import FnAssetAPI.logging
import FnAssetAPI.constants
from FnAssetAPI.core.properties import TypedProperty, TimecodeProperty

import traceback

import hiero.core

import specifications
import utils


class HieroShotTrackItem(FnAssetAPI.items.ShotItem):

  # We're not going to change the name here, as we want this to be
  # compatible with anything else that uses a shot - we also don't
  # add any new properties so there is no need.
  # So, we tell the class not to be registered as an item handler.
  _factoryIgnore = True

  sourceTimecode = TimecodeProperty(doc="The timecode of any source "+
    "media relating to this cut.")

  inTimecode = TimecodeProperty(doc="The starting timecode for the cut")


  def __init__(self, trackItems=None, options=None):
    super(HieroShotTrackItem, self).__init__

    self._trackItems = []
    if trackItems:
      self.setTrackItems(trackItems, options)

    self._thumbnailPath = ''


  def prepareThumbnail(self, options):
    """
    Call to create a thumbnail for this item, and store the path in the item.
    This will be set in the spec, if present later.
    """

    self._thumbnailPath = ''

    if not self._trackItems:
      raise RuntimeError("Unable to build a thumbnail, no TrackItems set")

    frame = 0
    if self._trackItems:
      frame = utils.thumbnail.getThumbnailFrameForTrackItem(self._trackItems[0])

    self._thumbnailPath = utils.thumbnail.writeThumbnailForObject(
        self._trackItems[0], options, frame)

    return self._thumbnailPath


  def getTrackItems(self):
    return self._trackItems


  def setTrackItems(self, trackItems, options=None):
    """
    Sets the ShotItems properties based on the supplied hiero.core.TrackItem.

    # Opts as per utils.track.timingsFromTrackItems and
    {
      'setShotTimings' : True
    }
    """

    options = options if options else {}

    trackItems = utils.ensureList(trackItems)

    self._trackItems = trackItems

    # Base static data on the first item
    masterItem = trackItems[0]

    self.nameHint = masterItem.name()
    self.code = masterItem.name()

    start = end = in_ = out = None
    sourceTc = inTc = None

    if options.get('setShotTimings', True):

      # This should be in one place in hiero but it's deeply embedded in the
      # export dialog where we can't easily get to it so it's just been
      # replicated in utils here for now.
      start, end, in_, out = utils.track.timingsFromTrackItems(trackItems,
          options)

      if options.get(utils.track.kTimingOption_includeSourceTimecode, True):
        sourceTc = utils.track.sourceTimecodeFromTrackItem(masterItem)
      if options.get(utils.track.kTimingOption_includeInTimecode, True):
        inTc = utils.track.inTimecodeFromTrackItem(masterItem)

    self.startFrame = start
    self.endFrame = end
    self.inFrame = in_
    self.outFrame = out
    self.sourceTimecode = sourceTc
    self.inTimecode = inTc

    ## @todo Revisit when we support resolution
    entity = utils.entity.entityFromObj(masterItem)
    if entity:
      self.setEntity(entity)


  def toLocale(self):
    """
    @localeUsage hiero.specifications.HieroTrackItemLocale
    """
    locale = None
    if self._trackItems:
      locale = specifications.HieroTrackItemLocale()
      locale.objects = self._trackItems
    return locale


  def toMetadata(self, type_=None, skip=None, force=None):

    if not force:
      force = []

    # We need to make sure we always have keys for these, so that we can
    # overwrite any metadata in the case that an in/out is missing.
    # See the base class for further explanation.
    force.extend(['inFrame', 'outFrame', 'startFrame', 'endFrame'])

    return super(HieroShotTrackItem, self).toMetadata(type_, skip, force)


  def toSpecification(self, spec=None):

    spec = super(HieroShotTrackItem, self).toSpecification(spec)

    # Make sure we set the thumbnail path if we have one
    if self._thumbnailPath:
      spec.thumbnailPath = self._thumbnailPath

    return spec


  def _readEntity(self, entity, context, skip=None):
    super(HieroShotTrackItem, self)._readEntity(entity, context, skip=skip)

    self.nameHint = entity.getName(context)


  def updateTrackItems(self, syncMeta=True):
    """

    @param syncMeta bool [True], If True, the TrackItems timings, metadata and
    other properties will also be updated from the Items properties. Otherwise,
    only the name, and entity reference will be updated.

    """

    if not self._trackItems:
      raise RuntimeError("Can't update, item has no TrackItems")

    for item in self._trackItems:
      self._updateTrackItem(item, syncMeta)


  def _updateTrackItem(self, trackItem, syncMeta=True):

    if syncMeta:
      ## @todo Update timings and other properties
      pass

    # We use the name to find the shot later, so make sure we update this
    # in case it was conformed, or adjusted by the asset management system
    if self.nameHint:
      trackItem.setName(self.nameHint)

    ## @todo Do we want to read back timecode properties etc...

    # This is where we'd tag the TackItem with the entity ref if we wanted to
    # do such a thing.


class HieroClipItem(FnAssetAPI.items.ClipItem):

  # We're not going to change the name here, as we want this to be
  # compatible with anything else that uses an image - we also don't
  # add any new properties so there is no need.
  # So, we tell the class not to be registered as an item handler.
  _factoryIgnore = True


  def __init__(self, clip=None):
    super(HieroClipItem, self).__init__()

    self._clip = None
    if clip:
      self.setClip(clip)

    self._thumbnailPath = ''


  def prepareThumbnail(self, options):
    """
    Call to create a thumbnail for this item, and store the path in the item.
    This will be set in the spec, if present later.
    """

    self._thumbnailPath = ''

    if not self._clip:
      raise RuntimeError("Unable to build a thumbnail, no Clip set")

    frame = utils.thumbnail.getThumbnailFrameForClip(self._clip)
    self._thumbnailPath = utils.thumbnail.writeThumbnailForObject(self._clip, options,
    frame)

    return self._thumbnailPath


  def getClip(self):
    return self._clip


  def setClip(self, clip):
    """
    Sets the ImageItems properties, base don the supplied hiero.core.Clip.
    """

    self._clip = clip

    ## @todo Check the below comment is still the goal, as we're not doing it
    ## right now...
    # If this clip has an entityRefrence instead of a path, we need to retrieve
    # the entity from the asset management system, and populate the information
    # from there instead, if it has a path we need to populate the information
    # from the Clip

    binItem = None
    # Annoyingly this raises rather than returning None
    try: binItem = clip.binItem()
    except: pass

    ms = clip.mediaSource()

    if ms:
      # A lot of these functions raise
      try:

        # Get the name from the parent bin item, if there is one, since that's
        # what the user sees in the UI and it's got the version number peeled off.
        ## @todo peel off the version number if taking it from the clip,
        ## But don't reimplement it here, call Hiero's function that does
        ## it so it's consistent.
        self.nameHint = binItem.name() if binItem else clip.name()

        self.path = ms.fileinfos()[0].filename()

        self.aspectRatio = ms.pixelAspect()
        self.width = ms.width()
        self.height = ms.height()

        self.enumerated = not ms.singleFile()

        self.startFrame = clip.timelineOffset()
        self.endFrame = clip.timelineOffset() + ms.duration()-1

        try: in_ = self.startFrame + clip.inTime()
        except: in_ = None
        try: out = self.startFrame + clip.outTime()
        except: out = None
        self.inFrame = in_ if in_ != self.startFrame else None
        self.outFrame = out if out != self.endFrame else None

        self.frameRate = clip.framerate().toFloat()
        self.dropFrame = clip.dropFrame()

        ## @todo validation of colourspace names
        # It errors if the media is offline...
        try: self.colorspace = clip.sourceMediaColourTransform()
        except: pass

      except Exception, e:
        FnAssetAPI.logging.debug(traceback.format_exc())
        FnAssetAPI.logging.warning("%s (%s)" % (e, clip))

    # We need to decide the meaning of an Item made from a Clip that is already
    # managed. We probably still want to read the properties from the Clip in
    # Hiero, to allow us to update the Entity if its out of date.
    # Otherwise, its harder to re-publish.

    entity = utils.entity.entityFromObj(self._clip)
    if entity:
      self.setEntity(entity, read=False)


  ## @todo do we need fromEntity here?
  def updateClip(self):

    if not self._clip:
      ## @todo Be a bit more professional here
      raise RuntimeError("Item has no Clip")

    self._updateClip(self._clip)


  def toClip(self, useExisting=True):

    if not self.path:
      return None

    ## @todo Re-visit when heiro supports media sources that can have their
    ## location chanegd once created. should really be in _updateClip

  ## @todo support useExisting

    entity = self.getEntity()
    mediaPath = entity.reference if entity else self.path
    if not mediaPath:
      raise ValueError("Unable to determine a suitable media path %s" % self)

    clip = hiero.core.Clip(mediaPath)

    return clip


  def toSpecification(self, spec=None):

    spec = super(HieroClipItem, self).toSpecification(spec)

    # Make sure we set the thumbnail path if we have one
    if self._thumbnailPath:
      spec.thumbnailPath = self._thumbnailPath

    return spec


  def _updateClip(self, clip):
    # Update the supplied clip using the attribute on the Item

    ## @todo update media source location when hiero supports it

    startFrame = self.startFrame if self.startFrame is not None else 0

    if self.inFrame is not None:
      clip.setInTime(self.inFrame - startFrame)

    if self.outFrame is not None:
      clip.setOutTime(self.outFrame - startFrame)

    if self.frameRate is not None:
      clip.setFramerate(self.frameRate)

    if self.dropFrame is not None:
      try:
        # You get a runtime error if you try and set dropframe for a frame rate
        # that doesn't support dropframe eg: 25
        clip.setDropFrame(self.dropFrame)
      except RuntimeError:
        pass

    if self.colorspace:
      ## @todo Validate/transform colourspace
      clip.setSourceMediaColourTransform(self.colorspace)

    if self._entity:
      if hasattr(clip, 'setEntityReference'):
        clip.setEntityReference(self._entity.reference)
      else:
        FnAssetAPI.logging.debug("This version of Hiero does not support "
            + "Entity Reference based clips, please update to at least 1.8v1")

    try:
      ## @todo It would be great if Hiero understood the concepts of versioning
      ## independently of the filename. As it places allsorts of requirements
      ## on the asset manager
      if self.nameHint:
        clip.setName(self.nameHint)
    except Exception as e:
      FnAssetAPI.logging.debug(e)


  def toLocale(self):
    """
    @localeUsage hiero.specifications.HieroClipLocale
    """
    locale = specifications.HieroClipLocale()
    if self._clip:
      locale.objects = [self._clip,]

    return locale


  def _readEntity(self, entity, context, skip=None):
    super(HieroClipItem, self)._readEntity(entity, context, skip=skip)

    with context.scopedOverride():
      context.locale = self.toLocale()
      name = entity.getDisplayName(context)
      versionName = entity.getVersionName(context)
      if versionName:
        self.nameHint = "%s_v%s" % (name, versionName)
      else:
        self.nameHint = name


  def toMetadata(self, type_=None, skip=None, force=None):

    if not force:
      force = []
    force.extend(('inFrame', 'outFrame', 'startFrame', 'endFrame'))

    return super(HieroClipItem, self).toMetadata(type_, skip, force)


class HieroProjectItem(FnAssetAPI.items.FileItem):
  _type = "file.hrox"

  name = TypedProperty(str, doc="The project name")


  def __init__(self, project=None):
    super(HieroProjectItem, self).__init__()

    self._project = None
    if project:
      self.setProject(project)


  def getProject(self):
    return self._project


  def setProject(self, project):
    self._project = project

    self.path = project.path()
    self.enumerated = False
    self.name = project.name()


  def toSpecification(self):
    """
    @specUsage FnAssetAPI.specifications.HieroProjectSpecification

    """
    spec = specifications.HieroProjectSpecification()
    super(HieroProjectItem, self).toSpecification(spec)
    spec.nameHint = self.name
    return spec


  def createAsset(self, workingEntity, context):
    """

    Called to publish the asset to a path managing asset system, generally
    called by utils.publishing.create.

    @param workingEntity Entity, the Entity returned by preflight

    """
    if not self._project:
      raise RuntimeError("No project set in item %s" % self)

    ## @todo Do we want to strip any entityReference stored in the projects
    ## tags here?

    path = workingEntity.resolve(context)
    if not path:
      raise FnAssetAPI.exceptions.RegistrationError("No path supplied",
          workingEntity)

    self._project.saveAs(path)
    self._project.setEditable(False)
    self.path = path

    return self


  def updateProject(self):
    # For now, we only keep a temporary ref to a projects entity, as to not
    # affect the document dirty state after publishing, but also to ensure that
    # a (re)published project doesn't then contain any invalid refs
    pass
