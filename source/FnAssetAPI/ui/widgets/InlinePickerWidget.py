from ...ui.toolkit import QtCore
from ...ui import constants
from ...SessionManager import SessionManager

from .BaseWidget import BaseWidget


__all__ = ['InlinePickerWidget']


class InlinePickerWidget(BaseWidget):
  """

  The InlinePickerWidget is analagous to a HTML <input> tag with type set to
  "file". Used whenever a Host wishes to allow the user to pick an Entity as
  part of a larger or more sophisticated dialog where the additional space
  required by a standard @ref BrowserWidget would be cumbersome.

  Typical presentation should provide a readout of the currently selected
  Entity, as well as the ability to pick another one, perhaps using the
  standard browsing interface as a modal dialog. eg:

        ----------------------------------
       | TNG / ODC / Shot 14 / Tiger / v4 |   [ Browse... ]
        ----------------------------------

  As much creativity and functionality as can be provided here is most welcome.
  Perhaps in the above example, each path component could be replaced with a
  Combo Box to facilitate quick changes without the need for a full browser.

  Though @ref setSelection() takes a list of entity references, it is only
  expected that this widget works on the first entity, and only allows single
  selection as far as the user is concerned.

  """

  _kIdentifier = constants.kInlinePickerWidgetId
  _kDisplayName = constants.kInlinePickerWidgetName

  selectionChanged = QtCore.Signal(list)


  def __init__(self, specification, context, parent=None):
    """

    As per the @ref BrowserWidget, the selectable Entities represented in the
    widget should be suitable for the supplied @ref Specification and @ref
    Context.

    @param specification EntitySpecification The 'type' of Entity that the
    picking should be filtered by.

    @param context Context The context that the picking is being performed
    for.

    @see python.ui.widgets.BrowserWidget.BrowserWidget for many more notes on
    interpretation of the spec and context.

    """
    super(InlinePickerWidget, self).__init__(parent=parent)
    self._specification = specification

    session = SessionManager.currentSession()
    if session:
      # Because we may wish to build a browser in a deferred fashion, rather
      # than storing the context itself, which might change in the time
      # between, we make a new context from the supplied one. This context will
      # have any meaningful state copied, but not be linked to any
      # transactions, etc... so can be safely retained.
      context = session.createContext(context)

    self._context = context


  def _emitSelectionChanged(self):
    self.selectionChanged.emit(self.getSelection())


  def getSelection(self):
    """

    @return list A list of selected @ref entity_references or an empty list.

    """
    raise NotImplementedError


  def setSelection(self, entityReferences):
    """

    Updates the widgets active selection

    Invalid selections should log a debug message, but not raise an
    exception, this is to prevent excessive user interruptions in the case of
    stale scene data being fed into the widget.

    """
    raise NotImplementedError


  ##
  # @name Selection Conveniences
  # These methods exists as conveniences to the Host application using the
  # widget, and generally don't need implementing in derived classes. Instead
  # getSelection and setSelection should be implemeted.
  #
  ## @{

  def getSelectionSingle(self):
    """

    @Return str The selection as a single @ref entity_reference rather than an
    array, using the first selected Entity if more than one had been selected.

    """
    sel = self.getSelection()
    return sel[0] if sel else ''

  def setSelectionSingle(self, entityReference):
    """

    Sets the selection of the widget to the supplied @ref entity_reference.
    Invalid selections should be silently ignored and the selection re-set.
    What constitutes 'invalid' is subject to interpretation of the current
    Specification and Context.

    @param entityReference str An @ref entity_reference

    """
    sel = [entityReference,] if entityReference else []
    self.setSelection(sel)

  ## @}

