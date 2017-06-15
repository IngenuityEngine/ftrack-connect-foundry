from __future__ import with_statement
import types

from ... import logging
from ...SessionManager import SessionManager

from ..toolkit import QtGui, QtWidgets
from ..constants import kBrowserWidgetId, kBrowserWidgetName

from ...core.decorators import debugApiCall
from ...audit import auditApiCall


__all__ = ['TabbedBrowserDialog']


class TabbedBrowserDialog(QtWidgets.QDialog):
  """

  Provides a Dialog box with accept/cancel buttons and a tab layout to hold one
  or more browser widgets. Only the visible tab's widget is ever connected to
  the dialogs API, or signals.

  @todo This should really return a list of Entities, not a list of references,
  otherwise its going to be difficult to support multiple active managers in
  the future. The widget should only deal with refs, and this should take care
  of the rest.

  """

  def __init__(self, specification, context, parent=None):
    """

    Constructs an empty tabbed browser. A Specificaion and Context are required
    as many manager widgets require this in their constructor to ensure that
    the UI is properly configured.

    """
    QtWidgets.QDialog.__init__(self, parent=parent)

    logging.log("TabbedBrowserDialog(%r, %r)" % (specification,
        context), logging.kDebugAPI)

    self._specification = specification
    self._context = context

    layout = QtWidgets.QVBoxLayout(self)

    self.__tabWidget = QtWidgets.QTabWidget(self)
    self.__tabWidget.currentChanged.connect(self.__tabChanged)
    layout.addWidget(self.__tabWidget)

    self.__optionsBox = QtWidgets.QFrame(self)
    QtWidgets.QHBoxLayout(self.__optionsBox)
    layout.addWidget(self.__optionsBox)

    self.__buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok
        | QtWidgets.QDialogButtonBox.Cancel)
    self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Accept')
    layout.addWidget(self.__buttons)

    self.__buttons.accepted.connect(self.accept)
    self.__buttons.rejected.connect(self.reject)

    self.__widgetMap = {}
    self.__activeWidget = None
    self.__tabChanged(self.getCurrentTabIndex())


  @classmethod
  @auditApiCall("Browse")
  def buildForSession(cls, specification, context, parent=None, session=None):
    """

    Configures and returns a TabbedBrowserDialog instance, with the browser
    widget for the current (or supplied) session. The widget will be created to
    handle the supplied specification and context.

    """

    if not session:
      session = SessionManager.currentSession()
    if not session:
      return None

    manager = session.currentManager()
    if not manager:
      return None

    managerWidget = session.getManagerWidget(kBrowserWidgetId, instantiate=False)
    if not managerWidget:
      logging.error("The current Asset Management System does not have a browser")
      return None

    browser = cls(specification, context, parent=parent)
    browser.addTab(managerWidget, manager.getDisplayName())

    return browser


  def getOptionsFrame(self):
    """

    @return a QFrame that can be used to add custom UI components. It
    appears below the Tab widget, and above the buttons.

    """
    return self.__optionsBox


  def addTab(self, widgetCls, name=None):
    """

    Adds a tab for the supplied browser widget class.

    @param widgetCls BrowserWidget, A *class* (not an instance) of the widget
    to be inserted. It should be derived from the BrowserWidget class, and have
    a selectionChanged signal. It will be initialized with the specification
    and context passed to the constructor for the TabbedBrowserDialog instance.

    @param name str, The label for the new tab. If omitted, it will take the
    display name for the widget, as returned by getDisplayName.

    @return int, The index of the tab the widget was added to.

    """

    # Get the name from the widget if we need to/can
    if not name:
      if hasattr(widgetCls, 'getDisplayName'):
        name = widgetCls.getDisplayName()
      else:
        name = kBrowserWidgetName

    widget = widgetCls(self._specification, self._context, parent=self.__tabWidget)
    index = self.__tabWidget.addTab(widget, name)
    self.__widgetMap[index] = widget

    self.__tabChanged(self.getCurrentTabIndex())

    return index


  def setAcceptButtonEnabled(self, enabled):
    """

    Sets the enabled state of the 'Accept' button in the dialog.

    """
    self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)

  def setAcceptButtonTitle(self, title):
    """

    Sets the title for the 'Accept' button in the dialog.

    """
    self.__buttons.button(QtWidgets.QDialogButtonBox.Ok).setText(title)


  def getCurrentTabIndex(self):
    """

    Returns the index of the currently selected tab.

    """
    return self.__tabWidget.currentIndex()


  def setCurrentTabByIndex(self, index):
    """

    Sets the currently visible tab, by index.

    """
    self.__tabWidget.setCurrentIndex(index)

  def setCurrentTabByName(self, name):
    """

    Sets the currently visible tab by name.

    @return int, The tab index if a matching tab was found, otherwise -1.

    """

    for i in range(self.__tabWidget.count()):
      if self.__tabWidget.tabText(i) == name:
        self.__tabWidget.setCurrentIndex(i)
        return i

    return -1


  def getCurrentBrowserWidget(self):
    """

    Returns the widget instance for the currently visible tab.

    """
    return self.__widgetMap.get(self.__tabWidget.currentIndex())


  def getBrowser(self, index):
    """

    Returns the widget for the tab with the specified index.

    """
    return self.__widgetMap.get(index)


  @debugApiCall
  @auditApiCall("Browse")
  def getSelection(self):
    """

    Gets the current selection of the currently visible tab, regardless of
    whether or not the selection is valid or not.

    @return list of entity references

    """
    widget = self.getCurrentBrowserWidget()
    return widget.getSelection() if widget else []


  @debugApiCall
  @auditApiCall("Browse")
  def setSelection(self, selection, index=None):
    """

    Sets the selection of the currently visible tab.

    @param selection list, A list of entity references.

    @param index int, if supplied then the tab at the specified index will be
    made current before setting the selection.

    """

    if not isinstance(selection, types.ListType) and not isinstance(selection,
        types.TupleType):
      selection = [selection,]

    if index:
      self.setCurrentTabByIndex(index)

    widget = self.getCurrentBrowserWidget()
    if widget:
      return widget.setSelection(selection)



  def __tabChanged(self, index):

    # Ensure the visible tab is correctly connected to the various buttons, and
    # disconnect the how hidden tab.

    # Disconnect the now-hidden widget
    if self.__activeWidget:

      if hasattr(self.__activeWidget, 'accepted'):
        self.__activeWidget.accepted.disconnect(self.accept)
      if hasattr(self.__activeWidget, 'selectionChanged'):
        self.__activeWidget.selectionChanged.disconnect(self.__selectionChanged)

    widget = self.__widgetMap.get(index)
    self.__activeWidget = widget

    # Connect up the new one if it has the right slots
    if self.__activeWidget:

      if hasattr(self.__activeWidget, 'accepted'):
        self.__activeWidget.accepted.connect(self.accept)
      if hasattr(self.__activeWidget, 'selectionChanged'):
        self.__activeWidget.selectionChanged.connect(self.__selectionChanged)

    else:
      self.setAcceptButtonEnabled(False)

    self.__selectionChanged()


  def __selectionChanged(self, selection=None):

    ## Ensure the accept button is in a suitable state

    canAccept = False
    widget = self.getCurrentBrowserWidget()

    if widget:
      if hasattr(widget, 'selectionChanged'):
        canAccept = widget.selectionValid()
      else:
        # Make sure we don't disable the button if it doesnt have the signal
        # (This might have been called by a tab change, etc...)
        canAccept = True

    self.setAcceptButtonEnabled(canAccept)




