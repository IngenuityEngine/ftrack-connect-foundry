from QtExt import QtGui, QtWidgets, QtCore

from FnAssetAPI.ui.widgets import SessionSettingsWidget, ItemSpreadsheetWidget

from .. import session
from .. import utils


__all__ = ['IconLabelWidget', 'AssetPreferencesDialog',
  'TrackItemTimingOptionsWidget', 'AdvancedHieroItemSpreadsheet' ]



class IconLabelWidget(QtGui.QWidget):

  def __init__(self, text=None, pixmap=None, resize=None, parent=None):
    super(IconLabelWidget, self).__init__(parent=parent)

    layout = QtGui.QHBoxLayout()
    self.setLayout(layout)

    self.pixmapLabel = QtGui.QLabel()
    self.label = QtGui.QLabel()

    layout.addWidget(self.pixmapLabel)
    layout.addWidget(self.label)

    if pixmap and not pixmap.isNull():
      self.setPixmap(pixmap, resize)

    if text:
      self.label.setText(text)


  def setPixmap(self, pixmap, resize=None):

    if resize:
      pixmap = pixmap.scaled(resize, QtCore.Qt.KeepAspectRatio,
          QtCore.Qt.SmoothTransformation)

    self.pixmapLabel.setPixmap(pixmap)
    self.pixmapLabel.setMinimumSize(pixmap.size())
    self.pixmapLabel.setMaximumSize(pixmap.size())

  def pixmap(self):
    return self.pixmapLabel.pixmap()


  def setText(self, text):
    self.label.setText(text)

  def text(self):
    return self.lable.text()



class AssetPreferencesDialog(QtGui.QDialog):

  def __init__(self, parent=None):
    super(AssetPreferencesDialog, self).__init__(parent=parent)

    self.setWindowTitle("Asset Management Preferences")

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    self.settingsWidget = SessionSettingsWidget()
    layout.addWidget(self.settingsWidget)

    self.applyButton = QtGui.QPushButton("Apply")
    layout.addWidget(self.applyButton)
    self.applyButton.clicked.connect(self.apply)


  def sizeHint(self):
    return QtCore.QSize(400, 450)


  def apply(self):
    # We listen on the manager changed event to save the new Id or update UI
    ## @todo Though we don't want to have to set this separately, when people
    ## have left the manager as it is, but not changed the logging
    self.settingsWidget.apply()
    session.saveAssetAPISettings()
    self.accept()


  def setSession(self, session):
    self.settingsWidget.setSession(session)




