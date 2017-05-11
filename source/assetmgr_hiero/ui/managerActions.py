import FnAssetAPI
from QtExt import QtGui, QtWidgets, QtCore


__all__ = ['ManagerLocalisedAction', 'ManagerPolicyDependentAction']


class ManagerLocalisedAction(QtGui.QAction):

  def __init__(self, name, parent=None):
    super(ManagerLocalisedAction, self).__init__(name, parent)

    self._name = name
    self.managerChanged()

    session = FnAssetAPI.SessionManager.currentSession()
    if session:
      session.configureAction(self, addIcon=True)


  def managerChanged(self):
    # Ensure we re-localise the label
    expanded = FnAssetAPI.l(self._name)
    self.setText(expanded)



class ManagerPolicyDependentAction(ManagerLocalisedAction):

  def __init__(self, name, specification, context, parent=None):

    self._specification = specification
    self._context = context

    self._allowedByPolicy = False

    super(ManagerPolicyDependentAction, self).__init__(name, parent=parent)

    self.managerChanged()


  def managerChanged(self):
    super(ManagerPolicyDependentAction, self).managerChanged()

    enabled = False

    # Check the policy for this state
    manager = FnAssetAPI.SessionManager.currentManager()
    if manager:
      policy = manager.managementPolicy(self._specification, self._context)
      enabled = not (policy & FnAssetAPI.constants.kIgnored)

    self.setEnabled(enabled)
    self._allowedByPolicy = enabled


