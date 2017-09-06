import traceback

import FnAssetAPI
from FnAssetAPI.decorators import ensureManager
from FnAssetAPI.contextManagers import ScopedProgressManager

from QtExt import QtGui, QtWidgets, QtCore

import utils
from BuildAssetTrackDialog import BuildAssetTrackDialog
from managerActions import ManagerPolicyDependentAction

from .. import utils as cmdUtils
from .. import specifications

import hiero.core
from hiero.ui.BuildExternalMediaTrack import BuildTrackActionBase, BuildTrack


__all__ = ['BuildAssetTrackAction', 'RefreshAssetTrackAction' ]


## @todo set the button state based on a present track name/etc....


class BuildAssetTrackAction(BuildTrackActionBase):
  """
  @specUsage FnAssetAPI.specifications.WorkflowRelationship
  @localeUsage hiero.specifications.HieroTimelineLocale

  """
  kTrackTagName = 'buildAssetTrackActionData'

  def __init__(self, name="From {published} {manager} Assets", parent=None, interactive=True):
    super(BuildAssetTrackAction, self).__init__(name)

    self._name = name

    if parent:
      self.setParent(parent)

    # Disable version tracking in the base class, there are
    # no accessors for this at present...
    self._useMaxVersions = False

    self.__interactive = interactive
    self.__trackItems = []
    # This is used for persistence, and (attempts to) hold a storable
    # persistent reference to the trackItems we had.
    self.__trackItemIdentifiers = []

    self.__criteria = ''
    self.__trackName = ''
    self.__ignoreClips = True
    self.__parentEntity = None
    self.__replaceOverlapping = False

    self.__trackItemReferences = {}

    self.__context = None

    session = FnAssetAPI.SessionManager.currentSession()
    if session:
      session.configureAction(self, addIcon=True)
    self.managerChanged()


  @cmdUtils.logExceptions
  def doit(self):
    super(BuildAssetTrackAction, self).doit()


  def setTrackItems(self, trackItems):
    self.__trackItems = trackItems
    self.__trackItemIdentifiers = []

  def getTrackItems(self):
    # This is called by the base class, and the result passed to configure
    if self.__trackItems:
      return self.__trackItems
    else:
      return super(BuildAssetTrackAction, self).getTrackItems()

  ## @name Options
  ## @{

  def setInteractive(self, interactive):
    self.__interactive = interactive

  def getInteractive(self):
    return self.__interactive


  def setCriteria(self, criteria):
    self.__criteria = criteria

  def getCriteria(self):
    return self.__criteria


  def setTrackName(self, trackName):
    self.__trackName = trackName

  def getTrackName(self):
    return self.__trackName


  def setIgnoreClips(self, ignore):
    self.__ignoreClips = ignore

  def getIgnoreClips(self):
    return self.__ignoreClips


  def setParentEntity(self, entity):
    self.__parentEntity = entity

  def getParentEntity(self):
    return self.__parentEntity


  def setReplaceOverlapping(self, replace):
    self.__replaceOverlapping = replace

  def getOverlapping(self):
    return self.__replaceOverlapping


  def setOptions(self, options):
    self.__trackName = options.get('trackName', self.__trackName)
    self.__criteria = options.get('criteriaString', self.__criteria)
    self.__ignoreClips = options.get('ignoreClips', self.__ignoreClips)
    self.__parentEntity = options.get('shotParentEntity', self.__parentEntity)
    self.__interactive = options.get('interactive', self.__interactive)
    self.__replaceOverlapping = options.get('replaceOverlapping',
        self.__replaceOverlapping)

  def getOptions(self):
    return {
      'trackName' : self.__trackName,
      'criteriaString' : self.__criteria,
      'ignoreClips' : self.__ignoreClips,
      'shotParentEntity' : self.__parentEntity,
      'interactive' : self.__interactive,
      'replaceOverlapping' : self.__replaceOverlapping
    }


  def reset(self):
    self.__trackName = ''
    self.__criteria = ''
    self.__ignoreClips = True
    self.__parentEntity = None
    self.__interactive = True
    self.__replaceOverlapping = False
    self.__context = None

  ## @}

  ## @name Persistence
  ## @{

  def serialize(self):

    data = self.getOptions()

    ref = ''
    if self.__parentEntity:
      ref = self.__parentEntity.reference

    del data['shotParentEntity']
    data['shotParentEntityReference'] = ref

    data['sourceTrackItemIdentifiers'] = self.__trackItemIdentifiers

    return repr(data)


  def restore(self, serializedString, sequence):

    data = eval(serializedString)

    entity = None
    ref = data.get('shotParentEntityReference', '')
    if ref:
      entity = FnAssetAPI.SessionManager.currentSession().getEntity(ref)
    data['shotParentEntity'] = entity

    self.setOptions(data)

    sourceTrackItemIds = data.get('sourceTrackItemIdentifiers', [])
    if sourceTrackItemIds:

      trackItems = cmdUtils.track.getTrackItemsFromIdentifiers(sourceTrackItemIds, sequence)

      if len(trackItems) != len(sourceTrackItemIds):
        FnAssetAPI.warning(("Unable to find all of the original TrackItems "
          +"used to build the track (%d or %d found)")
            % (len(trackItems), len(sourceTrackItemIds)))

      self.setTrackItems(trackItems)

  ## @}


  @ensureManager
  def configure(self, project, selection, context=None):


    # Called by the base class, to do any preparatory work, etc...
    # For now, well figure out any un-assetised shots

    # Presently, we build a track using the references of any managed clips in
    # the track items.
    # If there are no managed clips, or the user has chosen to ignore clips,
    # then we look for matching shots, similar to the way they are matched in
    # create shots.

    ## @todo Filter to Video Tracks?

    # Keep track of the source track items, and attempt to form some long-term
    # way of addressing them (for refresh)
    self.__trackItems = selection
    self.__trackItemIdentifiers = cmdUtils.track.getTrackItemIdentifiers(selection)

    if not selection:
      return False

    session = FnAssetAPI.SessionManager.currentSession()
    manager = session.currentManager()
    if not manager:
      return False

    l = FnAssetAPI.l


    if not context:
      context = session.createContext()

    items = cmdUtils.object.trackItemsToShotItems(selection)

    context.access = context.kReadMultiple
    context.retention = context.kPermanent
    context.locale = specifications.HieroTimelineLocale()
    context.locale.objects = selection

    if self.__ignoreClips and not self.__parentEntity:

      # If we're interactive, figure out a default entity ref if we don't have one
      if self.__interactive:
        entity = cmdUtils.defaults.getDefaultParentEntityForShots(selection, context)
        if entity:
          self.__parentEntity = entity
      else:
        raise RuntimeError(FnAssetAPI.l("No suitable parent entity selected to"
            +" look for {shot}s under"))

    # If we're interactive, then show a Dialog, else assume they've already
    # been configured
    if self.__interactive:
      if not self.__getOptsWithDialog(selection, context):
        return False

    ## @todo figure out if we always want to present overlap options

    # Check to see if we have anything lying in the way on our target track.
    # We do this in interactive mode or not, because overlapping may changed
    track = None

    parentTrack = selection[0].parent()
    if parentTrack:
      sequence = parentTrack.parent()
      if sequence:
        track = cmdUtils.track.getTracksInSequence(sequence).get(self.__trackName, None)

    if track:
      matching, overlapped = cmdUtils.track.getMatchingAndOverlappingTrackItems(self.__trackItems, track)
      if overlapped:
        if not self._getExistingItemOverlapOptions(track, overlapped):
          return False

    with ScopedProgressManager(1) as progress:
      progress.startStep(l("Looking for related {assets}"))
      newRefs = self.__getRelatedReferences(items, context)
      progress.finishStep()

    # See if we have any, newRefs is a list of lists
    if not cmdUtils.listHasItems(newRefs):
      if self.__interactive:
        return self._noItemsOptionsPrompt()
      else:
        FnAssetAPI.logging.warning("No matching assets found to build a track from.")
        return False

    # Build a map against track items
    self.__trackItemReferences = {}
    for i,r in zip(items, newRefs):
      if r:
        self.__trackItemReferences[i.getTrackItems()[0]] = r

    if self.__trackItemReferences:
      # As we're going head, store the context
      self.__context = context
      return True

    else:
      return False


  def getExternalFilePaths(self, trackItem):
    ref = self.__trackItemReferences.get(trackItem, None)
    return [ref,] if ref else None


  def trackName(self):
    return self.__trackName if self.__trackName else "New Track"


  def processExistingTrackItems(self, selection, sequence, project):

    # Because we're multi-purposing this action, so that it can deal with the
    # target track existing, we need to pre-process the any matching track
    # items, and remove them from the work list (selection).

    track =  cmdUtils.track.getTracksInSequence(sequence).get(self.__trackName, None)
    if not track:
      return

    matching, overlapped = cmdUtils.track.getMatchingAndOverlappingTrackItems(
        selection, track)

    self._processOverlappingItems(track, overlapped, selection)
    self._processMatchingItems(track, matching, selection, project, self.__context)


  def _noItemsOptionsPrompt(self):

    l = FnAssetAPI.l

    msgBox = QtGui.QMessageBox()
    msgBox.setText(l("No matching {assets} were found to build the track from."))
    msgBox.setInformativeText(l("Do you wish to keep the empty track (%s) "+
      "anyway? It can be refreshed later as {published} {assets} become "+
      "available.") % self.__trackName)
    msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

    return msgBox.exec_() == QtGui.QMessageBox.Yes



  def _processMatchingItems(self, track, matching, selection, project, context=None):

    sourceTrackItems = matching.keys()
    targetTrackItems = [ matching[i] for i in sourceTrackItems ]

    items = cmdUtils.object.trackItemsToShotItems(sourceTrackItems)
    newRefs = self.__getRelatedReferences(items, context)

    for target, ref in zip(targetTrackItems, newRefs):
      if not ref:
        ## @todo Should we delete/warn here?
        continue

      bin = BuildTrack.FindOrCreateBin(project, track.name())

      # Find/make a new clip
      newClip = cmdUtils.bin.findOrCreateClipInBin(ref, bin, context)
      target.setSource(newClip)


      # Remove these from the selection, so that the standard build track doesn't
      # do anything
      for t in sourceTrackItems:
        selection.remove(t)


  def _processOverlappingItems(self, track, overlapped, selection):

    if self.__replaceOverlapping:
      # Delete the TrackItem, so standard Build Track can work
      for items in overlapped.values():
        for i in items:
          track.removeItem(i)
    else:
      # Skip the overlapped shots - remove from selection to stop building
      for i in overlapped.keys():
        selection.remove(i)


  def _buildTrack(self, selection, sequence, project):

    with ScopedProgressManager(2) as progress:

      progress.startStep("Checking existing Clips...")

      # pre-build any items that already exist
      self.processExistingTrackItems(selection, sequence, project)

      progress.finishStep()

      progress.startStep("Building new Clips...")

      # This doesn't return the new track :(
      super(BuildAssetTrackAction, self)._buildTrack(selection, sequence, project)

      progress.finishStep()

    tracks = cmdUtils.track.getTracksInSequence(sequence)
    track = tracks.get(self.__trackName, None)
    if track is not None:
      # Tag the data on the track
      strRepr = self.serialize()
      cmdUtils.tag.setAssetTagField(track, self.kTrackTagName, strRepr)
    else:
      FnAssetAPI.logging.error(("Unable to find the track we just made (%s) "
          +"unable to tag the track for refresh.") % self.__trackName)


  def __getOptsWithDialog(self, selection, context=None):

    dialog = BuildAssetTrackDialog(context=context)

    dialog.setSelection(selection)

    # Update dialog if we have any options already known

    if self.__trackName:
      dialog.setTrackName(self.__trackName)

    if self.__parentEntity:
      dialog.setShotParentEntiy(self.__parentEntity)

    if self.__ignoreClips:
      dialog.setIgnoreClips(self.__ignoreClips)

    if self.__criteria:
      dialog.setCriteriaString(self.__criteria)

    if not dialog.exec_():
      return False

    self.__trackName = dialog.getTrackName()
    self.__criteria = dialog.getCriteriaString()
    self.__ignoreClips = dialog.getIgnoreClips()

    if self.__ignoreClips:
      self.__parentEntity = dialog.getShotParentEntity()
      cmdUtils.defaults.setDefaultParentEntityForShots(self.__parentEntity, selection)

    else:
      self.__parentEntity = None

    return True


  def __getRelatedReferences(self, items, context=None):

    if not self.__criteria:
      raise RuntimeError(FnAssetAPI.l("No criteria specified to find clips"))

    relationship = FnAssetAPI.specifications.WorkflowRelationship()
    relationship.criteria = self.__criteria

    if not context:
      context = FnAssetAPI.SessionManager.currentSession().createContext()

    with context.scopedOverride():

      context.access = context.kReadMultiple
      context.retention = context.kPermanent
      context.locale = specifications.HieroTimelineLocale()
      context.locale.objects = [i.getTrackItems()[0] for i in items]

      parentEntity = self.__parentEntity if self.__ignoreClips else None

      return cmdUtils.shot.getRelatedRefrencesForManagedHieroShotTrackItems(items,
            relationship, parentEntity, context)


  def _getExistingItemOverlapOptions(self, track, overlapping):

    count = len(overlapping)

    allOverlapping = []
    for items in overlapping.values():
      allOverlapping.extend(items)
    allOverlapping = [i.name() for i in allOverlapping]

    msgBox = QtGui.QMessageBox()
    msgBox.setText("TrackItems overlap.")
    msgBox.setInformativeText(("%d of your chosen Shots are overlapped by "+
      "existing items on the target track '%s'.") % (count, track.name()))

    msgBox.setDetailedText("The following Shots overlap your chosen shots:\n%s"
      % ", ".join(allOverlapping))

    replace = msgBox.addButton("Replace", msgBox.AcceptRole)
    cancel = msgBox.addButton("Cancel", msgBox.RejectRole)
    msgBox.addButton("Skip", msgBox.NoRole)

    msgBox.exec_()
    button = msgBox.clickedButton()

    if button == cancel:
      return False

    elif button == replace:
      self.__replaceOverlapping = True

    else:
      self.__replaceOverlapping = False

    return True


  def buildShotFromFiles(self, files, name, sequence, track, bin, originalTrackItem, expectedStartTime, expectedDuration, expectedHandles, expectedOffset):

    if not files:
      return

    entityRef = files[-1]

    manager = FnAssetAPI.SessionManager.currentManager()

    if not manager or not manager.isEntityReference(entityRef, self.__context):
      # If we're not an entity reference, fall back on the standard one
      return super(BuildAssetTrackAction, self).buildShotFromFiles(files, name, sequence, track, bin, originalTrackItem, expectedStartTime, expectedDuration, expectedHandles, expectedOffset)

    try:

      # Try to find an existing clip in the bin so we don't end up with duplicates
      clip = cmdUtils.bin.findOrCreateClipInBin(entityRef, bin, self.__context)

      # The media source might have already existed but been offline, in which case it needs to be refreshed.
      if clip:
        clip.rescan()

    # Catch errors creating the media source.  Since we should be able to open anything that Nuke can render,
    # the most likely reason for failure is that it's a movie format and rendering isn't finished.
    except Exception as e:
      tb = traceback.format_exc()
      FnAssetAPI.logging.debug(tb)
      self._errors.append( "Could not create clip for %s.  Check that the file has finished rendering. %s" % (file, e) )
      return

    trackItem = self._buildTrackItem(name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedHandles, expectedOffset )

    # Add to track
    track.addTrackItem(trackItem)

    # Tell anything listening
    self.trackItemAdded(trackItem, track, originalTrackItem)


  ## @name UI additions
  ## @{

  def managerChanged(self):
    expanded = FnAssetAPI.l(self._name)
    self.setText(expanded)


  def setSelection(self, selection):
    ## @todo Should we be using the passed selection here?
    trackItems = filter(lambda i : isinstance(i, hiero.core.TrackItem), selection)
    policy = cmdUtils.policy.clipPolicy(forWrite=False) & FnAssetAPI.constants.kIgnored
    self.setEnabled(policy and trackItems)

  ## @}



