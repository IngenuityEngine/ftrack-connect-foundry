# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from FnAssetAPI.ui.toolkit import QtGui, QtCore
import FnAssetAPI
import FnAssetAPI.ui.widgets

import ftrack


class WorkflowRelationship(
    FnAssetAPI.ui.widgets.WorkflowRelationshipWidget
):

    def __init__(self, bridge, context, parent=None):
        self._bridge = bridge
        super(WorkflowRelationship, self).__init__(context, parent)

        self._layout = QtGui.QHBoxLayout()
        self.setLayout(self._layout)

        self.workflowWidget = _WorkflowRelationshipWidget(self)

        self._layout.addWidget(self.workflowWidget)

    def getCriteriaString(self):
        return self.workflowWidget.getCriteria()


class _WorkflowRelationshipWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_WorkflowRelationship()
        self.ui.setupUi(self)

        self.ui.versionCombo.addItem('Latest', 'latest')
        self.ui.versionCombo.addItem('Latest Approved', 'latestapproved')

        taskTypes = ftrack.getTaskTypes()

        session = FnAssetAPI.SessionManager.currentSession()
        host = session.getHost()
        hostId = host.getIdentifier()

        selectTaskType = ''
        if hostId == 'uk.co.foundry.hiero':
            selectTaskType = 'Compositing'

        rowCntr = 0
        for taskType in sorted(taskTypes, key=lambda x: x.getName().lower()):
            self.ui.taskCombo.addItem(
                taskType.getName(), taskType.getEntityRef()
            )

            if taskType.getName() == selectTaskType:
                self.ui.taskCombo.setCurrentIndex(rowCntr)

            rowCntr += 1

    def getCriteria(self):
        return (
            self.ui.versionCombo.itemData(self.ui.versionCombo.currentIndex())
            + ','
            + self.ui.taskCombo.itemData(self.ui.taskCombo.currentIndex())
        )


class Ui_WorkflowRelationship(object):
    def setupUi(self, WorkflowRelationship):
        WorkflowRelationship.setObjectName("WorkflowRelationship")
        WorkflowRelationship.resize(275, 106)
        self.verticalLayout = QtGui.QVBoxLayout(WorkflowRelationship)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.label = QtGui.QLabel(WorkflowRelationship)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.taskCombo = QtGui.QComboBox(WorkflowRelationship)
        self.taskCombo.setObjectName("taskCombo")
        self.gridLayout.addWidget(self.taskCombo, 1, 1, 1, 1)
        self.versionCombo = QtGui.QComboBox(WorkflowRelationship)
        self.versionCombo.setObjectName("versionCombo")
        self.gridLayout.addWidget(self.versionCombo, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(WorkflowRelationship)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(WorkflowRelationship)
        QtCore.QMetaObject.connectSlotsByName(WorkflowRelationship)

    def retranslateUi(self, WorkflowRelationship):
        WorkflowRelationship.setWindowTitle(QtGui.QApplication.translate("WorkflowRelationship", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("WorkflowRelationship", "Task:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("WorkflowRelationship", "Version:", None, QtGui.QApplication.UnicodeUTF8))

