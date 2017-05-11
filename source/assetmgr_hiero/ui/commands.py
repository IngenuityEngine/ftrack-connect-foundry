from QtExt import QtGui, QtWidgets, QtCore

import FnAssetAPI
import FnAssetAPI.items
from FnAssetAPI.decorators import ensureManager

import hiero.core
import hiero.ui

import utils

from .. import commands
from .. import specifications
from .. import utils as cmdUtils


## @todo Once we have finalised the UI splits - we should make sure there is no
## logic left in the UI commands, so thats its still easy to script.


@cmdUtils.logExceptions
def linkToSequenceUI(hieroSequence, context=None, parent=None):

  if parent is None:
    parent = hiero.ui.mainWindow()

  ## @todo sort out setting the current project as a default
  session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  with context.scopedOverride():
    context.acces = context.kWriteMultiple

  specification = FnAssetAPI.specifications.ShotSpecification()

  browser = FnAssetAPI.ui.dialogs.TabbedBrowserDialog.buildForSession(
      specification, context, parent=parent)

  existing = cmdUtils.defaults.getDefaultParentEntityForShots(hieroSequence,
      context)
  if existing:
    browser.setSelection([existing.reference,])

  if not browser.exec_():
    return None

  newRef = browser.getSelection()[0]

  entity = session.getEntity(newRef, context=context)
  if entity:
    cmdUtils.defaults.setDefaultParentEntityForShots(entity, hieroSequence)
  return entity



@cmdUtils.logExceptions
def openPublishedProjectUI(context=None, parent=None):
  """

  @localeUsage FnAssetAPI.specifications.DocumentLocale

  """

  if parent is None:
    parent = hiero.ui.mainWindow()

  ## @todo sort out setting the current project as a default
  session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  with context.scopedOverride():

    context.access = context.kRead
    context.retention = context.kPermanent
    context.locale = FnAssetAPI.specifications.DocumentLocale()

    ## @todo set locationHint from the current project

    selection = utils.browseForProject(title="Open Project",
        button="Open", locale=context.locale, parent=parent)

    if not selection:
      return None

    return commands.openPublishedProject(selection[0], context=context)


def _getProjectOpenOptions(parent=None):

  l = FnAssetAPI.l

  if parent is None:
    parent = hiero.ui.mainWindow()

  msgBox = QtGui.QMessageBox(parent=parent)
  msgBox.setText(l("{published} Projects can't be opened directly."))
  msgBox.setInformativeText("This is to avoid changing the asset itself by "
      +"saving. Would you like to Save a Copy or open read-only?")

  saveAs = msgBox.addButton("Save As...", msgBox.AcceptRole)
  readOnly = msgBox.addButton("Read Only", msgBox.NoRole)

  # Had some issues with StandardButton .vs. AbstractButton
  msgBox.addButton("Cancel", msgBox.RejectRole)

  msgBox.exec_()
  button = msgBox.clickedButton()

  if button == saveAs:
    return 'saveas'
  elif button == readOnly:
    return 'readonly'
  else:
    return ''


def genericPublishProjectUI(context=None, parent=None, projects=None):

  projects = projects if projects else []

  if not projects:
    # Try to find some projects in the selection
    activeView = hiero.ui.activeView()
    if hasattr(activeView, 'selection'):
      projects = cmdUtils.object.projectsFromSelection(activeView.selection())

  if projects:
    return publishProjectsUI(projects, context, parent=parent)
  else:
    FnAssetAPI.logging.error("Sorry, unable to find a project from the "+
        "current selection. We're making this better, but for now, please "+
        "try selecting something on a track...")


