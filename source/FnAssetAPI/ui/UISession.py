from ..Session import Session
from .. import Events
from .. import constants

from ..audit import auditApiCall


__all__ = ['UISession']


class UISession(Session):
  """

  The UISession extends a standard non-interactive/headless Session to
  incorporate access to the UI delegation functionality of a Manager.

  @see python.ui.UISessionManager.UISessionManager
  @see python.Session.Session

  """

  def __init__(self, host):
    super(UISession, self).__init__(host)

    self._managerIconChecked = False
    self._managerIcon = None
    self._managerSmallIcon = None


  def useManager(self, identifier, settings=None):
    super(UISession, self).useManager(identifier, settings=settings)

    self._managerIconChecked = False


  @auditApiCall("UISession")
  def getUIDelegate(self):
    """

    @return ManagerUIDelegate, an instance of the ManagerUIDelegate for the
    Manager that has been set for this session using @ref useManager().  This
    will be lazily constructed the first time this function is called, then
    retained.

    """
    ## @todo Does this need to cache here like the manager call? Probably not
    ## as the factory caches anyway.
    manager = self.currentManager()
    if not manager:
      raise RuntimeError("No Manager has been set in this session")
    return self._factory.instantiateUIDelegate(manager._getInterface())


  @auditApiCall("UISession")
  def getManagerWidgets(self):
    """

    Returns relevant widgets provided by the manager.
    @see python.ui.implementation.ManagerUIDelegate.getWidgets()

    """
    widgets = {}
    delegate = self.getUIDelegate()
    if delegate:
      widgets = delegate.getWidgets(self._host)
    return widgets


  ## @todo Allow args/kwargs to be passed instead of fixed parent
  @auditApiCall("UISession")
  def getManagerWidget(self, identifier, instantiate=True, throw=True,
      parent=None, args=None, kwargs=None):
    """

    Retrieves a widget with the specified identifier. Optionally creating and
    configuring an instance of it. If this is the case, any event connections
    defined by the widgets attributes, will also be handled.

    @param instantiate bool, if True, then the widget will be instantiated,
    otherwise the class will be returned.

    @param parent object, An optional parent to pass to the class on
    construction, if instantiate is True, Note: This will override any key of
    the same name in kwargs, if specified.

    @param args list, An optional list of args to pass to the widget on
    construction if instantiate is True

    @param kwargs dict, An optional dict of additional kwargs to pass to the widget on
    construction if instantiate is True

    @see @ref python.ui.implementation.BaseWidget.attributes()

    """
    widget = None

    delegate = self.getUIDelegate()
    if delegate:
      widget = delegate.getWidget(identifier)

    if widget:
      if instantiate:

        args = args if args else []
        kwargs = kwargs if kwargs else {}
        if parent:
          kwargs['parent'] = parent

        widget = widget(*args, **kwargs)

        self.configureWidget(widget)
    elif throw:
      raise RuntimeError("The Manager did not supply a widget for the id: %s"
          % identifier)

    return widget


  def configureWidget(self, widget):
    """

    Can be passed a widget instance, and any 'automagic' configuration will be
    applied. For example, the widgets attributes will be queried, and if the
    kSelectionChanged flag is set, then the widget's 'selectionChanged' method
    will be registered as a listener to the selectionChanged event.

    @param widget object, a widget instance that is a derived class of
    BaseWidget, or implements the BaseWidget class methods.

    """
    from .widgets import attributes

    # Connect any event handlers
    if hasattr(widget, 'getAttributes'):
      attr = widget.getAttributes()
      if attr & attributes.kConnectSelectionChanged:
        m = Events.getEventManager()
        m.registerListener(m.kSelectionChanged, widget.selectionChanged)


  def configureAction(self, action, addIcon=False, dynamicTitle=None):
    """

    Attempts to apply any Manager specific decorations to the action so it is
    presented in a consistent fashion. For example, set the actions Icon to
    that provided by the Manager.

    @param addIcon bool, if True, then the icon for the current manager will be
    added to the action, and the action will be marked as requiring an icon.

    """
    from .toolkit import QtGui

    if addIcon:
      action._usesManagerIcon = True

    if dynamicTitle:
      action._dynamicTitle = dynamicTitle

    if hasattr(action, '_usesManagerIcon') and action._usesManagerIcon:
      icon = self.getManagerIcon(small=True)
      action.setIcon(icon if icon else QtGui.QIcon())

    if hasattr(action, '_dynamicTitle'):
      from .. import SessionManager
      session = SessionManager.currentSession()
      expanded = session.localizeString(action._dynamicTitle)
      if hasattr(action, 'setTitle'):
        action.setTitle(expanded)
      elif hasattr(action, 'setText'):
        action.setText(expanded)


  def getManagerIcon(self, small=False):
    """

    This call is cached, so can be called frequently.

    @return QIcon, The icon for the current Manager, or None if there is no
    manager or None is provided.

    """

    if not self._managerIconChecked:

      self._managerIconChecked = True

      import os
      from .toolkit import QtCore, QtGui

      self._managerIcon = None
      self._managerSmallIcon = None

      manager = self.currentManager()
      if manager:
        info = manager.getInfo()

        iconPath = info.get(constants.kField_Icon, None)
        smallIconPath = info.get(constants.kField_SmallIcon, None)

        if iconPath and os.path.exists(iconPath):
          icon = QtGui.QIcon(iconPath)
          if not icon.isNull():
            self._managerIcon = icon

        if smallIconPath and os.path.exists(smallIconPath):
          icon = QtGui.QIcon(smallIconPath)
          if not icon.isNull():
            self._managerSmallIcon

        if not self._managerSmallIcon and self._managerIcon:
          smallSize = QtCore.QSize(24, 24)
          self._managerSmallIcon = QtGui.QIcon(self._managerIcon.pixmap(smallSize))

    if small:
      return self._managerSmallIcon
    else:
      return self._managerIcon


