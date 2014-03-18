from ...ui import constants

from . import attributes

from .SelectionTrackingWidget import SelectionTrackingWidget


__all__ = ['InfoWidget']


class InfoWidget(SelectionTrackingWidget):
  """

  The InfoWidget is a standardised Selection Tracking widget, that will be
  automatically connected to the selectionChanged event when instantiated.

  Its purpose is to provide the user with any meaningful 'information' about
  these entities.

  @see selectionChanged

  """

  _kIdentifier = constants.kInfoWidgetId
  _kDisplayName = constants.kInfoWidgetName


  def __init__(self, parent=None):
    super(InfoWidget, self).__init__(parent=parent)


  @classmethod
  def getAttributes(cls):
    attr = super(InfoWidget, cls).getAttributes()
    return attr | attributes.kCreateApplicationPanel


  def selectionChanged(self, entityRefs):
    """

    This method receives a list of all of the @ref entity_reference s the host
    considers 'selected'. Generally, it should be assumed that there may be
    unrecognised references within the list, and these should be silently
    ignored - for example in the case of old data, or multiple active Managers.

    The default implementation of this serves as a quick-and-dirty convenience
    for panels that only have scope to display a single Entity's information at
    one time, by taking the first reference from the list or an empty string.
    As such, panels like this can simple implement @ref setEntityReference.

    If the panel supports more sophisticated display, it should re-implement
    this method accordingly.

    @param entityRefs list(str) A list of zero or more @ref entity_reference
    "Entity References" that are considered to be currently selected.

    """
    entityRef = entityRefs[0] if entityRefs else ''
    self.setEntityReference(entityRef)


  def setEntityReference(self, entityRef):
    """

    Called to set the selection to that of a single @ref entity_reference. This
    may be called directly, or by the default implementation of @ref
    selectionChanged.

    """
    raise NotImplementedError