@ensureManager
@cmdUtils.logExceptions
def publishProjectsUI(projects, context=None, parent=None):
  """
  @localeUsage FnAssetAPI.specifications.DocumentLocale
  """

  if not projects:
    return None

  if parent is None:
    parent = hiero.ui.mainWindow()

  session = FnAssetAPI.SessionManager.currentSession()

  if not context:
    context = session.createContext()

  context.access = context.kWriteMultiple if len(projects) > 1 else context.kWrite
  context.locale = FnAssetAPI.specifications.DocumentLocale()

  verb = FnAssetAPI.l("{publish}")
  title = FnAssetAPI.l("{publish} Project")

  # See if we have a default destination, if we determine it from the project
  # itself, we set the location to make it easy to version up. If we have to go
  # figure it, just set it as a hint

  refHint = None
  setLocation = False
  if len(projects) == 1:
    # We use the temp asset tag as it doesn't mess with the document state
    refHint = cmdUtils.tag.getTemporaryAssetTagField(projects[0], 'entityReference', None)
    setLocation = True if refHint else False

  if not refHint:
    entity = cmdUtils.defaults.getDefaultParentEntityForProjects(projects, context)
    if entity:
      refHint = entity.reference
      # We don't want to set the location - as we dont know the validity of
      # this - it might be some indirect or non-existent place as it didnt come
      # from the project directly
      setLocation = False

  selection = utils.browseForProject(locationHint=refHint,
      setLocation=setLocation, title=title, button=verb, context=context,
      parent=parent)

  if not selection:
    return None

  targetEntity = session.getEntity(selection[0], context)
  cmdUtils.defaults.setDefaultParentEntityForProjects(targetEntity, projects)

  return commands.publishProjects(projects, targetEntity, context)



@cmdUtils.logExceptions
def importClipsUI(target=None, context=None, parent=None):
  """
  @specUsage FnAssetAPI.specifications.ImageSpecification
  @localeUsage hiero.specifications.HieroBinLocale
  """

  from FnAssetAPI.ui.dialogs import TabbedBrowserDialog

  if parent is None:
    parent = hiero.ui.mainWindow()

  session =  FnAssetAPI.SessionManager.currentSession()
  if not session:
    FnAssetAPI.logging.error("No Asset Management Session")
    return []

  if not context:
    context = session.createContext()

  context.access = context.kReadMultiple
  context.retention = context.kPermanent
  context.locale = specifications.HieroBinLocale()

  ## @todo Fill in with valid extensions, etc...
  spec = FnAssetAPI.specifications.ImageSpecification()

  browser = TabbedBrowserDialog.buildForSession(spec, context, parent=parent)
  browser.setWindowTitle("Import Clips")
  browser.setAcceptButtonTitle("Import")

  # Find a default entity
  defaultEntity = cmdUtils.defaults.getDefaultParentEntityForClips(target, context)
  if defaultEntity:
    browser.setSelection(defaultEntity.reference)

  if browser.exec_():
    selection = browser.getSelection()

    # Store a new default location
    cmdUtils.defaults.getDefaultParentEntityForClips(selection[0], target)

    return commands.importClips(selection, target, context)
  else:
    return []



@cmdUtils.logExceptions
def publishClipsUI(clips, context=None, parent=None):
  """
  @specUsage FnAssetAPI.specifications.ImageSpecification
  @localeUsage hiero.specifications.HieroBinLocale
  """
  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    FnAssetAPI.logging.error("No Asset Management Session")
    return

  if parent is None:
    parent = hiero.ui.mainWindow()

  if not context:
    context = session.createContext()

  with context.scopedOverride():
    context.access = context.kWriteMultiple if len(clips) > 1 else context.kWrite

    context.locale = specifications.HieroBinLocale()
    context.locale.objects = clips

    specification = FnAssetAPI.specifications.ImageSpecification()

    clipItems = cmdUtils.object.clipsToHieroClipItems(clips)

    from itemDialogs import ClipPublishDialog
    dialog = ClipPublishDialog(specification, context, parent=parent)
    dialog.setItems(clipItems)

    # Find a default entity
    defaultEntity = cmdUtils.defaults.getDefaultParentEntityForClips(clips, context)
    if defaultEntity:
      dialog.setTargetEntityRefrence(defaultEntity.reference)

    result = dialog.exec_()
    if result:

      targetEntityRef = dialog.getTargetEntityReference()
      targetEntity = session.getEntity(targetEntityRef)

      # Store a default
      ## @todo We might want to get the parent grouping here
      cmdUtils.defaults.setDefaultParentEntityForClips(targetEntity, clips)

      options = dialog.getOptions()
      context.managerOptions = options.get('managerOptions', {})

      ignorePublished = options.get('ignorePublishedClips', True)

      clipItems = commands.publishClips(clips, targetEntity, context,
          ignorePublished)

      if options.get('usePublishedClips', False):
        # The items will have been updated with the entity they created
        for i in clipItems:
          i.updateClip()

      return clipItems
    else:
      return []



