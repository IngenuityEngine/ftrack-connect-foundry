from ...ui.toolkit import QtCore
from ...ui import constants


__all__ = ['ParameterDelegate']


class ParameterDelegate(QtCore.QObject):
  """

  Because QWidgets can be prohibitively expensive on some platforms, parameter
  panels generally use nested layouts instead. Consequently, the 'Parameter
  Widget' must not derive from QWidget itself, and should instead be a layout.
  Derived classes should first derive from a suitable layout class, and
  additionally derive (or re-implement) functionality from this.

  The ParameterDelegate is used within Host application UI to represent a
  string that contains an @ref entity_reference. Often this will be in place of
  the applications standard string control.

  """

  _kIdentifier = constants.kParameterDelegateId
  _kDisplayName = constants.kParameterDelegateName

  valueChanged = QtCore.Signal(str)


  def __init__(self, parameterSpecification, context, parent=None):
    """

    The init method should only call super on the layout class the widget is
    derived from.

    @param parameterSpecification
    FnAssetAPI.python.specifications.Specification The specification of the
    Parameter the widget is being created for, or an EntitySpecification that
    describes the type of entity that the parameter desires to reference.

    @param context FnAssetAPI.python.Context.Context The Host context the
    parameter will be used in, this may be None.

    @param parent object the UI parent for the widget, if applicable.

    """
    raise NotImplementedError


  @classmethod
  def getIdentifier(cls):
    """

    Returns the identifier for this widget @ref python.ui.

    This is used by a host to request widgets for specific roles. For example,
    a widget that implements an Info Panel should return @ref
    python.ui.constants.kInfoWidgetId.

    Within any Manager, each identifier should only be represented once.

    By default this returns cls.kIdentifier, so it may not be necessary to
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
    return 0


  def _emitValueChanged(self):
    self.valueChanged.emit(self.getValue())

  def getValue(self):
    """

    @return str The selected @ref entity_reference as a UTF-8 encode ASCII
    string. An empty string can be returned in the case of no selection.

    """
    raise NotImplementedError

  def setValue(self, entityReference):
    """

    @param string a UTF-8 encoded ASCII string containing a single @ref
    entity_reference, or an empty string. Valid, but non-existant entity
    references should not raise any errors.

    @exception InvalidEntityReference in the case that the supplied string is
    non-empty and contains an entity reference in an invalid format.

    """
    raise NotImplementedError


  def setEnabled(self, enabled):
    """

    When disabled, the control should not be editable and any buttons/menus
    should be de-activated. Generally this is implemented by 'greying out' the
    UI. Text, etc... should not be selectable.

    """
    raise NotImplementedError

  def getEnabled(self):
    """

    @return Bool Whether or not the control is enabled.

    """
    raise NotImplementedError


  def setLocked(self, locked):
    """

    When locked, any text should still be selectable, but not changeable. The
    control should still present any utility functions that might be applicable
    to the selected reference, but the reference itself should not be
    modifiable. For example, if the control has a 'show history' action, it
    would still be available when locked, but not if the control was disabled.

    """
    raise NotImplementedError


  def getLocked(self):
    """

    @return Bool Whether or not the control is locked.

    """
    raise NotImplementedError

