from PySide import QtCore, QtGui

from .. import session

from FnAssetAPI.ui.widgets import SessionSettingsWidget


class AssetPreferencesDialog(QtGui.QDialog):

  def __init__(self):
    super(AssetPreferencesDialog, self).__init__()

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