@cmdUtils.logExceptions
def createShotsFromTrackItemsUI(trackItems, context=None, parent=None):
  """

  @param trackItems list(hiero.core.TrackItem) Should be sorted in time order.

  @localeUsage hiero.specifications.HieroTimelineLocale

  """
  if not trackItems:
    return []

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()
  if not manager:
    FnAssetAPI.loggin.error("No Asset Manager has been chosen.")
    return

  managerOpsKey = cmdUtils.defaults.managerSpecificKey('managerOptionsCreateShot')

  if parent is None:
    parent = hiero.ui.mainWindow()

  duplicates = cmdUtils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    FnAssetAPI.logging.error(("There are duplicate Shot names in your selection, "
      + "please make sure any identically named Shots are adjacent or "
      + "overlapping so they can be combined.  - %s.")
        % ", ".join(duplicates))
    return []

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  ## @todo There is probably a better place for this
  context.locale = specifications.HieroTimelineLocale()
  context.locale.objects = trackItems

  from CreateShotsDialog import CreateShotsDialog
  dialog = CreateShotsDialog(context, parent=parent)
  dialog.setTrackItems(trackItems)

  sequence = None
  if hasattr(trackItems[0], 'sequence'):
    sequence = trackItems[0].sequence()
  if sequence:

    # See if we have any default timing options
    savedOpts = cmdUtils.defaults.getDefaultsFromObjTag(sequence,
        cmdUtils.defaults.kTrackItemTimingOptionsKey)

    # See if we have any manager options
    managerOpts = cmdUtils.defaults.getDefaultsFromObjTag(sequence, managerOpsKey)
    savedOpts['managerOptionsShot'] = managerOpts

    dialog.setOptions(savedOpts)

  # Figure out a default entity ref if we don't have one
  entity = cmdUtils.defaults.getDefaultParentEntityForShots(trackItems, context)
  if entity:
    opts = { 'targetEntityRef' : entity.reference }
    dialog.setOptions(opts)

  result = dialog.exec_()
  if not result:
    return []

  options = dialog.getOptions()

  # Prepare some to store as persistent options
  timingOpts = cmdUtils.track.filterToTimingOptions(options)
  timingOpts['setShotTimings'] = options.get('setShotTimings', True)
  managerOpts = options.get('managerOptionsShot', {})

  FnAssetAPI.logging.debug("CreateShotDialog options: %s" % options)

  with session.scopedActionGroup(context):

    targetEntityRef = options['targetEntityRef']
    # This must already exist since we're about to ask for the shots
    # underneath it to see what we already have compared to what we've
    # been given to publish.
    targetEntity = session.getEntity(targetEntityRef, mustExist=True)

    # Store the last used someplace relevant to the trackItems so next
    # time we do this, we default to the same target entity for these guys.
    cmdUtils.defaults.setDefaultParentEntityForShots(targetEntity, trackItems)
    if sequence:
      cmdUtils.defaults.setDefaultsInObjTag(sequence,
          cmdUtils.defaults.kTrackItemTimingOptionsKey, timingOpts)
      cmdUtils.defaults.setDefaultsInObjTag(sequence, managerOpsKey,
          managerOpts)

    context.managerOptions = options.get('managerOptionsShot', {})

    shotItems = commands.createShotsFromTrackItems(trackItems,
        targetEntity, adoptExistingShots=False,
        updateConflictingShots=False, context=context,
        trackItemOptions=timingOpts, linkToEntities=True,
        coalesseByName=True)

  return shotItems



