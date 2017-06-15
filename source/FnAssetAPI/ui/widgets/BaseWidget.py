from ...ui.toolkit import QtGui, QtWidgets


__all__ = ['BaseWidget']


class BaseWidget(QtWidgets.QFrame):
  """

  A backing for all QWidget based widgets within the Asset API.

  Any widgets provided to the API should derive from this class, it should be
  thought of as a QtGui.QWidget, but any coding should support both PySide and
  PyQt, there is an abstraction @ref python.ui.toolkit that will always point
  to the correct toolkit so imports of QtCore/et.al. should be done from
  there.

  """

  def __init__(self, parent=None):
    super(BaseWidget, self).__init__(parent)

  @classmethod
  def getIdentifier(cls):
    """

    Returns the identifier for this widget @ref python.ui.

    This is used by a host to request widgets for specific roles. For example,
    a widget that implements an Info Panel should return @ref
    python.ui.constants.kInfoWidgetId.

    Within any Manager, each identifier should only be represented once.

    By default this returns cls._kIdentifier, so it may not be necessary to
    override this method in a subclass, just that attribute.

    @return str, an ASCII compatible string using only the alphanum characters
    and '.', '-' and '_'.

    """
    return cls._kIdentifier

  @classmethod
  def getDisplayName(cls):
    """

    Returns a display name for the widget.

    This is used by a host to label the widget in the UI. If you are
    implementing one of the core widgets, then you should use the appropriate
    constant in the @ref python.ui module. For example, if implementing @ref
    python.ui.constants.kInfoWidgetId then this function should return @ref
    python.ui.constants.kInfoWidgetName

    @return str, any ASCII compatible single-line string, though long names are
    discouraged.

    """
    return cls._kDisplayName

  @classmethod
  def getAttributes(cls):
    """

    Properties of the widget.

    The UI framework supports various properties to automate
    connectivity/etc... within the host. For example, attributes can request
    that upon instantiation, the widget is connected to the @ref
    python.ui.SelectionTracker.

    These are bitmasks, defined in @ref python.ui.widgets.attributes

    @return int, The relevant bitmask

    @see python.UISessionManager.getManagerWidget

    """
    return 0


