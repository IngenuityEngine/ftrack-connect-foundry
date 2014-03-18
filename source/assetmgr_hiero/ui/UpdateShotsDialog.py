from FnAssetAPI.specifications import ShotSpecification
from FnAssetAPI.ui.toolkit import QtCore, QtGui

import FnAssetAPI.logging

from .. import utils as cmdUtils

from widgets import TrackItemTimingOptionsWidget, IconLabelWidget
from widgets import AdvancedHieroItemSpreadsheet

## @todo Disable the Media tab if policy doesn't support media

class UpdateShotsDialog(QtGui.QDialog):
  """

  """

  def __init__(self, context=None, parent=None):
    super(UpdateShotsDialog, self).__init__(parent)

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    session = FnAssetAPI.ui.UISessionManager.currentSession()
    if session is None:
      FnAssetAPI.logging.error("There is currently no Session started with an "
          +"Asset Management System, unable to create shots.")
      self.reject()

    if context is None:
      context = session.createContext()

    self.setWindowTitle(FnAssetAPI.l("Update {shots} {published} in {manager}"))

    self.widget = UpdateShotsWidget(context)
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
    return QtCore.QSize(800, 550)

  def __setButtonTitle(self):

    title, enabled = self.widget.getButtonState()
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setText(title)
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setEnabled(enabled)



class UpdateShotsWidget(QtGui.QWidget):
  """

  A dialog to present the user with options pertaining to creating shots in an
  asset manager, based on a number of selected track items. Clips from these
  TrackItems can also be published to the shots, or, if shared with multiple
  TrackItems, they can be published to an alternate location.

  @specUsage FnAssetAPI.specifications.ShotSpecification

  """

  optionsChanged = QtCore.Signal()

  ## @name Constants for Option Keys
  ## @{
  kTargetEntityRef = 'targetEntityRef'
  kUpdateConflictingShots = 'updateConflictingShots'
  kSetShotTimings = 'setShotTimings'
  ## @}

  ## @todo We currently require a context at initialisation time, as we need to
  # create Manager UI elements. Ideally, we'd let this be set later, and
  # re-create any context-dependent UI as necessary.
  def __init__(self, context, parent=None, options=None):

    super(UpdateShotsWidget, self).__init__(parent=parent)

    self._tickIcon = QtGui.QIcon("icons:TagGood.png")
    self._crossIcon = QtGui.QIcon("icons:SwapInputs.png")
    self._blockIcon = QtGui.QIcon("icons:status/TagOnHold.png")

    self.__updatingOptions = False

    self.__trackItems = []
    self.__shotItems = []

    self.__options = {
        self.kTargetEntityRef : '',
        self.kUpdateConflictingShots : True,
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

    # Add the 'Create Under' section, to choose the parent entity that should
    # receive the new shots.

    specification = ShotSpecification()

    pickerCls = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kInlinePickerWidgetId, instantiate=False)

    # Parent Picker

    l = FnAssetAPI.l

    parentPickerLayout = QtGui.QHBoxLayout()
    parentPickerLayout.addWidget(QtGui.QLabel(l("Match {shots} under:")))
    self._shotParentPicker = pickerCls(specification, self._context)
    parentPickerLayout.addWidget(self._shotParentPicker)
    layout.addLayout(parentPickerLayout)

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

    # - Conflicting Shots

    self._shotsList = AdvancedHieroItemSpreadsheet()
    self._shotsList.setAlternatingRowColors(True)
    self._shotsList.setHiddenProperties(("nameHint",))
    self._shotsList.setForcedProperties(
        ("startFrame", "endFrame", "inFrame", "outFrame", "inTimecode",
          "sourceTimecode"))
    self._shotsList.setStatusText(l("Update Timings"), l("Timings Match"))

    self._shotsList.setDisabledCallback(self.__shotItemIsDisabled)
    self._shotsList.setStatusCallback(self.__statusForShotItem)
    self._shotsList.setIconCallback(self.__iconForShotItem)
    shotsWidgetLayout.addWidget(self._shotsList)


    # Length Options

    self._shotLengthGBox = QtGui.QGroupBox("Set Shot Timings")
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

    self._validateOptions()

  def __iconForShotItem(self, item):
    if item in self._existingShots:
      return self._tickIcon
    elif item in self._newShots:
      return self._blockIcon
    else:
      return self._crossIcon

  def __statusForShotItem(self, item):
    if item in self._existingShots:
      return "Timings Match"
    elif item in self._newShots:
      return FnAssetAPI.l("No Matching {shot}")
    else:
      return "Timings Different"

  def __shotItemIsDisabled(self, item):
    return item not in self._conflictingShots

  def _readOptions(self):

    self.__updatingOptions = True

    # Update UI, this will set the options in the defaulted case due to the
    # signal connections on the toggled event

    targetEntityRef = self.__options.get(self.kTargetEntityRef, '')

    # Update main picked value
    try:
      self._shotParentPicker.setSelectionSingle(targetEntityRef)
    except Exception as e:
      FnAssetAPI.logging.debug(e)

    # Shot length options are read directly in the widget
    setTimings = self.__options.get(self.kSetShotTimings, True)
    self._shotLengthGBox.setChecked(setTimings)

    self.__updatingOptions = False


  def _validateOptions(self):
    pass


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
    options.update(self._shotLengthOptionsWidget.getOptions())
    return options

  def setOptions(self, options):
    self.__options.update(options)
    self._readOptions()
    self._shotLengthOptionsWidget.setOptions(options)
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

    # Update Shot Creation

    parentRef = self.__options.get(self.kTargetEntityRef, None)

    # Ensure we don't waste time repeatedly looking under the same parent
    if not self._parentEntity or self._parentEntity.reference != parentRef:

      self._parentEntity = session.getEntity(parentRef)

      newShots, existingShots, conflictingShots = cmdUtils.shot.analyzeHieroShotItems(
          self.__shotItems, self._parentEntity, self._context)

      self._newShots = newShots
      self._existingShots = existingShots
      self._conflictingShots = conflictingShots

      self._shotsList.setItems(self.__shotItems)

    self._validateOptions()

    self.optionsChanged.emit()


  def getButtonState(self):

    update =  bool(self._conflictingShots)

    return "Update", update