@cmdUtils.logExceptions
def updateShotsFromTrackItemsUI(trackItems, context=None, parent=None):
  """

  @param trackItems list(hiero.core.TrackItem) Should be sorted in time order.

  @localeUsage hiero.specifications.HieroTimelineLocale

  """
  if not trackItems:
    return []

  if parent is None:
    parent = hiero.ui.mainWindow()

  duplicates = cmdUtils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    FnAssetAPI.logging.error(("There are duplicate Shot names in your selection, "
      + "please make sure any identically named Shots are adjacent or "
      + "overlapping so they can be combined.  - %s.")
        % ", ".join(duplicates))
    return []

  session = FnAssetAPI.SessionManager.currentSession()
  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  ## @todo There is probably a better place for this
  context.locale = specifications.HieroTimelineLocale()
  context.locale.objects = trackItems

  from UpdateShotsDialog import UpdateShotsDialog
  dialog = UpdateShotsDialog(context, parent=parent)
  dialog.setTrackItems(trackItems)

  # See if we have any default timing options
  sequence = None
  if hasattr(trackItems[0], 'sequence'):
    sequence = trackItems[0].sequence()
  if sequence:
    timingOpts = cmdUtils.defaults.getDefaultsFromObjTag(sequence,
        cmdUtils.defaults.kTrackItemTimingOptionsKey)
    dialog.setOptions(timingOpts)

  # Figure out a default entity ref if we don't have one
  entity = cmdUtils.defaults.getDefaultParentEntityForShots(trackItems, context)
  if entity:
    opts = { 'targetEntityRef' : entity.reference }
    dialog.setOptions(opts)

  result = dialog.exec_()
  if not result:
    return []

  ## @todo Save the options here in user prefs or something, and reset them
  ## next time? So they're sticky?

  options = dialog.getOptions()
  timingOpts = cmdUtils.track.filterToTimingOptions(options)
  timingOpts['setShotTimings'] = options.get('setShotTimings', True)
  FnAssetAPI.logging.debug("CreateShotDialog options: %s" % options)

  with session.scopedActionGroup(context):

    targetEntityRef = options['targetEntityRef']
    # This must already exist since we're about to ask for the shots
    # underneath it to see what we already have compared to what we've
    # been given to publish.
    targetEntity = session.getEntity(targetEntityRef, mustExist=True)

    # Store the last used someplace relevant to the trackItems so next
    # time we do this, we default to the same target entity for these guys.
    cmdUtils.defaults.setDefaultParentEntityForShots(targetEntity, trackItems)
    if sequence:
      cmdUtils.defaults.setDefaultsInObjTag(sequence,
          cmdUtils.defaults.kTrackItemTimingOptionsKey, timingOpts)

    shotItems = cmdUtils.object.trackItemsToShotItems(trackItems,
          options, coalesseByName=True)

    newShots, existingShots, conflictingShots = cmdUtils.shot.analyzeHieroShotItems(
          shotItems, targetEntity, context, adopt=True)

    if conflictingShots:
      cmdUtils.shot.updateEntitiesFromShotItems(conflictingShots, context)

  return shotItems


