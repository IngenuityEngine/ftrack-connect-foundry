from ..toolkit import QtCore, QtGui, QtWidgets
from ... import logging


__all__ = [ 'SessionSettingsWidget' ]


class SessionSettingsWidget(QtWidgets.QWidget):
  """

  The SessionSettingsWidget is a convenience widget for Host applications to
  provide a generalised representation of settings for an Asset Management
  Session. Presently this displays the selected Asset Manager.

  For convenience, a separate selector is also provided to manipulate the
  API-level Logging Severity option. As this is not part of a sessions
  settings, but part of the API in general, this is not exposed through
  get/setSettings, but instead, the control directly reads/sets the static
  variable in the FnAssetAPI.logging module.

  @note This widget should not be sub-classed by Manager implementations.

  """

  sessionChanged = QtCore.Signal(object)
  sessionSettingsChanged = QtCore.Signal(object)

  def __init__(self, session=None, parent=None):
    super(SessionSettingsWidget, self).__init__(parent=parent)

    self._session = None

    layout = QtWidgets.QVBoxLayout()
    self.setLayout(layout)
    self._buildUI(layout)

    self.sessionChanged.connect(self._managerSelector.setSession)
    self.sessionChanged.connect(self.updateFromSession)


  def _buildUI(self, layout):

    managerHBox = QtWidgets.QHBoxLayout()
    managerHBox.addWidget(QtWidgets.QLabel("Manager:"))
    self._managerSelector = ManagerSelectorWidget()
    managerHBox.addWidget(self._managerSelector)
    layout.addLayout(managerHBox)

    self._managerSettings = ManagerSettingsWidget()
    layout.addWidget(self._managerSettings)

    layout.addStretch()

    loggingHBox = QtWidgets.QHBoxLayout()
    loggingHBox.addWidget(QtWidgets.QLabel("Logging:"))
    self._loggingSelector = LoggingLevelWidget()
    loggingHBox.addWidget(self._loggingSelector)
    layout.addLayout(loggingHBox)

    self._currentManager = QtWidgets.QLabel()
    layout.addWidget(self._currentManager)


  def setSession(self, session=None):
    """
    Sets the session for the UI to manage. It will update the selected
    manager, and the manager's settings accordingly to manage those of the
    current Manager.
    """
    self._session = session
    self.sessionChanged.emit(self._session)


  def getSession(self):
    return self._session


  def apply(self):
    """
    Sets the current session to use the specified manager, and sets the
    settings of the manager to those in the UI.
    """
    if not self._session:
      return

    currentIdentifier = None
    currentManager = self._session.currentManager()
    if currentManager:
      currentIdentifier = currentManager.getIdentifier()

    settings = self._managerSettings.getSettings()
    selectedIdentifier = self._managerSelector.getIdentifier()

    if selectedIdentifier != currentIdentifier:
      self._session.useManager(selectedIdentifier, settings)

    currentManager = self._session.currentManager()
    if currentManager:
      currentManager._getInterface().setSettings(settings)

    logging.displaySeverity = self._loggingSelector.getSeverityIndex()

    self.updateFromSession()

    self.sessionSettingsChanged.emit(self._session)


  def updateFromSession(self):
    """
    Updates the UI to reflect the sessions current manager and its settings.
    """
    currentIdentifier = None
    currentManager = self._session.currentManager()
    if currentManager:
      currentIdentifier = currentManager.getIdentifier()
      self._currentManager.setText("Current Manager: %s" % currentManager.getDisplayName())
    else:
      self._currentManager.setText("No Manager currently in use")

    self._managerSelector.setIdentifier(currentIdentifier)
    self._managerSettings.setManager(currentManager)

    self._loggingSelector.setSeverityIndex(logging.displaySeverity)


class LoggingLevelWidget(QtWidgets.QComboBox):

  def __init__(self, parent=None):
    super(LoggingLevelWidget, self).__init__(parent=parent)
    self.addItems(logging.kSeverityNames)

  def setSeverityIndex(self, seveityIndex):
    self.setCurrentIndex(seveityIndex)

  def getSeverityIndex(self):
    return self.currentIndex()

  def setSeverity(self, severityName):
    index = logging.kSeverityNames.index()
    if index == -1:
      raise ValueError("Unknown logging severity '%s' (%s)"
          % (severityName, ", ".join(logging.kSeverityNames)))
    self.setSeverityIndex(index)

  def getSeverity(self):
    return logging.kSeverityNames[self.getSeverityIndex()]


class ManagerSettingsWidget(QtWidgets.QWidget):

  settingsChanged = QtCore.Signal()
  ## @see __managerChanged - but its important to note that the manager
  ## instance here is *not* the one that will be in use in the session.
  managerChanged = QtCore.Signal(object)

  def __init__(self, manager=None, parent=None):
    super(ManagerSettingsWidget, self).__init__(parent=parent)

    self._layout = QtWidgets.QGridLayout()
    self.setLayout(self._layout)

    self.setManager(manager)


  def setManager(self, manager):
    self._manager = manager
    self.managerChanged.emit(manager)

  def getSettings(self):
    return {}


class ManagerSelectorWidget(QtWidgets.QComboBox):

  sessionChanged = QtCore.Signal(object)
  managerChanged = QtCore.Signal(object)

  def __init__(self, session=None, addNoneItem=True):
    super(ManagerSelectorWidget, self).__init__()

    self.sessionChanged.connect(self.updateFromSession)
    self.currentIndexChanged.connect(self.__managerChanged)

    self.addNoneItem = addNoneItem

    self._identifiers = []
    if self.addNoneItem:
      self._identifiers.append('')
      self.addItem('None')

    self.setSession(session)


  def setSession(self, session):
    self._session = session
    self.sessionChanged.emit(session)


  def apply(self):

    if not self._session:
      return

    currentIndex= self.currentIndex()
    if currentIndex >= 0:
      self._session.useManager(self._identifiers[currentIndex])


  def updateFromSession(self):

    self.clear()
    self._identifiers = []

    if self.addNoneItem:
      self._identifiers.append('')
      self.addItem('None')

    if not self._session:
      return

    managers = self._session.getRegisteredManagers()
    for i,pInfo in managers.iteritems():
      self._identifiers.append(i)
      self.addItem(pInfo['name'])

    currentIdentifier = ''
    manager = self._session.currentManager()
    if manager:
      currentIdentifier = manager.getIdentifier()
    self.setIdentifier(currentIdentifier)


  def getIdentifier(self):

    if not self._session:
      return ''

    currentSelection = self.currentIndex()
    if currentSelection == -1:
      return ''

    return self._identifiers[currentSelection]


  def setIdentifier(self, identifier):

    if not self._session:
      return

    identifier = identifier if identifier else ''

    try:
      index = self._identifiers.index(identifier)
      self.setCurrentIndex(index)
    except:
      self.setCurrentIndex(-1)


  def __managerChanged(self, index):

    manager = None

    if index > 0:
      identifier = self._identifiers[index]
      # We don't cache as otherwise the other UI code will be potentially
      # interacting with something that is already in use somewhere else.
      # This might seem counter-intuative, but the idea is not to configure the
      # manager, this isn't the same as applyign the changes to a session, its
      # to allow other UI elements to potentially display more information
      # about the selected manager, etc.... - we have to be able to do this
      # *before* it's applied to the session otherwise there is no going back
      # if the use presses 'cancel'. As such we make a new one for sure.
      manager = self._session._factory.instantiate(identifier, cache=False)

    self.managerChanged.emit(manager)





