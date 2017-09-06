from .Host import Host
from . import logging


__all__ = ['QtHost']


class QtHost(Host):
  """

  A convenience class for hosts based on Qt. It provides alternate
  implementations of the log call to bind messages of significant severity to
  modal QMessageBoxes, and progress is mapped to a QProgressDialog.

  The @ref inUI method shold be implemented by derived classes if they support
  a headless/batch mode, where the UI is not initialized, otherwise the class
  assumes that QtGui can be successfully imported, as the default
  implementation always returns True.

  """

  def __init__(self, *args, **kwargs):
    super(QtHost, self).__init__(*args, **kwargs)
    self._progressDialog = None


  def inUI(self):
    """

    Determines if the application is running in a headless/batch mode, or with
    a UI.

    @return Bool True if the application has a UI.

    @note This method should be re-implemented by any Hosts that support a
    headless/batch mode where the UI is not initialized. If this call returns
    True, then this class assumes that QtGui can be successfully imported and
    ImportErrors will be raised if this is not the case.

    """
    return True


  def mainWindow(Self):
    """

    This method returns what is considered to be the 'main window' of the
    application from the point of view of UI widget parenting. 'None' is
    returned if this cannot be determined.

    """
    return None


  def log(self, message, severity):

    # First use the standard logging call.
    logging._log(message, severity, noRemap=True)

    # If we're in a UI, map any meaningful messages to a more modal UI
    # presentation.
    if self.inUI() and severity <= logging.kWarning :
      self.showMessage(message, severity)


  def showMessage(self, message, severity):
    """

    Shows a modal QMessageBox of the appropriate type given the supplied
    severity.

    @param message str, A message to display in the body of the popup.

    @param severity int, A severity index @see python.logging

    """

    from ui.toolkit import QtGui, QtWidgets

    title = logging.kSeverityNames[severity]
    title.capitalize()

    handlers = {
      logging.kCritical : QtWidgets.QMessageBox.critical,
      logging.kError: QtWidgets.QMessageBox.critical,
      logging.kWarning : QtWidgets.QMessageBox.warning
    }

    box = handlers.get(severity, QtWidgets.QMessageBox.information)
    box(self.mainWindow(), title, str(message))


  def progress(self, decimalProgress, message):
    """

    Maps a normalized decimal progress value (ie: 0-1) to a QProgressDialog
    when in the UI, instead of a standard logging print.

    @see inUI
    @see python.logging

    """

    if self.inUI():

      from ui.toolkit import QtGui, QtWidgets

      if decimalProgress < 0:
        if self._progressDialog:
          self._progressDialog.cancel()
        self._progressDialog = None
        return True

      if not self._progressDialog:
        self._initProgress()

      if decimalProgress >= 0 and decimalProgress < 1:
        self._progressDialog.forceShow()

      if message is not None:
        self._progressDialog.setLabelText(message)
      self._progressDialog.setValue(decimalProgress*100)
      QtWidgets.QApplication.instance().processEvents()

      if decimalProgress > 1:
        # The dialog should have closed itself based on the above
        # value set above max range
        self._progressDialog = None
        return False

      cancelled = self._progressDialog.wasCanceled()
      if cancelled:
        self._progressDialog = None
      return cancelled

    else:
      logging._progress(decimalProgress, message)
      return False


  def _initProgress(self):

    from ui.toolkit import QtWidgets

    progressDialog = QtWidgets.QProgressDialog(self.mainWindow())
    progressDialog.setRange(0, 100)
    progressDialog.setWindowTitle("Progress")
    progressDialog.setMinimumWidth(230)
    progressDialog.setModal(True)

    label = QtWidgets.QLabel()
    progressDialog.setLabel(label)

    self._progressDialog = progressDialog