class RefreshAssetTrackAction(ManagerPolicyDependentAction):

  def __init__(self, parent=None):

    name = "Scan for new {manager} {assets}"
    spec = FnAssetAPI.specifications.ImageSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kRead

    super(RefreshAssetTrackAction, self).__init__(name, spec, context, parent=parent)

    self.triggered.connect(self.doit)


  def setSelection(self, selection):
    ## @todo Should we be using the passed selection?
    tracks = self.getApplicableTracks()
    self.setEnabled(bool(tracks) and self._allowedByPolicy)


  def doit(self):
    tracks = self.getApplicableTracks()
    for t in tracks:
      refreshAssetTrack(t)


  def getApplicableTracks(self, selection=None):

    if not selection:
      view = hiero.ui.activeView()
      if hasattr(view, 'selection'):
        selection = view.selection()
      else:
        return []

    tracks = []

    for item in selection:
      if isinstance(item, hiero.core.VideoTrack):
        data = cmdUtils.tag.getAssetTagField(item, BuildAssetTrackAction.kTrackTagName)
        if data:
          tracks.append(item)

    return tracks



def refreshAssetTrack(track):

  data = cmdUtils.tag.getAssetTagField(track, BuildAssetTrackAction.kTrackTagName)
  if not data:
    FnAssetAPI.logging.error("The track %s is not tagged with asset track data"
        % track.name())
    return

  sequence = track.parent()

  action = BuildAssetTrackAction()
  action.restore(data, sequence)
  # make sure we're not interactive
  action.setInteractive(False)
  action.doit()
