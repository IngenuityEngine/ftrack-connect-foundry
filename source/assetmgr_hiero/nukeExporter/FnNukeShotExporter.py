# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import FnAssetAPI

import re
import os.path
import sys, math

import hiero.core
import hiero.core.util
import hiero.core.nuke as nuke
import hiero.exporters

from hiero.exporters import FnShotExporter
from hiero.exporters import FnExternalRender

from .. import items
from .. import constants
from .. import specifications
from .. import utils as assetApiUtils

class NukeShotExporter(FnShotExporter.ShotTask):
  """
  @specUsage FnAssetAPI.specifications.NukeScriptSpecification
  @specUsage FnAssetAPI.specifications.ShotSpecification
  @localeUsage hiero.specifications.HieroNukeScriptExportLocale
  @itemUsage hiero.items.HieroShotTrackItem
  @itemUsage FnAssetAPI.items.FileItem

  """
  def __init__( self, initDict ):
    """Initialize"""
    FnShotExporter.ShotTask.__init__( self, initDict )

    self._nothingToDo = True
    self._tag = None
    self._tag_guid = None
    self._parentSequence = None

    self._targetEntity = None
    self._context = None

    ## Horrible Workaround:
    ## Because of the way collate works at the moment, it will run this task
    ## for every track item in a collated set. We only want to publish the
    ## first time around. This is a little bit nasty as the collate logic sets
    ## frame numbers in the Nuke script based on relative timings to the
    ## current item. So, the script you get is dependent on the order the tasks
    ## run in.  In standard behaviour, it seem the last task is the one that
    ## gets to write the file. So we'll use the last one instead so the scripts
    ## are the same as non-assetised behaviour.
    ## @todo Make sure the script written by each iteration are the same, or
    ## only do the work once on the 'right' TrackItem
    self._skipPublish = False

    ## @todo We have to figure out how to get a context for all tasks, and once
    ## we've done that we HAVE TO PROMISE NOT TO PUSH ACTION GROUPS across
    ## threads.

    if isinstance(self._item, hiero.core.TrackItem):
      if not self._source.isMediaPresent() and self._skipOffline:
        return

    # All clear.
    self._nothingToDo = False
    self._collate = False

    if isinstance(self._item, hiero.core.TrackItem):

      # Build list of collated shots
      self._collatedItems = self._collatedItems()

      # Only build sequence if there are multiple shots
      if  len(self._collatedItems) > 1:
        self._collate = True
        # Build the sequence of collated shots
        self._buildCollatedSequence()

        # Make sure we only publish on the last time around (see note above)
        if self._item != self._collatedItems[-1]:
          self._skipPublish = True

      # If we're requested to publish the script, see if we can find our target
      if self._preset.properties()["publishScript"]:
        self._targetEntity = self.__getTargetEntityForScript(self._item, self._context)
        if not self._targetEntity:
          FnAssetAPI.logging.warning(FnAssetAPI.l("Unable to find where to "+
            "{publish} the Nuke Script to for %r, the file will be written, "+
            "but not {published}.") % self._item)


  def _collatedItems  (self):
    """Build and return list of collated shots, the CollateTracks option includes overlapping and identically named shots.\n
      CollateSequence Option includes all shots in parent sequence"""
    collatedItems = []

    collateTime, collateName = self._preset.properties()["collateTracks"], self._preset.properties()["collateShotNames"]

    if self._preset.properties()["collateSequence"]:

      # Add all trackitems to collate list
      for track in self._sequence.videoTracks():
        for trackitem in track:
          collatedItems.append(trackitem)

    elif collateName or collateTime:

      nameMatches = [self._item]
      orderedMatches = []

      if collateName:
        # The collate tracks option will detect any trackitems on other tracks which overlap
        # so they can be included in the nuke script.
        for track in self._sequence.videoTracks():
          for trackitem in track:

            if trackitem is not self._item:

              # Collate if shot name matches.
              if trackitem.name() == self._item.name():
                nameMatches.append(trackitem)
                continue

      for track in self._sequence.videoTracks():
        for trackitem in track:

          for nameMatchTrackItem in nameMatches:

            if collateTime:

              # Starts before or at same time
              if trackitem.timelineIn() <= nameMatchTrackItem.timelineIn():
                # finishes after start
                if trackitem.timelineOut() >= nameMatchTrackItem.timelineIn():
                  orderedMatches.append(trackitem)
                  break

              # Starts after
              elif trackitem.timelineIn() > nameMatchTrackItem.timelineIn():
                # Starts before end
                if trackitem.timelineIn() < nameMatchTrackItem.timelineOut():
                  orderedMatches.append(trackitem)
                  break

            elif trackitem == nameMatchTrackItem:
              orderedMatches.append(trackitem)
              break
      collatedItems = orderedMatches
    return collatedItems

  def _buildCollatedSequence(self):
    """From the list of collated Items build a sequence, extend edge shots for handles, offset relative to custom start or master shot source frame"""
    if self._collate:


      # When building a collated sequence, everything is offset by 1000
      # This gives head room for shots which may go negative when transposed to a
      # custom start frame. This offset is negated during script generation.
      headRoomOffset = 1000

      # Build a new sequence from the collated items
      newSequence = hiero.core.Sequence(self._sequence.name())


      # Copy tags from sequence to clone
      for tag in self._sequence.tags():
        newSequence.addTag(hiero.core.Tag(tag))

      # Apply the format of the master shot to the whole sequence
      newSequence.setFormat(self._clip.format())

      offset = self._item.sourceIn() - self._item.timelineIn()
      if self._startFrame is not None:
        # This flag indicates that an explicit start frame has been specified
        # To make sure that when the shot is expanded to include handles this is still the first
        # frame, here we offset the start frame by the in-handle size
        if  self._preset.properties()["collateCustomStart"]:
          self._startFrame += self._cutHandles

        # The offset required to shift the timeline position to the custom start frame.
        offset = self._startFrame - self._item.timelineIn()


      sequenceIn, sequenceOut = sys.maxint, 0
      for trackitem in self._collatedItems:
        if trackitem.timelineIn() <= sequenceIn:
          sequenceIn = trackitem.timelineIn()
        if trackitem.timelineOut() >= sequenceOut:
          sequenceOut = trackitem.timelineOut()


      newTracks = {}
      for trackitem in self._collatedItems:
        parentTrack = trackitem.parentTrack()

        # Clone each track and add it to a dictionary, using guid as key
        if parentTrack.guid() not in newTracks:
          trackClone = hiero.core.VideoTrack(parentTrack.name())
          newTracks[parentTrack.guid()] = trackClone
          newSequence.addTrack(trackClone)

          # Copy tags from track to clone
          for tag in parentTrack.tags():
            trackClone.addTag(hiero.core.Tag(tag))

        trackItemClone = trackitem.clone()

        # extend any shots
        if self._cutHandles is not None:
          # Maximum available handle size
          handleInLength, handleOutLength = trackitem.handleInLength(), trackitem.handleOutLength()
          # Clamp to desired handle size
          handleIn, handleOut = min(self._cutHandles, handleInLength), min(self._cutHandles, handleOutLength)

          if trackItemClone.timelineIn() <= sequenceIn and handleIn:
            trackItemClone.trimIn(-handleIn)
            hiero.core.log.debug("Expanding %s in by %i frames" % (trackItemClone.name(), handleIn))
          if trackItemClone.timelineOut() >= sequenceOut and handleOut:
            trackItemClone.trimOut(-handleOut)
            hiero.core.log.debug("Expanding %s out by %i frames" % (trackItemClone.name(), handleOut))


        trackItemClone.setTimelineOut(trackItemClone.timelineOut() + headRoomOffset + offset)
        trackItemClone.setTimelineIn(trackItemClone.timelineIn() + headRoomOffset + offset)

        # Add Cloned track item to cloned track
        try:
          newTracks[parentTrack.guid()].addItem(trackItemClone)
        except Exception as e:
          clash = newTracks[parentTrack.guid()].items()[0]
          error = "Failed to add shot %s (%i - %i) due to clash with collated shots, This is likely due to the expansion of the master shot to include handles. (%s %i - %i)\n" % (trackItemClone.name(), trackItemClone.timelineIn(), trackItemClone.timelineOut(), clash.name(), clash.timelineIn(), clash.timelineOut())
          self.setError(error)
          hiero.core.log.error(error)
          hiero.core.log.error(str(e))


      handles = self._cutHandles if self._cutHandles is not None else 0
      # Use in/out point to constrain output framerange to track item range
      newSequence.setInTime(max(0, (sequenceIn + offset) - handles))
      newSequence.setOutTime((sequenceOut + offset) + handles)

      # Useful for debugging, add cloned collated sequence to Project
      #hiero.core.projects()[-1].clipsBin().addItem(hiero.core.BinItem(newSequence))

      #bin = self._sequence.binItem().parentBin()
      # Use this newly built sequence instead
      self._parentSequence = self._sequence
      self._sequence = newSequence
  #bin.addItem(hiero.core.BinItem(self._sequence))


  def updateItem (self, originalItem, localtime):
    """updateItem - This is called by the processor prior to taskStart, crucially on the main thread.\n
      This gives the task an opportunity to modify the original item on the main thread, rather than the clone."""

    timestamp = self.timeStampString(localtime)
    tag = hiero.core.Tag("Nuke Project File " + timestamp, "icons:Nuke.png")

    writePaths = []

    # Need to instantiate each of the selected write path tasks and resolve the path
    for (itemPath, itemPreset) in self._exportTemplate.flatten():
      for writePath in self._preset.properties()["writePaths"]:
        if writePath == itemPath:
          # Generate a task on same items as this one but swap in the shot path that goes with this preset.
          taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                         project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
          task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

          resolvedPath = task.resolvedExportPath()

          # Ensure enough padding for output range
          output_start, output_end = task.outputRange(ignoreRetimes=False, clampToSource=False)
          count = len(str(max(output_start, output_end)))
          resolvedPath = hiero.core.util.ResizePadding(resolvedPath, count)

          writePaths.append(resolvedPath)

    tag.metadata().setValue("tag.path", ";".join(writePaths))
    # Right now don't add the time to the metadata
    # We would rather store the integer time than the stringified time stamp
    # tag.setValue("time", timestamp)

    tag.metadata().setValue("tag.script", self.resolvedExportPath())
    tag.metadata().setValue("tag.localtime", str(localtime))

    start, end = self.outputRange()
    tag.metadata().setValue("tag.startframe", str(start))
    tag.metadata().setValue("tag.duration", str(end-start+1))

    if isinstance(self._item, hiero.core.TrackItem):
      tag.metadata().setValue("tag.sourceretime", str(self._item.playbackSpeed()))

    frameoffset = self._startFrame if self._startFrame else 0

    # Only if write paths have been set
    if len(writePaths) > 0:
      # Video file formats are not offset, so set frameoffset to zero
      if hiero.core.isVideoFileExtension(os.path.splitext(writePaths[0])[1].lower()):
        frameoffset = 0

    tag.metadata().setValue("tag.frameoffset", str(frameoffset))

    if self._cutHandles:
      tag.metadata().setValue("tag.handles", str(self._cutHandles))

    originalItem.addTag(tag)

    if self._preset.properties()["useAssets"]:
      # Allow listeners to update the item too
      manager = FnAssetAPI.Events.getEventManager()
      manager.blockingEvent(True, 'hieroToNukeScriptUpdateTrackItem', self._item, tag)

    # The guid of the tag attached to the trackItem is different from the tag instance we created
    # Get the last tag in the list and store its guid
    self._tag = originalItem.tags()[-1]
    self._tag_guid = originalItem.tags()[-1].guid()

  def _buildAdditionalNodes(self, item):
    # Callback from script generation to add additional nodes
    nodes = []

    data = self._preset.properties()["additionalNodesData"]

    itemType = None
    if isinstance(item, hiero.core.Clip):
      itemType = FnExternalRender.kPerShot
    elif isinstance(item, hiero.core.TrackItem):
      itemType = FnExternalRender.kPerShot
    elif isinstance(item, (hiero.core.VideoTrack, hiero.core.AudioTrack)):
      itemType = FnExternalRender.kPerTrack
    elif isinstance(item, hiero.core.Sequence):
      itemType = FnExternalRender.kPerSequence

    if itemType:

      if self._preset.properties()["additionalNodesEnabled"]:
        nodes.extend(FnExternalRender.createAdditionalNodes(itemType, data, item))

      if self._preset.properties()["useAssets"]:
        # Allow registered listeners to work with the script
        manager = FnAssetAPI.Events.getEventManager()
        ## @todo Assuming that we're always on a thread for now, this should be verified
        manager.blockingEvent(False, 'hieroToNukeScriptAddNodesForItem', itemType, item, nodes)

    return nodes

  def taskStep(self):
    FnShotExporter.ShotTask.taskStep(self)
    if self._nothingToDo:
      return False

    eventManager = FnAssetAPI.Events.getEventManager()
    script = nuke.ScriptWriter()

    start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
    unclampedStart = start
    hiero.core.log.debug( "rootNode range is %s %s %s", start, end, self._startFrame )

    firstFrame = start
    if self._startFrame is not None:
      firstFrame = self._startFrame

    # if startFrame is negative we can only assume this is intentional
    if start < 0 and (self._startFrame is None or self._startFrame >= 0):
      # We dont want to export an image sequence with negative frame numbers
      self.setWarning("%i Frames of handles will result in a negative frame index.\nFirst frame clamped to 0." % self._cutHandles)
      start = 0

    # Clip framerate may be invalid, then use parent sequence framerate
    framerate = self._sequence.framerate()
    dropFrames = self._sequence.dropFrame()
    if self._clip and self._clip.framerate().isValid():
      framerate = self._clip.framerate()
      dropFrames = self._clip.dropFrame()
    fps = framerate.toFloat()

    # Create the root node, this specifies the global frame range and frame rate
    rootNode = nuke.RootNode(start, end, fps)
    rootNode.addProjectSettings(self._projectSettings)
    #rootNode.setKnob("project_directory", os.path.split(self.resolvedExportPath())[0])
    script.addNode(rootNode)

    reformat = None
    # Set the root node format to default to source format
    if isinstance(self._item, hiero.core.Sequence) or self._collate:
      reformat = self._sequence.format().addToNukeScript(None)
    elif isinstance(self._item, hiero.core.TrackItem):
      reformat = self._clip.format().addToNukeScript(None)

    if isinstance(self._item, hiero.core.TrackItem):
      rootNode.addInputTextKnob("shot_guid", value=hiero.core.FnNukeHelpers._guidFromCloneTag(self._item), tooltip="This is used to identify the master track item within the script")
      inHandle, outHandle = self.outputHandles(self._retime != True)
      rootNode.addInputTextKnob("in_handle", value=int(inHandle))
      rootNode.addInputTextKnob("out_handle", value=int(outHandle))

    # This sets the format knob of the root node in the Nuke Script
    rootReformat = None
    if isinstance(self._item, hiero.core.Sequence) or self._collate:
      rootReformat = self._sequence.format().addToNukeScript(None)
    elif isinstance(self._item, hiero.core.TrackItem):
      rootReformat = self._item.parentSequence().format().addToNukeScript(None)

    rootNode.setKnob("format", rootReformat.knob("format"))


    # Add Unconnected additional nodes
    if self._preset.properties()["additionalNodesEnabled"]:
      script.addNode(FnExternalRender.createAdditionalNodes(FnExternalRender.kUnconnected, self._preset.properties()["additionalNodesData"], self._item))

    # Project setting for using OCIO nodes for colourspace transform
    useOCIONodes = self._project.lutUseOCIOForExport()

    # To add Write nodes, we get a task for the paths with the preset
    # (default is the "Nuke Write Node" preset) and ask it to generate the Write node for
    # us, since it knows all about codecs and extensions and can do the token
    # substitution properly for that particular item.
    # And doing it here rather than in taskStep out of threading paranoia.
    self._writeNodes = []

    stackId = "ScriptEnd"
    self._writeNodes.append( nuke.SetNode(stackId, 0) )

    writePathExists = False
    writePaths = self._preset.properties()["writePaths"]

    for (itemPath, itemPreset) in self._exportTemplate.flatten():
      for writePath in writePaths:
        if writePath == itemPath:
          # Generate a task on same items as this one but swap in the shot path that goes with this preset.
          taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate, project=self._project, cutHandles=self._cutHandles,
                                         retime=self._retime, startFrame=firstFrame, resolver=self._resolver, skipOffline=self._skipOffline)
          task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)
          if hasattr(task, "nukeWriteNode"):
            self._writeNodes.append( nuke.PushNode(stackId) )

            rf = itemPreset.properties()["reformat"]
            # If the reformat field has been set, create a reformat node immediately before the Write.
            if str(rf["to_type"]) == nuke.ReformatNode.kToFormat:
              if "width" in rf and "height" in rf and "pixelAspect" in rf and "name" in rf and "resize" in rf:
                format = hiero.core.Format(rf["width"], rf["height"], rf["pixelAspect"], rf["name"])
                resize=rf["resize"]
                reformat = format.addToNukeScript(None, resize=resize)
                self._writeNodes.append(reformat)
              else:
                self.setError("reformat mode set to kToFormat but preset properties do not contain required settings.")

            # Add Burnin group (if enabled)
            burninGroup = task.addBurninNodes(script=None)
            if burninGroup is not None:
              self._writeNodes.append(burninGroup)

            try:
              writeNode = task.nukeWriteNode(framerate, projectsettings=self._projectSettings)
              writeNode.setKnob("first", start)
              writeNode.setKnob("last", end)


              self._writeNodes.append(writeNode)

            except RuntimeError as e:
              # Failed to generate write node, set task error in export queue
              # Most likely because could not map default colourspace for format settings.
              self.setError(str(e))

          writePathExists = True

    # MPLEC TODO should enforce in UI that you can't pick things that won't work.
    if not writePaths:
      # Blank preset is valid, if preset has been set and doesn't exist, report as error
      self.setWarning(str("NukeShotExporter: No write node destination selected"))

    # If this flag is True, a read node pointing at the original media will be added
    # If read nodes which point at export items are selected, this flag will be set False
    originalMediaReadNode = True

    useEntityRefs = self._preset.properties().get("useAssets", False)

    for item in [self._item]:
      originalMediaReadNode = True
      if not self._collate:
        # Build read nodes for selected entries in the shot template
        readPaths = self._preset.properties()["readPaths"]
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
          for readPath in readPaths:
            if itemPath == readPath:

              # Generate a task on same items as this one but swap in the shot path that goes with this preset.
              taskData = hiero.core.TaskData(itemPreset, item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                             project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
              task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

              readNodePath = task.resolvedExportPath()
              itemStart, itemEnd = task.outputRange()
              itemFirstFrame = firstFrame
              if self._startFrame:
                itemFirstFrame = self._startFrame

              if hiero.core.isVideoFileExtension(os.path.splitext(readNodePath)[1].lower()):
                # Don't specify frame range when media is single file
                newSource = hiero.core.MediaSource(readNodePath)
                itemEnd = itemEnd - itemStart
                itemStart = 0

              else:
                # File is image sequence, so specify frame range
                newSource = hiero.core.MediaSource(readNodePath + (" %i-%i" % task.outputRange()))

              newClip = hiero.core.Clip(newSource, itemStart, itemEnd)


              originalMediaReadNode = False

              if self._cutHandles is None:
                newClip.addToNukeScript(script, firstFrame=itemFirstFrame,
                    trimmed=True, useOCIO=useOCIONodes,
                    additionalNodesCallback=self._buildAdditionalNodes,
                    nodeLabel=item.parent().name(), useEntityRefs=useEntityRefs)
              else:
                # Clone track item and replace source with new clip (which may be offline)
                newTrackItem = hiero.core.TrackItem(item.name(), item.mediaType())

                for tag in self._item.tags():
                  newTrackItem.addTag(tag)

                # Handles may not be exactly what the user specified. They may be clamped to media range
                inHandle, outHandle = 0, 0
                if self._cutHandles:
                  # Get the output range without handles
                  inHandle, outHandle = task.outputHandles()
                  hiero.core.log.debug( "in/outHandle %s %s", inHandle, outHandle )


                newTrackItem.setSource(newClip)

                # Trackitem in/out
                newTrackItem.setTimelineIn(item.timelineIn())
                newTrackItem.setTimelineOut(item.timelineOut())

                # Source in/out is the clip range less the handles.
                newTrackItem.setSourceIn(inHandle * -1)
                newTrackItem.setSourceOut((newClip.duration() -1 )- outHandle)

                #print "New trackitem (src/dst/clip) ", newTrackItem.sourceDuration(), newTrackItem.duration(), newClip.duration()

                # Add track item to nuke script
                newTrackItem.addToNukeScript(script, firstFrame=itemFirstFrame,
                    includeRetimes=self._retime,
                    retimeMethod=self._preset.properties()["method"],
                    startHandle=self._cutHandles, endHandle=self._cutHandles,
                    additionalNodesCallback=self._buildAdditionalNodes,
                    useOCIO=useOCIONodes, nodeLabel=item.parent().name(),
                    useEntityRefs=useEntityRefs)

      if originalMediaReadNode:

        if isinstance(self._item, hiero.core.Sequence) or self._collate:

          # When building a collated sequence, everything is offset by 1000
          # This gives head room for shots which may go negative when transposed to a
          # custom start frame. This offset is negated during script generation.
          offset = -1000 if self._collate else 0
          self._sequence.addToNukeScript(script,
              additionalNodesCallback=self._buildAdditionalNodes,
              includeRetimes=True, offset=offset, useOCIO=useOCIONodes,
              skipOffline = self._skipOffline, useEntityRefs=useEntityRefs)
        elif isinstance(self._item, hiero.core.TrackItem):
          clip = item.source()

          # Add a Read Node for this Clip.
          if self._cutHandles is None:
            clip.addToNukeScript(script, firstFrame=firstFrame, trimmed=True,
                additionalNodesCallback=self._buildAdditionalNodes,
                useOCIO=useOCIONodes, nodeLabel=item.parent().name(),
                useEntityRefs=useEntityRefs)
          else:
            item.addToNukeScript(script, firstFrame=firstFrame,
                includeRetimes=self._retime,
                retimeMethod=self._preset.properties()["method"],
                startHandle=self._cutHandles, endHandle=self._cutHandles,
                additionalNodesCallback=self._buildAdditionalNodes,
                useOCIO=useOCIONodes, nodeLabel=item.parent().name(),
                useEntityRefs=useEntityRefs)


    metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid()), ("hiero/shot_tag_guid", self._tag_guid) ] )

    # Add sequence Tags to metadata
    metadataNode.addMetadata([ ('"hiero/tags/' + tag.name() + '"', tag.name()) for tag in self._sequence.tags()])
    metadataNode.addMetadata([ ('"hiero/tags/' + tag.name() + '/note"', tag.note()) for tag in self._sequence.tags()])

    # Apply timeline offset to nuke output
    if isinstance(self._item, hiero.core.TrackItem):
      if self._cutHandles is None:
        # Whole clip, so timecode start frame is first frame of clip
        timeCodeNodeStartFrame = unclampedStart
      else:
        # Exporting shot with handles, adjust timecode start frame by shot trim and handle count
        timeCodeNodeStartFrame = (unclampedStart - self._item.sourceIn()) + self._cutHandles
      timecodeStart = self._clip.timecodeStart()
    else:
      # Exporting whole sequence/clip
      timeCodeNodeStartFrame = unclampedStart
      timecodeStart = self._item.timecodeStart()

    script.addNode(nuke.AddTimeCodeNode(timecodeStart=timecodeStart, fps=framerate, dropFrames=dropFrames, frame=timeCodeNodeStartFrame))
    # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
    metadataNode.addMetadata([("input/frame_rate",framerate.toFloat())])

    script.addNode(metadataNode)

    # Generate Write nodes for nuke renders.
    for node in self._writeNodes:
      script.addNode(node)
      # We do this here, rather than when its created so the event happens at a
      # suitable time, otherwise, it's called before the Read node is created.
      if node.type() == "Write" and self._preset.properties()["useAssets"]:
        ## @todo Assuming that we're always on a thread for now, this should be verified
        eventManager.blockingEvent(False, 'hieroToNukeScriptAddWrite', self._item, node.knob("file"), node, script)

    # add a viewer
    viewerNode = nuke.Node("Viewer")
    script.addNode( viewerNode )

    self._writeScript(script)

    # Nothing left to do, return False.
    return False

  def finishTask(self):
    FnShotExporter.ShotTask.finishTask(self)
    self._parentSequence = None
    self._tag = None
    self._targetEntity = None

  def outputHandles ( self, ignoreRetimes = True):
    return self._outputHandles(ignoreRetimes)

  def outputRange(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
    """outputRange(self)
      Returns the output file range (as tuple) for this task, if applicable"""
    start = 0
    end  = 0

    if isinstance(self._item, hiero.core.Sequence) or self._collate:

      start, end = 0, self._item.duration() - 1
      if self._startFrame is not None:
        start += self._startFrame
        end += self._startFrame

      try:
        start = self._sequence.inTime()
      except RuntimeError:
        # This is fine, no in time set
        pass

      try:
        end = self._sequence.outTime()
      except RuntimeError:
        # This is fine, no out time set
        pass

    elif isinstance(self._item, (hiero.core.TrackItem, hiero.core.Clip)):
      # Get input frame range
      ignoreRetimes = self._preset.properties()["method"] != "None"
      start, end = self.inputRange(ignoreHandles=ignoreHandles, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)

      if self._retime and isinstance(self._item, hiero.core.TrackItem) and ignoreRetimes:
        srcDuration = abs(self._item.sourceDuration())
        playbackSpeed = self._item.playbackSpeed()
        end = (end - srcDuration) + (srcDuration / playbackSpeed) + (playbackSpeed - 1.0)

      start = int(math.floor(start))
      end = int(math.ceil(end))

      # Offset by custom start time
      if self._startFrame is not None:
        end = self._startFrame + (end - start)
        start = self._startFrame

    return (start, end)


  def _writeScript(self, script):

    # Call callback before writing script to disk (see _beforeNukeScriptWrite definition below)
    self._beforeNukeScriptWrite(script)

    defaultPath = self.resolvedExportPath()

    # This will be None in the case that 'publishScript' is turned off
    if self._targetEntity:

      nameHint = self._nameHintFromExportPath(self._exportPath)

      # See note in __init__
      if self._skipPublish:
        FnAssetAPI.logging.debug(("NOT Publishing script for %s as we're not the"+
            " last TrackItem in the Collated list.") % self._item)
      else:
        self.__doWriteScriptToAsset(script, self._targetEntity, nameHint, defaultPath)

    else:
      self.__doWriteScript(script, defaultPath)

  def _nameHintFromExportPath(self, exportPath):
    ## Horrible version removing, we do it in pieces to make sure we
    ## dont match _{version}_ as we'd get rid of both separators
    versionFree = re.sub("[_\-.]{version}", "", exportPath)
    versionFree = re.sub("{version}[_\-.]", "", versionFree)
    versionFree = versionFree.replace("{version}", "")
    path = self.resolvePath(versionFree)
    path = os.path.splitext(path)[0]
    return os.path.basename(path)


  @FnAssetAPI.core.decorators.debugCall
  def __getTargetEntityForScript(self, item, context):

    ## @todo Do we need to always try and make this the shot, or is it actually
    ## more meaningful for the manager to get the source media? We need to look
    ## into this. There are pros and cons. Supplying the media makes more work
    ## in register(). As we try and supply the _item in the locale, then in
    ## theory this information is still available. Espeicially if in the Host
    ## we expose 'refForItem'. If we did give the Image entity, this is also a
    ## lot of work for the Manager, as it needs to check the locale - as it
    ## could be a comp script for Write node, which has a completely different
    ## meaning.
    ## For now, we'll attempt to find the Shot or nothing, to make their lives
    ## easier! Means its important they implement ParentGroupingRelationship
    ## properly though.
    entity = None

    session = FnAssetAPI.SessionManager.currentSession()
    if not session:
      return None

    # If the item in managed, the simply get its entity ref - as its a
    # TrackItem, it should be the applicable shot, or nothing.
    entity = assetApiUtils.entity.entityFromObj(item)

    if not entity and isinstance(item, hiero.core.TrackItem):
      # Try and find a shot by looking under a shot parent (sequence) that we
      # might already know about, for a shot with this name
      sequenceEntity = assetApiUtils.defaults.getDefaultParentEntityForShots(
        [item,], context)

      if sequenceEntity:
        shotItem = items.HieroShotTrackItem(item)
        shotSpec = shotItem.toSpecification()
        # This always returns an array of arrays
        shots = sequenceEntity.getRelatedEntities([shotSpec,], context=context)[0]
        if shots:
          entity = shots[0]

    if not entity:
      # Finally try to fall back and find an asset underneath
      anEntity = assetApiUtils.entity.anEntityFromObj(item, includeChildren=True,
          includeParents=False)

      if anEntity:
        shotSpec = FnAssetAPI.specifications.ShotSpecification()
        shots = anEntity.getRelatedEntities([shotSpec,], context=context)[0]
        if shots:
          entity = shots[0]

    return entity


  def __doWriteScript(self, script, path):
      hiero.core.log.debug( "Writing Script to: %s", path )
      script.writeToDisk(path)
      return path


  def __doWriteScriptToAsset(self, script, targetEntity, nameHint, defaultPath):

    # we use a standard file item to take care of the path manipulation/hints
    fileItem = FnAssetAPI.items.FileItem()
    fileItem.path = defaultPath
    spec = FnAssetAPI.specifications.NukeScriptSpecification()
    spec = fileItem.toSpecification(spec)
    # Override the name hint - as it will have a version number in etc...
    ## @todo Whats a good name here?
    spec.nameHint = nameHint if nameHint else "compScript"

    def workFn(path):
      return self.__doWriteScript(script, path if path else defaultPath)

    if not self._context:
      session = FnAssetAPI.SessionManager.currentSession()
      self._context = session.createContext()

    with self._context.scopedOverride():

      self._context.locale = specifications.HieroNukeScriptExportLocale()
      self._context.locale.role = constants.kHieroExportRole_Comp
      self._context.locale.scope = constants.kHieroExportScope_TrackItem
      self._context.locale.objects = [self._item,]

      entity = assetApiUtils.publishing.publishSingle(workFn, spec, targetEntity)

      # We can't do this up front in updateItem, as we don't know the final
      # entity reference So we have to cheat a bit, as were now in another
      # thread...
      def setScriptMetadata():
        self._tag.metadata().setValue("tag.script", entity.reference)

      hiero.core.executeInMainThreadWithResult(setScriptMetadata)


  def _beforeNukeScriptWrite(self, script):
    """ Call-back method introduced to allow modifications of the script object before it is written to disk.
    Note that this is a bit of a hack, please speak to the AssetMgrAPI team before improving it. """

    if self._preset.properties()["useAssets"]:
      # Allow registered listeners to work with the script
      manager = FnAssetAPI.Events.getEventManager()
      ## @todo Assuming that we're always on a thread for now, this should be verified
      manager.blockingEvent(False, 'hieroToNukeScriptBeforeWrite', self._item, script)