@cmdUtils.logExceptions
def publishShotClipsFromTrackItemsUI(trackItems, context=None, parent=None):
  """

  @param trackItems list(hiero.core.TrackItem) Should be sorted in time order.

  @localeUsage hiero.specifications.HieroTimelineLocale

  """
  if not trackItems:
    return []

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()
  if not manager:
    FnAssetAPI.loggin.error("No Asset Manager has been chosen.")
    return

  managerOpsKey = cmdUtils.defaults.managerSpecificKey('managerOptionsPublishShotClips')
  clipOptsKey = 'publishShotClipsDefaults'

  if parent is None:
    parent = hiero.ui.mainWindow()

  duplicates = cmdUtils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    FnAssetAPI.logging.error(("There are duplicate Shot names in your selection, "
      + "please make sure any identically named Shots are adjacent or "
      + "overlapping so they can be combined.  - %s.")
        % ", ".join(duplicates))
    return []

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  ## @todo There is probably a better place for this
  context.locale = specifications.HieroTimelineLocale()
  context.locale.objects = trackItems

  from PublishShotClipsDialog import PublishShotClipsDialog
  dialog = PublishShotClipsDialog(context, parent=parent)
  dialog.setTrackItems(trackItems)

  sequence = None
  if hasattr(trackItems[0], 'sequence'):
    sequence = trackItems[0].sequence()
  if sequence:

    # See if we have any default options
    savedOpts = cmdUtils.defaults.getDefaultsFromObjTag(sequence, clipOptsKey)

    # See if we have any manager options
    managerOpts = cmdUtils.defaults.getDefaultsFromObjTag(sequence, managerOpsKey)
    savedOpts['managerOptionsClip'] = managerOpts

    dialog.setOptions(savedOpts)

  # Figure out a default entity ref if we don't have one, and a default for the
  # shared clips
  entity = cmdUtils.defaults.getDefaultParentEntityForShots(trackItems, context)
  clipEntity = cmdUtils.defaults.getDefaultParentEntityForClips(trackItems, context)
  defaultOpts = {}
  if entity:
    defaultOpts['targetEntityRef'] = entity.reference
  if clipEntity:
    defaultOpts['sharedClipTargetEntityRef'] = clipEntity.reference
  if defaultOpts:
    dialog.setOptions(defaultOpts)

  result = dialog.exec_()
  if not result:
    return []

  ## @todo Save the options here in user prefs or something, and reset them
  ## next time? So they're sticky?

  options = dialog.getOptions()
  managerOpts = {}
  clipOpts = dict(options)
  if 'managerOptionsClip' in options:
    managerOpts = options['managerOptionsClip']
    # We don't want to stash these with the other opts
    del clipOpts['managerOptionsClip']

  FnAssetAPI.logging.debug("CreateShotDialog options: %s" % options)

  shotItems = []

  with session.scopedActionGroup(context):

    targetEntityRef = options['targetEntityRef']
    # This must already exist since we're about to ask for the shots
    # underneath it to see what we already have compared to what we've
    # been given to publish.
    targetEntity = session.getEntity(targetEntityRef, mustExist=True)

    sharedTarget = None
    sharedTargetRef = options.get('sharedClipTargetEntityRef', None)
    if sharedTargetRef:
      sharedTarget = session.getEntity(sharedTargetRef, mustExist=True)

    # Store the last used someplace relevant to the trackItems so next
    # time we do this, we default to the same target entity for these guys.
    cmdUtils.defaults.setDefaultParentEntityForShots(targetEntity, trackItems)
    if sharedTarget:
      cmdUtils.defaults.setDefaultParentEntityForClips(sharedTarget, trackItems)
    if sequence:
      cmdUtils.defaults.setDefaultsInObjTag(sequence, clipOptsKey, clipOpts)
      cmdUtils.defaults.setDefaultsInObjTag(sequence, managerOpsKey, managerOpts)

    # Map track items to existing shots in the manager
    shotItems = cmdUtils.object.trackItemsToShotItems(trackItems, coalesseByName=True)

    newShots, existingShots, unused = cmdUtils.shot.analyzeHieroShotItems(shotItems,
        targetEntity, context=context, adopt=True, checkForConflicts=False)

    # In order to get the 'shared clip analysis' working properly in the
    # command, we actually want all selected shotTrackItems, not just the
    # existing ones - otherwise, we don't pick up clips shared with
    # non-matching shots, even though they can still be published, as we're
    # publishing to an alternate location. The command will filter out any
    # shots that don't have an entity.
    shotItems = []
    shotItems.extend(existingShots)
    shotItems.extend(newShots)

    publishShared = options.get('publishSharedClips', False)
    replaceSource = options.get('usePublishedClips', True)

    context.managerOptions = options.get('managerOptionsClip', {})

    customClipName = None
    if options.get('clipsUseCustomName', False):
      customClipName = options.get('customClipName', None)

    ignorePublished = options.get('ignorePublishedClips', True)

    commands.publishClipsFromHieroShotItems(shotItems,
        publishShared, sharedTarget, replaceSource, customClipName,
        ignorePublished, context)

  return shotItems




