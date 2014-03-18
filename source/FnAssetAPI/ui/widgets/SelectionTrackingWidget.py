from .BaseWidget import BaseWidget
from . import attributes


__all__ = ['SelectionTrackingWidget']


class SelectionTrackingWidget(BaseWidget):
  """

  This class forms an intermediate base class for any widgets that desire to
  track the selection in a Host application. It simply sets the correct
  attribute bits with the kConnectSelectionChanged flag. When this flag is set,
  the Host application will automatically connect the widgets @ref
  selectionChanged method to the selctionChanged event.

  @see python.Events

  """

  def __init__(self, parent=None):
    super(SelectionTrackingWidget, self).__init__(parent=parent)


  @classmethod
  def getAttributes(cls):
    attr = super(SelectionTrackingWidget, cls).getAttributes()
    return attr | attributes.kConnectSelectionChanged


  def selectionChanged(self, entityRefs):
    """

    Generally called by the Event Manager, with a list of @ref entity_reference
    "Entity References" that represent the selection in the Host application.

    @note In situations where more than one Manager is currently active, the
    references passed may be a mixture, where only certain references are known
    to the Widget. Unknown references should be silently ignored.

    """
    raise NotImplementedError



