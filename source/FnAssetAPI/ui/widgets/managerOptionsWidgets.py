from ...ui.toolkit import QtCore
from ...ui import constants
from ...SessionManager import SessionManager

from .BaseWidget import BaseWidget


__all__ = [ 'ManagerOptionsWidget', 'RegistrationManagerOptionsWidget' ]


class ManagerOptionsWidget(BaseWidget):
  """

  This widget is used to present custom options specific to a particular
  Manager to the user. Because of the architecture of many hosts, it is not
  always possible to persist these options. As such, at this time it is
  generally advisable to present any required controls directly in Browser or
  *Picker widgets, and encode them in the returned @ref entity_reference.
  Mixing data like this isn't ideal, but is a compromise that should ensure
  consistent behaviour.

  Ideally, in the long term, this widget will be supported in all host
  interactions, and replace this behaviour. For now it's mainly used for
  batch-processes, or multi-step tasks, where a series of related registrations
  are performed by a Host, and so intermediate references may not be determined
  in an 'interactive way' ahead of time.

  Options returned by this widget will be available, if applicable through the
  Context @ref python.Context.managerOptions.

  @warning A Manager should NEVER modify the managerOptions of a Context
  directly, as the lifetime of these objects cannot be assumed. You should only
  ever READ options from a context.

  @warning A Manager should also implement suitable defaults should any
  managerOptions not be available. This widget will only be used when a Host is
  capable of passing the returned options to other API calls.

  The widget should also ensure it calls self.setHidden(True) if no options are
  applicable to the given Specification or Context to avoid dead space in a UI
  layout.

  A widget is free to use a frame or border if it likes, a host may, or may not
  embed the widget within a border of its own, if other options are also
  present.

  It's rare the base class will be requested, usually one of the derived, more
  specific classes will be used instead.

  """

  _kIdentifier = constants.kManagerOptionsWidgetId
  _kDisplayName = constants.kManagerOptionsWidgetName

  optionsChanged = QtCore.Signal(dict)


  def __init__(self, specification, context, parent=None):
    """

    @param specification The @ref Specification of the kind of Entity the
    options should be applicable to.

    @param context The @ref Context applicable to the imminent publish, special
    care should be payed to the interpretation of the specification in
    relation to the access and retention of the context.

    @note The base class implementation of __init__ will keep a safe-copy of
    the context and specification in as protected variables in the instance.
    @see Session.createContext. In derived classes, this method should either
    be called, or its techniques applied when the context needs to be retained.

    """
    super(ManagerOptionsWidget, self).__init__(parent=parent)

    session = SessionManager.currentSession()
    if session:
      # Because we may wish to refer to the context later, rather
      # than storing the context itself, which might change in the time
      # between, we make a new context from the supplied one. This context will
      # have any meaningful state copied, but not be linked to any
      # transactions, etc... so can be safely retained.
      context = session.createContext(context)

    self._specification = specification
    self._context = context


  def _emitOptionsChanged(self):
    self.optionsChanged.emit(self.getOptions())


  def getOptions(self):
    """

    @return dict, Any options to store in the Context's managerLocale. Note,
    these should use simple data types only, or be fully repr-able.

    """
    return {}


  def setOptions(self, options):
    """

    Called to restore any options from a previous run, etc... This may be
    called using the repr/eval'd return from getOptions.

    """
    pass



class RegistrationManagerOptionsWidget(ManagerOptionsWidget):
  """

  A ManagerOptionsWidget used when assets are being registered.

  """

  _kIdentifier = constants.kRegistrationManagerOptionsWidgetId
  _kDisplayName = constants.kRegistrationManagerOptionsWidgetName





