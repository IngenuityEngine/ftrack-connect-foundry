from FnAssetAPI.specifications import ShotSpecification
from FnAssetAPI.ui.toolkit import QtCore, QtGui

import FnAssetAPI.logging

from .. import utils as cmdUtils

from widgets import TrackItemTimingOptionsWidget
from widgets import AdvancedHieroItemSpreadsheet

## @todo Disable the Media tab if policy doesn't support media

class CreateShotsDialog(QtGui.QDialog):
  """

  A Dialog to give a user a preview of the 'create shots' action. The result of
  the dialog is an options dict @ref getOptions that matches the kwargs of @ref
  createShotsFromTrackItems and publishClipsFromHieroShotItems.
  The dialog will not actually do any work itself.

  """

  def __init__(self, context=None, parent=None):
    super(CreateShotsDialog, self).__init__(parent)


    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    session = FnAssetAPI.ui.UISessionManager.currentSession()
    if session is None:
      FnAssetAPI.logging.error("There is currently no Session started with an "
          +"Asset Management System, unable to create shots.")
      self.reject()

    if context is None:
      context = session.createContext()

    self.setWindowTitle(FnAssetAPI.l("Create {shots} in {manager}"))

    self.widget = CreateShotsWidget(context)
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
    return QtCore.QSize(700, 550)

  def __setButtonTitle(self):

    title, enabled = self.widget.getButtonState()
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setText(title)
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setEnabled(enabled)