class TrackItemTimingOptionsWidget(QtGui.QWidget):
  """

  An options widget for the utils.track.timingsFromTrackItem funtion.

  """

  optionsChanged = QtCore.Signal(dict)


  def __init__(self, parent=None):
    super(TrackItemTimingOptionsWidget, self).__init__(parent=parent)

    # Get the default options from the module
    self._options = dict(utils.track.kTimingOptionDefaults)
    self.__updatingOptions = False

    layout = QtGui.QGridLayout()
    self._buildUI(layout)
    self.setLayout(layout)

    self._readOptions()
    self._connectUI()


  def setOptions(self, opts):

    numbering = opts.get(utils.track.kTimingOption_numbering, None)
    if numbering is not None:
      self._options[utils.track.kTimingOption_numbering] = numbering

    numberStart = opts.get(utils.track.kTimingOption_customNumberingStart, None)
    if numberStart is not None:
      self._options[utils.track.kTimingOption_customNumberingStart] = numberStart

    handles = opts.get(utils.track.kTimingOption_handles, None)
    if handles is not None:
      self._options[utils.track.kTimingOption_handles] = handles

    handleLength = opts.get(utils.track.kTimingOption_customHandleLength, None)
    if handleLength is not None:
      self._options[utils.track.kTimingOption_customHandleLength] = handleLength

    retimes =  opts.get(utils.track.kTimingOption_includeRetiming, None)
    if retimes is not None:
      self._options[utils.track.kTimingOption_includeRetiming] = retimes

    inTc = opts.get(utils.track.kTimingOption_includeInTimecode, None)
    if inTc is not None:
      self._options[utils.track.kTimingOption_includeInTimecode] = inTc

    srcTc = opts.get(utils.track.kTimingOption_includeSourceTimecode, None)
    if srcTc is not None:
      self._options[utils.track.kTimingOption_includeSourceTimecode] = srcTc

    self._readOptions()
    self._optionsChanged()


  def getOptions(self):
    return dict(self._options)


  def _buildUI(self, layout):

    # Labels

    layout.addWidget(QtGui.QLabel("Frame Numbering:"), 0, 0, QtCore.Qt.AlignRight)
    layout.addWidget(QtGui.QLabel("Handles:"), 1, 0, QtCore.Qt.AlignRight)
    layout.addWidget(QtGui.QLabel("Include Timecode:"), 2, 0, QtCore.Qt.AlignRight)

    # Combos

    self._numberingCombo = QtGui.QComboBox()
    items = ("Match Source Clip", "Start At")
    self._numberingCombo.addItems(items)
    layout.addWidget(self._numberingCombo, 0, 1)

    self._handlesCombo = QtGui.QComboBox()
    items = ("None", "Fixed", "Clip Extents", "Clip Extents + Fixed")
    self._handlesCombo.addItems(items)
    layout.addWidget(self._handlesCombo, 1, 1)

    # Custom Fields

    self._customNumSpinner = QtGui.QSpinBox()
    self._customNumSpinner.setMinimum(0)
    self._customNumSpinner.setMaximum(9999999)
    self._customNumSpinner.setMaximumWidth(60)
    layout.addWidget(self._customNumSpinner, 0, 2)

    self._handleLengthSpinner = QtGui.QSpinBox()
    self._handleLengthSpinner.setMinimum(0)
    self._handleLengthSpinner.setMaximum(10000)
    self._handleLengthSpinner.setMaximumWidth(60)
    layout.addWidget(self._handleLengthSpinner, 1, 2)

    # Checkboxes

    tcHBox = QtGui.QHBoxLayout()

    self._setSrcTcCB = QtGui.QCheckBox("Src In")
    tcHBox.addWidget(self._setSrcTcCB)
    self._setCutTcCB = QtGui.QCheckBox("Dst In")
    tcHBox.addWidget(self._setCutTcCB)
    tcHBox.addStretch()

    layout.addLayout(tcHBox, 2, 1, 1, 2)

    self._includeRetimesCB = QtGui.QCheckBox("Durations Include Retiming")
    layout.addWidget(self._includeRetimesCB, 0, 3)


  def _connectUI(self):

    self._numberingCombo.currentIndexChanged.connect(self._optionsChanged)
    self._handlesCombo.currentIndexChanged.connect(self._optionsChanged)
    self._customNumSpinner.valueChanged.connect(self._optionsChanged)
    self._handleLengthSpinner.valueChanged.connect(self._optionsChanged)
    self._setCutTcCB.stateChanged.connect(self._optionsChanged)
    self._setSrcTcCB.stateChanged.connect(self._optionsChanged)
    self._includeRetimesCB.stateChanged.connect(self._optionsChanged)


  def _readOptions(self):

    self.__updatingOptions = True

    index = utils.track.kTimingOptions_numbering.index(
        self._options[utils.track.kTimingOption_numbering])
    if index != -1:
      self._numberingCombo.setCurrentIndex(index)

    index = utils.track.kTimingOptions_handles.index(
        self._options[utils.track.kTimingOption_handles])
    if index != -1:
      self._handlesCombo.setCurrentIndex(index)

    try:
      val = int(self._options[utils.track.kTimingOption_customNumberingStart])
      self._customNumSpinner.setValue(val)
    except ValueError:
      pass

    try:
      val = int(self._options[utils.track.kTimingOption_customHandleLength])
      self._handleLengthSpinner.setValue(val)
    except ValueError:
      pass

    cutTc = self._options[utils.track.kTimingOption_includeInTimecode]
    self._setCutTcCB.setChecked(cutTc)

    srcTc = self._options[utils.track.kTimingOption_includeSourceTimecode]
    self._setSrcTcCB.setChecked(srcTc)

    retimes = self._options[utils.track.kTimingOption_includeRetiming]
    self._includeRetimesCB.setChecked(retimes)

    self.__updatingOptions = False



  def _optionsChanged(self):

    if self.__updatingOptions:
      return

    numberingIndex = self._numberingCombo.currentIndex()
    handlesIndex = self._handlesCombo.currentIndex()

    numbering = utils.track.kTimingOptions_numbering[numberingIndex]
    handles = utils.track.kTimingOptions_handles[handlesIndex]

    # ints should be validated by the validator
    numberStart = int(self._customNumSpinner.value())
    handleLength = int(self._handleLengthSpinner.value())

    retimes = bool(self._includeRetimesCB.isChecked())
    cutTc = bool(self._setCutTcCB.isChecked())
    srcTc = bool(self._setSrcTcCB.isChecked())

    newOpts = {
      utils.track.kTimingOption_numbering : numbering,
      utils.track.kTimingOption_customNumberingStart : numberStart,
      utils.track.kTimingOption_handles : handles,
      utils.track.kTimingOption_customHandleLength : handleLength,
      utils.track.kTimingOption_includeRetiming : retimes,
      utils.track.kTimingOption_includeInTimecode : cutTc,
      utils.track.kTimingOption_includeSourceTimecode : srcTc
    }

    if newOpts == self._options:
      return

    self._customNumSpinner.setEnabled(numbering == 'custom')
    self._handleLengthSpinner.setEnabled(handles in ('custom', 'customClip'))

    self._options.update(newOpts)
    self.optionsChanged.emit(self.getOptions())


