
class ManagerUIDelegate(object):

  """

  Handles assorted UI interactions with the @ref asset_management_system.

  Responsible for creating widgets to embed into the host interface, and performing
  actions such as browsing etc...

  @note It is fine to import UI toolkit modules at this point, but it is
  advisable to deffer them till needed if possible.

  There are two special widgets that can be returned:

  @li @ref python.ui.constants.kParameterDelegateId
  @li @ref python.ui.constants.kBrowserWidgetId

  The first will be used to draw parameters that hold an @ref entity_refrence
  The second will be used in File dialogs, etc... based on @ref
  python.Manager.managementPolicy()

  """


  def getWidget(self, identifier):
    """

    Retrieves a class that implements the widget with the supplied identifier
    (or an object that implements all of the methods of widgets.BaseWidget and
    return a widget instance when called)

    @return python.ui.widgets.BaseWidget or None if the identifier is unknown.

    @see python.ui.widgets.BaseWidget.getIdentifer

    """
    return None


  def getWidgets(self, host):
    """

    Returns the classes for all widgets the delegate supports (or objects that
    implement all of the methods of widgets.BaseWidget and return a widget
    instance when called).

    @param host python.Host, The delegate may wish to consider properties of
    the host to make sure that only relevant widgets are supplied.

    @return dict, Keys are identifiers, values are the corresponding class

    @see getWidget()
    @see python.ui.widgets.BaseWidget.getIdentifier()

    """
    return {}


  def populateUI(self, uiElement, specification, context):
    """

    This entry point provides the opportunity for a manager to add items to
    the Host UI. The locale of the context should be used to determine what UI
    element is being presented, etc...

    """
    pass




