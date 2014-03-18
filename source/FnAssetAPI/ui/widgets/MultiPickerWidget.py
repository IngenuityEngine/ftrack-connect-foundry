from .BaseWidget import BaseWidget
from ...ui import constants
from ...SessionManager import SessionManager


__all__ = ['MultiPickerWidget']


class MultiPickerWidget(BaseWidget):

  """

  The MultiPickerWidget is a 'spreadsheet' type widget that can be used to pick
  multiple assets. For example, listing all the Entities used by read nodes in
  a comp script, and allowing users to pick updated or replacement assets.

  There is no requirement for all listed Entities to share a common
  specification etc...

  In its simplest form, it could be a list of InlinePickerWidgets, but any
  richer functionality that say, allows a user to batch-update many references
  is the real purpose for the widget. For example, allowing all references to be
  updated to the latest etc...

  """

  _kIdentifier = constants.kMultiPickerWidgetId
  _kDisplayName = constants.kMultiPickerWidgetName

  def __init__(self, context, *args, **kwargs):
    """


    """
    super(MultiPickerWidget, self).__init__(*args, **kwargs)

    session = SessionManager.currentSession()
    if session:
      # Because we may wish to build a browser in a deferred fashion, rather
      # than storing the context itself, which might change in the time
      # between, we make a new context from the supplied one. This context will
      # have any meaningful state copied, but not be linked to any
      # transactions, etc... so can be safely retained.
      context = session.createContext(context)

    self._context = context


  def setSourceReferences(self, entityReferences, specifications):
    """

    Sets the Entity References that should be displayed in the widget.

    @param entityReferences list(str) A list of @ref entity_reference to be
    picked. It is valid for this to be an empty string, in the case of the
    desire to pick multiple new references. If any of the supplied entity
    references are correctly formated references, but invalid for the
    Specification and Context, they should be silently ignored and replaced by
    an empty string or a meaningful alternative if one is available.

    @param specifications list(Specification) A list of @ref Specification
    with the same length as the list of references. The Specification should
    describe what type of Entity the reference should represent. Specifications
    may be None, and in that case, a best-guess should be used by the Manager.

    @exeception InvalidEntityReference should be thrown if any of the supplied
    Entity References are not recognised by the Manager.

    """
    raise NotImplementedError

  def getSourceReferences(self):
    """

    @return The list of source references held in the widget, this should not
    include any modifications made by user action.

    """
    raise NotImplementedError


  def getSelection(self):
    """

    @return list(str) A list of @ref entity_refernce "Entity References" that
    reflect the updated state of the source references from user action. ie: a
    list with the same length as the supplied source references. Any of these
    can be empty strings if the user has cleared the selection.

    """
    raise NotImplementedError


