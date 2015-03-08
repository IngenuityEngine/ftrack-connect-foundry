from FnAssetAPI.specifications import ShotSpecification, ImageSpecification
from FnAssetAPI.ui.toolkit import QtCore, QtGui
from PublishShotClipsSummaryWidget import PublishShotClipsSummaryWidget

import FnAssetAPI.logging

from .. import utils as cmdUtils

class PublishShotClipsDialog(QtGui.QDialog):
  """

  """

  def __init__(self, context=None, parent=None):
    super(PublishShotClipsDialog, self).__init__(parent)

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    session = FnAssetAPI.ui.UISessionManager.currentSession()
    if session is None:
      FnAssetAPI.logging.error("There is currently no Session started with an "
          +"Asset Management System, unable to create shots.")
      self.reject()

    if context is None:
      context = session.createContext()

    self.setWindowTitle(FnAssetAPI.l("{publish} Source Clips to {shots} in {manager}"))

    self.widget = PublishShotClipsWidget(context)
    layout.addWidget(self.widget)

    self.__buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok
        | QtGui.QDialogButtonBox.Cancel)

    self.widget.optionsChanged.connect(self.__setButtonTitle)
    self.__setButtonTitle()

    layout.addWidget(self.__buttons)

    self.__buttons.accepted.connect(self.accept)
    self.__buttons.rejected.connect(self.reject)


  def getOptions(self):
    return self.widget.getOptions()

  def setOptions(self, options):
    self.widget.setOptions(options)

  def setTrackItems(self, trackItems):
    self.widget.setTrackItems(trackItems)

  def sizeHint(self):
    return QtCore.QSize(850, 650)

  def __setButtonTitle(self):

    title, enabled = self.widget.getButtonState()
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setText(title)
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setEnabled(enabled)



