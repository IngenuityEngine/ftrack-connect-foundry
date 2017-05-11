from ...ui.toolkit import QtCore, QtGui, QtWidgets
from ...ui import constants

from .BaseWidget import BaseWidget


__all__ = ['WorkflowRelationshipWidget']


class WorkflowRelationshipWidget(BaseWidget):

  """

  This widget provides a way for a user to select some kind of relationship
  based on pipeline or workflow steps. For example 'get me all the latest vfx
  renders' or 'get me the approved comps'.  It should not ever list individual
  entity references in the UI, this is the domain of the MultiPickerWidget.

  The widget's responsibility is to produce a 'criteria string' that describes
  this relationship. It will later be passed to the getRelatedReferences call
  along with the reference of interest. It's important that this criteria
  string does not directly reference any particular entity.

  Entity References are provided by the host in some cases in order to help
  optimise display.

  """

  _kIdentifier = constants.kWorkflowRelationshipWidgetId
  _kDisplayName = constants.kWorkflowRelationshipWidgetName


  criteriaChanged = QtCore.Signal(str)

  def __init__(self, context, parent=None):
    super(WorkflowRelationshipWidget, self).__init__(parent=parent)
    self._references = []


  def usesEntityReferences(self):
    """

    If True is returned, the holding UI will attempt to set any relevant entity
    refs into the widget if known. If these are not used, then its best to
    return False, as there can often be a significant blocking overhead
    determining these references, which affects the user's experience.

    """
    return False


  def setEntityReferences(self, entityReferences):
    """

    Called to set one or more relevant entityReferences. Generally these are
    references of interest to the user, so it may be prudent to adapt the UI to
    only reflect options valid for these entities.

    It is not advisable to store any reference to these in the criteria string,
    as the criteria string may be used again on unrelated source references.

    @param entityReferences str list, A list of @ref entity_references

    """
    self._references = entityReferences

  def getEntityReferences(self):
    """

    @return str list, Any entity references that may have been set in the
    widget for its consideration or an empty list.

    """
    return self._references


  def getCriteriaString(self):
    """

    The criteria string will be subsequently used in a call to
    @ref python.implementation.ManagerInterfaceBase.ManagerInterfaceBase.getRelatedReferences
    "getRelateReferences". It can be any ascii-compatible string in which you
    encode some representation of the widgets options. This may also be
    persisted within a Host, and re-used at a later date without reference to
    the UI, for 'refresh' type tasks.

    @return str, An ascii-compatabale string.


    """
    raise NotImplementedError

  def setCriteriaString(self, criteriaString):
    """

    Called to re-configure the widget to some pre-existing criteria.

    @param criteriaSting str, A string, as returned by @ref getCriteriaString.

    """
    raise NotImplementedError


  def _emitCriteriaChanged(self):
    """

    A convenience to emit the criteria changed signal with the current criteria
    string.

    """
    self.criteriaChanged.emit(self.getCriteriaString())