class AdvancedHieroItemSpreadsheet(ItemSpreadsheetWidget):

  def __init__(self, *args, **kwargs):
    super(AdvancedHieroItemSpreadsheet, self).__init__(*args, **kwargs)

    self._columnTitle = 'Status'

    self._disabledText = ''
    self._enabledText = ''
    self._textCallback = None

    self._enabledIcon = QtGui.QIcon("icons:status/TagFinal.png")
    self._disabledIcon = QtGui.QIcon("icons:status/TagOmitted.png")
    self._iconCallback = None

    self._disabledCallback = None
    self._disableItems = True

    self._statusIndex = -1
    self._iconIndex = -1


  def setColumnTitle(self, title):
    self._columnTitle = title

  def getColumnTitle(self):
    return self._columnTitle


  def setStatusText(self, enabled, disabled):
    self._enabledText = enabled
    self._disabledText = disabled

  def getStatusText(self):
    return (self._enabledText, self._disabledText)


  def setIcons(self, enabledIcon, disabledIcon):
    self._enabledIcon = enabledIcon
    self._disabledIcon = disabledIcon

  def getIcons(self):
    return (self._enabledIcon, self._disabledIcon)


  def setDisabledCallback(self, callable):
    self._disabledCallback = callable

  def getDisabledCallback(self):
    return self._disabledCallback


  def setStatusCallback(self, callable):
    self._textCallback = callable

  def getStatusCallback(self):
    return self._textCallback


  def setIconCallback(self, callable):
    self._iconCallback = callable

  def getIconCallback(self):
    return self._iconCallback


  def setDisableItems(self, disableItems):
    self._disableItems = disableItems

  def getDisableItems(self):
    return self._disableItems


  def _itemIsDisabled(self, item):
    if self._disabledCallback:
      return self._disabledCallback(item)


  def _createTreeItem(self, item):

    t = super(AdvancedHieroItemSpreadsheet, self)._createTreeItem(item)
    if t:

      disabled = self._itemIsDisabled(item)

      icon = self._enabledIcon
      status = self._enabledText
      if disabled:
        icon = self._disabledIcon
        status = self._disabledText

      if self._textCallback:
        status = self._textCallback(item)

      if self._iconCallback:
        icon = self._iconCallback(item)

      if self._iconIndex > -1 and icon:
        t.setIcon(self._iconIndex, icon)
      if self._statusIndex > -1:
        t.setText(self._statusIndex, status)

      if self._disableItems:
        t.setDisabled(disabled)

      t.setSizeHint(self._statusIndex, QtCore.QSize(100, 22))

    return t


  def _buildHeaderList(self, itemMap):

    headers = super(AdvancedHieroItemSpreadsheet, self)._buildHeaderList(itemMap)
    startIndex = len(headers)

    self._iconIndex = startIndex + 1
    self._statusIndex = startIndex + 2

    headers.extend(("", self._columnTitle))

    return headers








