from QtExt import QtGui, QtWidgets, QtCore

import FnAssetAPI
from FnAssetAPI import specifications

from .. import utils as cmdUtils

from FnAssetAPI.ui.constants import kWorkflowRelationshipWidgetId

## @todo Unify how the dialogs work - some use explicit accessors, some use
## options dicts

class BuildAssetTrackDialog(QtWidgets.QDialog):
  """

  This dialog is to hold a UI, supplied by the manager, to get a set of
  options, to be used with a 'getRelatedEntities' call, in order to fins a new
  set of entities to build a track.

  The options should be storable in the host, so that we can update the track
  without needing to use the UI.
  
  @specUsage FnAssetAPI.specifications.ShotSpecification

  """

  def __init__(self, parent=None, session=None, context=None):
    super(BuildAssetTrackDialog, self).__init__(parent)

    self.setWindowTitle("Build Track")

    if not session:
      session = FnAssetAPI.SessionManager.currentSession()
    self.__session = session

    if not context:
      context = session.createContext()
    self.__context = context

    self.__selection = []
    self.__entities = []
    self.__ignoreClips = False

    self.__lastIgnoreClips = None
    self.__lastParentRef = None

    layout = QtWidgets.QVBoxLayout()
    self.setLayout(layout)

     # Asset Manager Widget

    self.__relationshipWidget = session.getManagerWidget(
        kWorkflowRelationshipWidgetId, args=[context,])
    layout.addWidget(self.__relationshipWidget)

    # Stretch
    layout.addStretch()

    # Options

    optionsBox = QtWidgets.QGroupBox("Options")
    optionsLayout = QtWidgets.QVBoxLayout()
    optionsBox.setLayout(optionsLayout)
    layout.addWidget(optionsBox)

    self.__trackName = QtWidgets.QLineEdit()
    trackNameLayout = QtWidgets.QHBoxLayout()
    trackNameLayout.addWidget(QtWidgets.QLabel("Track Name"))
    trackNameLayout.addWidget(self.__trackName)
    optionsLayout.addLayout(trackNameLayout)

    self.__useClipsRadio = QtWidgets.QRadioButton("Match by Clip")
    self.__useShotsRadio = QtWidgets.QRadioButton("Match by Shot")
    optionsLayout.addWidget(self.__useClipsRadio)
    optionsLayout.addWidget(self.__useShotsRadio)

   ## @todo Use the project entityReferences Parent if we have one?

    context.access = context.kReadMultiple
    context.retention = context.kTransient
    specification = specifications.ShotSpecification()

    self.__shotParentPicker = self.__session.getManagerWidget(
        FnAssetAPI.ui.constants.kInlinePickerWidgetId, args=[specification, context])
    optionsLayout.addWidget(self.__shotParentPicker)

    # Buttons

    ## @todo disable the ok button if using shots and no valid entity ref

    self.__buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok
        | QtWidgets.QDialogButtonBox.Cancel)
    self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Build')
    layout.addWidget(self.__buttons)

    # Connections

    self.__buttons.accepted.connect(self.accept)
    self.__buttons.rejected.connect(self.reject)

    self.__useShotsRadio.toggled.connect(self.__modeChanged)
    self.__useClipsRadio.toggled.connect(self.__modeChanged)

    self.__relationshipWidget.criteriaChanged.connect(self.__syncUI)
    # This might be better on editingFinished, but there is only one text field
    # some of the time so loosing focus might not happen as required
    self.__trackName.textChanged.connect(self.__syncUI)

    self.__shotParentPicker.selectionChanged.connect(self.__parentChanged)

    self.__syncUI()

    # Make sure the name field is ready for editing as we can't create without
    self.__trackName.setFocus()


  def setIgnoreClips(self, ignore):
    self.__ignoreClips = ignore
    self.__syncUI()

  def getIgnoreClips(self):
    return self.__ignoreClips


  def setCriteriaString(self, string):
    self.__relationshipWidget.setCriteriaString(string)

  def getCriteriaString(self):
    return self.__relationshipWidget.getCriteriaString()


  def setTrackName(self, name):
    self.__trackName.setText(name)

  def getTrackName(self):
    return self.__trackName.text()


  def setShotParentEntiy(self, entity):
    self.__shotParentPicker.setSelectionSingle(str(entity))

  def getShotParentEntity(self):

    entity = None

    entityRef = self.__shotParentPicker.getSelectionSingle()
    if entityRef:
      manager = self.__session.currentManager()
      entity = manager.getEntity(entityRef, self.__context)

    return entity


  def setSelection(self, selection):
    self.__selection = selection
    self._analyze()


  def getSelection(self):
    return self.__selection


  def _analyze(self):

    # Only do this if the widget wants them, as its slow
    if not self.__relationshipWidget.usesEntityReferences():
      return

    ## @todo Validate the selection is only track items?
    items = cmdUtils.object.trackItemsToShotItems(self.__selection)

    if self.__ignoreClips:
      parent = self.getShotParentEntity()
      self.__entities = cmdUtils.shot.entitiesFromShotItems(items, asShotsUnderEntity=parent)
    else:
      self.__entities = cmdUtils.shot.entitiesFromShotItems(items)

    refs = [e.reference for e in self.__entities if e]
    self.__relationshipWidget.setEntityReferences(refs)


  def __syncUI(self):

    # Ensures the UI is up to date with internal options
    if self.__ignoreClips:
      self.__useShotsRadio.setChecked(True)
    else:
      self.__useClipsRadio.setChecked(True)

    # See if the button should be enabled
    criteria = self.__relationshipWidget.getCriteriaString()
    trackName = self.__trackName.text()

    shotParentOk = True
    if self.__ignoreClips:
      shotParentOk = bool(self.__shotParentPicker.getSelectionSingle())

    enabled = bool(criteria and trackName and shotParentOk)
    self.__buttons.button(QtGui.QDialogButtonBox.Ok).setEnabled(enabled)


  def __modeChanged(self):

    pickerVisiblity = False
    buttonEnabled = True

    self.__ignoreClips = bool(self.__useShotsRadio.isChecked())

    if self.__ignoreClips:
      pickerVisiblity = True
      ref = self.__shotParentPicker.getSelectionSingle()
      buttonEnabled = bool(ref)

    self.__shotParentPicker.setVisible(pickerVisiblity)
    self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(buttonEnabled)

    self._analyze()
    self.__syncUI()


  def __parentChanged(self):

    if self.__ignoreClips:
      ref = self.__shotParentPicker.getSelectionSingle()
      self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(bool(ref))

      self._analyze()
      self.__syncUI()