class PublishShotClipsWidget(QtGui.QWidget):
  """

  A dialog to present the user with options pertaining to creating shots in an
  asset manager, based on a number of selected track items. Clips from these
  TrackItems can also be published to the shots, or, if shared with multiple
  TrackItems, they can be published to an alternate location.

  @specUsage FnAssetAPI.specifications.ImageSpecification
  @specUsage FnAssetAPI.specifications.ShotSpecification

  """

  optionsChanged = QtCore.Signal()

  ## @name Constants for Option Keys
  ## @{
  kTargetEntityRef = 'targetEntityRef'
  kPublishClips = 'publishClips'
  kClipsUseCustomName = 'clipsUseCustomName'
  kCustomClipName = 'customClipName'
  kPublishSharedClips = 'publishSharedClips'
  kUsePublishedClips = 'usePublishedClips'
  kIgnorePublishedClips = 'ignorePublishedClips'
  kSharedClipEntityRef = 'sharedClipTargetEntityRef'
  kManagerOptionsClip = 'managerOptionsClip'
  ## @}

  ## @todo We currently require a context at initialisation time, as we need to
  # create Manager UI elements. Ideally, we'd let this be set later, and
  # re-create any context-dependent UI as necessary.
  def __init__(self, context, parent=None, options=None):

    super(PublishShotClipsWidget, self).__init__(parent=parent)

    self.__trackItems = []
    self.__shotItems = []
    self.__clipItems = []
    self.__sharedClipItems = []

    self.__updatingOptions = False

    self.__options = {
        self.kTargetEntityRef : '',
        self.kPublishClips : True,
        self.kPublishSharedClips : False,
        self.kUsePublishedClips : True,
        self.kSharedClipEntityRef : '',
        self.kClipsUseCustomName : False,
        self.kCustomClipName : 'plate',
        self.kIgnorePublishedClips : True,
    }

    self._session = FnAssetAPI.ui.UISessionManager.currentSession()
    self._context = context # Note, this is a reference
    self._context.access = context.kWriteMultiple

    # Make some caches for these, to avoid thrashing the API
    self.__clipPolicy = cmdUtils.policy.clipPolicy(forWrite=True)
    self.__perEntityClipPolicy = {}

    # We'll need to keep track of some lookups to avoid excess traffic
    self._parentEntity = None
    self._newShots = []
    self._existi_existingShotsLabelngShots = []

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    self._buildUI(layout)
    self._connectUI()

    if options:
      self.setOptions(options)
    else:
      self._readOptions()


  def _buildUI(self, layout):

    ## @todo Some of these should probably be widgets in their own right, but
    ## it needs a little though due to the interaction between them.


    # Add the 'Create Under' section, to choose the parent entity that should
    # receive the new shots.

    specification = ShotSpecification()

    pickerCls = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kInlinePickerWidgetId, instantiate=False)

    # Parent Picker

    parentPickerLayout = QtGui.QHBoxLayout()
    parentPickerLayout.addWidget(QtGui.QLabel("Look for matching Shots under:"))
    self._shotParentPicker = pickerCls(specification, self._context)
    parentPickerLayout.addWidget(self._shotParentPicker)
    layout.addLayout(parentPickerLayout)

    mediaWidget = self._buildClipsTab()

    layout.addWidget(mediaWidget)


  def _buildClipsTab(self):

    l = FnAssetAPI.l

    imageSpecification = ImageSpecification()

    # > Media Ta

    mediaWidget = QtGui.QWidget()
    mediaWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    mediaWidgetLayout = QtGui.QVBoxLayout()
    mediaWidgetLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    mediaWidget.setLayout(mediaWidgetLayout)

    # - Shared Media

    self._sharedClipsGroup = QtGui.QGroupBox(l("Some Source Clips are Shared "+
      "and used in more than one Shot in the Edit"))
    mediaWidgetLayout.addWidget(self._sharedClipsGroup)
    sharedClipsGroupLayout = QtGui.QVBoxLayout()
    self._sharedClipsGroup.setLayout(sharedClipsGroupLayout)

    self._sharedIgnoredRadio = QtGui.QRadioButton(l("Don't {publish}"))
    self._sharedToSequenceRadio = QtGui.QRadioButton(l("{publish} at the level above the Shots"))
    self._sharedToCustomRadio = QtGui.QRadioButton(l("{publish} to another location"))
    self._sharedIgnoredRadio.setChecked(True)
    sharedClipsGroupLayout.addWidget(self._sharedIgnoredRadio)
    sharedClipsGroupLayout.addWidget(self._sharedToSequenceRadio)
    sharedClipsGroupLayout.addWidget(self._sharedToCustomRadio)

    ## @todo Use the project entityReferences Parent if we have one?

    pickerCls = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kInlinePickerWidgetId, instantiate=False)

    self._sharedClipParentPicker = pickerCls(imageSpecification, self._context)
    self._sharedClipParentPicker.setVisible(False)
    sharedClipsGroupLayout.addWidget(self._sharedClipParentPicker)

    self._previewWidget = PublishShotClipsSummaryWidget()
    self._previewWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    mediaWidgetLayout.addWidget(self._previewWidget)

    # - Options

    self._clipOptionsGroup = QtGui.QGroupBox(l("Options"))
    optionsGroupLayout = QtGui.QVBoxLayout()
    self._clipOptionsGroup.setLayout(optionsGroupLayout)
    mediaWidgetLayout.addWidget(self._clipOptionsGroup)

    # See if we have any options from the manager
    self._managerOptionsClip = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kRegistrationManagerOptionsWidgetId,
        throw=False, args=(imageSpecification, self._context))

    if self._managerOptionsClip:
      optionsGroupLayout.addWidget(self._managerOptionsClip)
      optionsGroupLayout.addSpacing(10)

    hieroOptionsGrid = QtGui.QGridLayout()

    ## @todo we should have some base widget for this

    hieroOptionsGrid.addWidget(QtGui.QLabel(l("{asset} name:")), 0, 0)

    self._clipNameCombo = QtGui.QComboBox()
    self._clipNameCombo.addItems(("Clip Name", "Custom"))
    hieroOptionsGrid.addWidget(self._clipNameCombo, 0, 1)

    self._clipNameCustomField = QtGui.QLineEdit()
    hieroOptionsGrid.addWidget(self._clipNameCustomField, 0, 2)

    self._replaceClipSource = QtGui.QCheckBox(l("Link Source Clips to "+
        "{published} {assets}"))
    hieroOptionsGrid.addWidget(self._replaceClipSource, 1, 1, 1, 2)

    self._ignorePublishedClips = QtGui.QCheckBox(l("Ignore Source Clips that are "+
      "already {published}"))
    hieroOptionsGrid.addWidget(self._ignorePublishedClips, 2, 1, 1, 2)

    # Make sure we don't stretch the grid layout too much and make the last
    #column really wide
    hieroOptionsHBox = QtGui.QHBoxLayout()
    optionsGroupLayout.addLayout(hieroOptionsHBox)
    hieroOptionsHBox.addLayout(hieroOptionsGrid)
    hieroOptionsHBox.addStretch()

    return mediaWidget


  def _connectUI(self):

    self._shotParentPicker.selectionChanged.connect(
        lambda v: self.__updateOption(self.kTargetEntityRef, v[0] if v else ''))

    # Make sure the shared clip destination is updated too
    self._shotParentPicker.selectionChanged.connect(self.__sharedClipDestToggle)

    self._replaceClipSource.toggled.connect(
        lambda s: self.__updateOption(self.kUsePublishedClips, s))

    self._ignorePublishedClips.toggled.connect(
        lambda s: self.__updateOption(self.kIgnorePublishedClips, s,
          clearItems=True))

    self._sharedToSequenceRadio.toggled.connect(self.__sharedClipDestToggle)
    self._sharedToCustomRadio.toggled.connect(self.__sharedClipDestToggle)
    self._sharedIgnoredRadio.toggled.connect(self.__sharedClipDestToggle)
    self._sharedClipParentPicker.selectionChanged.connect(self.__sharedClipDestToggle)

    self._clipNameCustomField.editingFinished.connect(self.__clipNameOptionsChanged)
    self._clipNameCombo.currentIndexChanged.connect(self.__clipNameOptionsChanged)

    ## @todo Do we need to connect up the manager options widget too?



  def __clipNameOptionsChanged(self):

    if self.__updatingOptions:
      return

    source = self._clipNameCombo.currentText()
    self.__updateOption(self.kClipsUseCustomName, source == "Custom", refresh=False)
    name = self._clipNameCustomField.text()
    self.__updateOption(self.kCustomClipName, name, refresh=True, clearItems=True)


  def __sharedClipDestToggle(self):

    ignore = self._sharedIgnoredRadio.isChecked()

    useCustom = self._sharedToCustomRadio.isChecked()
    self._sharedClipParentPicker.setVisible(useCustom)

    if self.__updatingOptions:
      return

    if useCustom:
      sharedTarget = self._sharedClipParentPicker.getSelectionSingle()
    else:
      sharedTarget = self._shotParentPicker.getSelectionSingle()

    self.__updateOption(self.kPublishSharedClips, not ignore)
    self.__updateOption(self.kSharedClipEntityRef, sharedTarget)


  def __updateOption(self, option, value, refresh=True, clearParent=False,
      clearItems=False):

    if self.__updatingOptions:
      return

    self.__options[option] = value
    if refresh:
      if clearParent:
        self._parentEntity = None
      if clearItems:
        self.__shotItems = []
      self.refresh()

    self._validateOptions()


  def _readOptions(self):

    self.__updatingOptions = True

    # Drive some defaults if the options aren't set
    publishSharedClips = self.__options.get(self.kPublishSharedClips, False)

    # Update UI, this will set the options in the defaulted case due to the
    # signal connections on the toggled event
    targetEntityRef = self.__options.get(self.kTargetEntityRef, '')
    sharedTargetEntityRef = self.__options.get(self.kSharedClipEntityRef, '')

    # Update the radios first due to signal connections
    if publishSharedClips:
      if sharedTargetEntityRef or sharedTargetEntityRef == targetEntityRef:
        self._sharedToSequenceRadio.setChecked(True)
      else:
        self._sharedIgnoredRadio.setChecked(True)
    else:
      try:
        self._sharedClipParentPicker.setSelectionSingle(sharedTargetEntityRef)
      except Exception as e:
        FnAssetAPI.logging.debug(e)
      self._sharedToCustomRadio.setChecked(True)

    # Update main picked value
    try:
      self._shotParentPicker.setSelectionSingle(targetEntityRef)
    except Exception as e:
      FnAssetAPI.logging.debug(e)

    replaceClips = self.__options.get(self.kUsePublishedClips, True)
    self._replaceClipSource.setChecked(replaceClips)

    # Manager Options

    managerOptionsClip = self.__options.get(self.kManagerOptionsClip, None)
    if managerOptionsClip and self._managerOptionsClip:
      self._managerOptionsClip.setOptions(managerOptionsClip)

    clipCustomName = self.__options.get(self.kCustomClipName, '')
    self._clipNameCustomField.setText(clipCustomName)

    useClipCustomName = self.__options.get(self.kClipsUseCustomName, False)
    self._clipNameCombo.setCurrentIndex( 1 if useClipCustomName else 0 )

    ignorePublished = self.__options.get(self.kIgnorePublishedClips, True)
    self._ignorePublishedClips.setChecked(ignorePublished)

    self.__updatingOptions = False

    # Make sure that the shared clip options are correctly configured - there
    # isn't a 1:1 mapping between options and controls, so the case of 'publish
    # to shot parent' lets just double check that the options dict contain the
    # right parent

    self.__sharedClipDestToggle()


  def _validateOptions(self):

    # Make sure that the asset manager can take us publishing a clip
    clipsAllowed = self.__clipPolicy != FnAssetAPI.constants.kIgnored
    ## @todo disable dialog if clips not allowed

    # If people are choosing to publish shared clips to the main sequence,
    # make sure that the parent is capable of taking them (some cases, its not)
    # Disable the radio button if its not applicable

    sharedPublishEnabled = True

    if self._sharedToSequenceRadio.isChecked():
      dest = self.__options.get(self.kSharedClipEntityRef, None)
      if dest:

        if dest not in self.__perEntityClipPolicy:
          self.__perEntityClipPolicy[dest] = cmdUtils.policy.clipPolicy(
              forWrite=True, entityRef=dest)

        sharedClipPolicy = self.__perEntityClipPolicy.get(dest,
            FnAssetAPI.constants.kIgnored)

        if sharedClipPolicy == FnAssetAPI.constants.kIgnored:
          sharedPublishEnabled = False

    if not sharedPublishEnabled:
      self._sharedToCustomRadio.setChecked(True)

    ## @todo For some reason, this doesn't seem to take effect, so it looks a bit
    # confusing to the user :(
    self._sharedToSequenceRadio.setEnabled(sharedPublishEnabled)
    self._sharedToSequenceRadio.setCheckable(sharedPublishEnabled)

    self._clipNameCustomField.setEnabled(
        self.__options.get(self.kClipsUseCustomName, False))


  def sizeHint(self):
    return QtCore.QSize(600, 400)


  def setTrackItems(self, trackItems):

    self.__trackItems = []

    self.__trackItems = trackItems
    self.__shotItems = [] # Clear cache
    self.refresh()

  def getTrackItems(self):
    return self.__trackItems


  def getOptions(self):

    options = dict(self.__options)

    managerOptionsClip = {}
    if self._managerOptionsClip:
      managerOptionsClip = self._managerOptionsClip.getOptions()
    options[self.kManagerOptionsClip] = managerOptionsClip

    return options


  def setOptions(self, options):

    self.__options.update(options)
    self._readOptions()

    if self._managerOptionsClip:
      managerOptions = options.get(self.kManagerOptionsClip, {})
      self._managerOptionsClip.setOptions(managerOptions)

    self.refresh()


  # This refreshes the UI based on its current state, it doesn't re-read the
  # options dict directly. If required, call _readOptions() first
  def refresh(self):

    ## @todo Call managementPolicy on an image sequence to the chosen sequence
    ## in case, say someone selected a project as the destination and the ams
    ## can't handle image sequences at the project level...

    session = FnAssetAPI.SessionManager.currentSession()
    if not session:
      raise RuntimeError("No Asset Management session available")

    if not self.__shotItems:

      self.__shotItems = cmdUtils.object.trackItemsToShotItems(self.__trackItems,
          self.getOptions(), coalesseByName=True)

      self._parentEntity = None

      self._previewWidget.setShotItems(self.__shotItems)

    # Update Shot Creation

    parentRef = self.__options.get(self.kTargetEntityRef, None)

    # Ensure we don't waste time repeatedly looking under the same parent
    if not self._parentEntity or self._parentEntity.reference != parentRef:

      self._parentEntity = session.getEntity(parentRef)

      if self._parentEntity:
        # Ensure we have the entity for any existing shots
        cmdUtils.shot.analyzeHieroShotItems(self.__shotItems, self._parentEntity,
            checkForConflicts=False, adopt=True)

    self.__clipItems, self.__sharedClipItems = \
      cmdUtils.shot.analyzeHeiroShotItemClips(self.__shotItems, asItems=True)

    haveShared = bool(self.__sharedClipItems)

    if self.__options.get(self.kIgnorePublishedClips, True):
      itemFilter = lambda i : not i.getEntity()
      self.__clipItems = filter(itemFilter, self.__clipItems)
      self.__sharedClipItems = filter(itemFilter, self.__sharedClipItems)

    # Update Clip publishing
    self._previewWidget.setShotItems(self.__shotItems)
    self._previewWidget.setOptions(self.getOptions())
    self._previewWidget.refresh()

    self._sharedClipsGroup.setDisabled(not bool(self.__sharedClipItems))
    self._sharedClipsGroup.setVisible(haveShared)

    self._validateOptions()

    self.optionsChanged.emit()


  def getButtonState(self):

    publishClips = bool(self.__clipItems) and self.__options[self.kTargetEntityRef]

    publishShared = (self.__options[self.kPublishSharedClips] and
        bool(self.__sharedClipItems))
    publishSharedValid = self.__options[self.kSharedClipEntityRef]

    publish = bool(publishClips or publishShared)

    enabled = publish
    if publishShared and not publishSharedValid:
      enabled = False

    title = FnAssetAPI.l("{publish}")

    return title, enabled