class CreateShotsWidget(QtGui.QWidget):
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
  kManagerOptionsShot = 'managerOptionsShot'
  kSetShotTimings = 'setShotTimings'
  ## @}

  ## @todo We currently require a context at initialisation time, as we need to
  # create Manager UI elements. Ideally, we'd let this be set later, and
  # re-create any context-dependent UI as necessary.
  def __init__(self, context, parent=None, options=None):

    super(CreateShotsWidget, self).__init__(parent=parent)

    self.__trackItems = []
    self.__shotItems = []

    self.__updatingOptions = False

    self.__options = {
        self.kTargetEntityRef : '',
        self.kSetShotTimings : True
    }

    self._session = FnAssetAPI.ui.UISessionManager.currentSession()
    self._context = context # Note, this is a reference
    self._context.access = context.kWriteMultiple

    # We'll need to keep track of some lookups to avoid excess traffic
    self._parentEntity = None
    self._newShots = []
    self._existingShots = []
    self._conflictingShots = []

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    self._buildUI(layout)
    self._connectUI()

    if options:
      self.setOptions(options)
    else:
      self._readOptions()


  def _buildUI(self, layout):

    self._managerOptionsShot = None

    # Add the 'Create Under' section, to choose the parent entity that should
    # receive the new shots.

    specification = ShotSpecification()

    pickerCls = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kInlinePickerWidgetId, instantiate=False)

    # Parent Picker

    parentPickerLayout = QtGui.QHBoxLayout()
    layout.addLayout(parentPickerLayout)
    parentPickerLayout.addWidget(QtGui.QLabel("Create Under:"))
    self._shotParentPicker = pickerCls(specification, self._context)
    parentPickerLayout.addWidget(self._shotParentPicker)

    shotsWidget = self._buildShotsTab()
    layout.addWidget(shotsWidget)


  def _buildShotsTab(self):

    l = FnAssetAPI.l

    # > Shots Tab

    shotsWidget = QtGui.QWidget()
    shotsWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    shotsWidgetLayout = QtGui.QVBoxLayout()
    shotsWidgetLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    shotsWidget.setLayout(shotsWidgetLayout)

    self._tickIcon = QtGui.QIcon("icons:TagGood.png")
    self._actionIcon = QtGui.QIcon("icons:Add.png")

    self._shotsList = AdvancedHieroItemSpreadsheet()
    self._shotsList.setAlternatingRowColors(True)
    self._shotsList.setIcons(self._actionIcon, self._tickIcon)
    self._shotsList.setHiddenProperties(("nameHint",))
    self._shotsList.setForcedProperties(
        ("startFrame", "endFrame", "inFrame", "outFrame"))
    self._shotsList.setStatusText(l("New {shot}"), l("Existing {shot}"))

    self._shotsList.setDisabledCallback(self.__shotItemIsDisabled)
    shotsWidgetLayout.addWidget(self._shotsList)

    # See if we have any options from the manager
    shotSpec = ShotSpecification()
    self._managerOptionsShot = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kRegistrationManagerOptionsWidgetId,
        throw=False, args=(shotSpec, self._context))
    if self._managerOptionsShot:
      shotsWidgetLayout.addWidget(self._managerOptionsShot)
      shotsWidgetLayout.addSpacing(10)

    # Length Options

    self._shotLengthGBox = QtGui.QGroupBox("Set Shot Timings from Hiero")
    self._shotLengthGBox.setCheckable(True)
    self._shotLengthGBox.setChecked(False)
    slGbLayout = QtGui.QHBoxLayout()
    self._shotLengthGBox.setLayout(slGbLayout)

    self._shotLengthOptionsWidget = TrackItemTimingOptionsWidget()
    slGbLayout.addWidget(self._shotLengthOptionsWidget)
    slGbLayout.addStretch()

    shotsWidgetLayout.addWidget(self._shotLengthGBox)

    return shotsWidget


  def _connectUI(self):

    self._shotParentPicker.selectionChanged.connect(
        lambda v: self.__updateOption(self.kTargetEntityRef, v[0] if v else ''))

    self._shotLengthOptionsWidget.optionsChanged.connect(self.__timingOptionsChanged)

    self._shotLengthGBox.toggled.connect(self.__timingOptionsChanged)

    ## @todo Do we need to connect up the manager options widget too?


  def __timingOptionsChanged(self):

    if self.__updatingOptions:
      return

    self.__options.update(self._shotLengthOptionsWidget.getOptions())
    self.__options[self.kSetShotTimings] = bool(self._shotLengthGBox.isChecked())
    # Force a full refresh
    self.__shotItems = []
    self._parentEntity = None
    self.refresh()


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


  def _readOptions(self):

    self.__updatingOptions = True

    # Update main picked value
    targetEntityRef = self.__options.get(self.kTargetEntityRef, '')
    try:
      self._shotParentPicker.setSelectionSingle(targetEntityRef)
    except Exception as e:
      FnAssetAPI.logging.debug(e)

    # Manager Options

    managerOptionsShot = self.__options.get(self.kManagerOptionsShot, None)
    if managerOptionsShot and self._managerOptionsShot:
      self._managerOptionsShot.setOptions(managerOptionsShot)

    # Shot length options are read directly in the widget
    setTimings = self.__options.get(self.kSetShotTimings, True)
    self._shotLengthGBox.setChecked(setTimings)

    self.__updatingOptions = False


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

    managerOptionsShot = {}
    if self._managerOptionsShot:
      managerOptionsShot = self._managerOptionsShot.getOptions()
    options[self.kManagerOptionsShot] = managerOptionsShot

    options.update(self._shotLengthOptionsWidget.getOptions())

    return options


  def setOptions(self, options):

    self.__options.update(options)
    self._readOptions()

    self._shotLengthOptionsWidget.setOptions(options)

    if self._managerOptionsShot:
      managerOptions = options.get(self.kManagerOptionsShot, {})
      self._managerOptionsShot.setOptions(managerOptions)

    self.refresh()



  def __shotItemIsDisabled(self, item):
    return item in self._existingShots

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

    # Update Shot Creation

    parentRef = self.__options.get(self.kTargetEntityRef, None)

    # Ensure we don't waste time repeatedly looking under the same parent
    if not self._parentEntity or self._parentEntity.reference != parentRef:

      self._parentEntity = session.getEntity(parentRef, mustExist=True,
          throw=False)

      if self._parentEntity:
        newShots, existingShots, unused = cmdUtils.shot.analyzeHieroShotItems(
            self.__shotItems, self._parentEntity, self._context,
            adopt=True, checkForConflicts=False)

        self._newShots = newShots
        self._existingShots = existingShots

      self._shotsList.setItems(self.__shotItems)
      self._shotsList.setEnabled(bool(self._parentEntity))

    self.optionsChanged.emit()


  def __refreshClips(self):

    self.__clipItems, self.__sharedClipItems = \
      cmdUtils.shot.analyzeHeiroShotItemClips(self.__shotItems, asItems=True)

    if self.__options.get(self.kIgnorePublishedClips, True):
      itemFilter = lambda i : not i.getEntity()
      self.__clipItems = filter(itemFilter, self.__clipItems)
      self.__sharedClipItems = filter(itemFilter, self.__sharedClipItems)

    ## @todo We probably shouldn't be duplicating this work, and it should
    ## come out of the utils functions or something... Its here for now as it
    ## minimises redundant work done to create the UI. That probably means
    ## the utility functions arent so well structured now we've added so much
    ## more into this dialog ;)
    customClipName = None
    if self.__options.get(self.kClipsUseCustomName, False):
      customClipName = self.__options.get(self.kCustomClipName, None)
    if customClipName:
      for c in self.__clipItems:
        c.nameHint = customClipName

    # Update Clip publishing

    self._clipsGroup.setVisible(bool(self.__clipItems))
    self._clipsList.setItems(self.__clipItems)

    self._sharedClipsGroup.setVisible(bool(self.__sharedClipItems))
    self._sharedClipsList.setItems(self.__sharedClipItems)

    haveClips = bool(self.__sharedClipItems) or bool(self.__clipItems)
    self._noMedia.setVisible(not haveClips)


  def getButtonState(self):
    create = bool(self._newShots) and bool(self.__options[self.kTargetEntityRef])
    return "Create", create



