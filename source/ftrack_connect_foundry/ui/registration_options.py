# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from FnAssetAPI.ui.toolkit import QtGui
import FnAssetAPI.ui.widgets

import ftrack_connect_foundry.constant


class RegistrationOptions(
    FnAssetAPI.ui.widgets.RegistrationManagerOptionsWidget
):
    '''Present options that can affect the registering of assets.'''

    def __init__(self, bridge, specification, context, parent=None):
        '''Initialise widget.'''
        self._bridge = bridge
        super(RegistrationOptions, self).__init__(
            specification, context, parent=parent
        )
        self._build()
        self._postBuild()

    def _build(self):
        '''Build and layout widget.'''
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if self._specification.isOfType('group'):
            self.setHidden(True)

        else:
            # Assume asset task type.
            self._taskTypeCombo = QtGui.QComboBox()
            self._taskTypeCombo.addItems(('Compositing', 'Editing'))

            taskLayout = QtGui.QHBoxLayout()
            taskLayout.addWidget(QtGui.QLabel('Create under task: '))
            taskLayout.addWidget(self._taskTypeCombo)
            layout.addLayout(taskLayout)

    def _postBuild(self):
        '''Perform post build operations.'''
        if not self._specification.isOfType('group'):

            # Set defaults.
            taskType, taskName = self._bridge.getTaskTypeAndName(
                self._specification
            )
            index = self._taskTypeCombo.findText(taskType)
            if index > -1:
                self._taskTypeCombo.setCurrentIndex(index)

            # Connect events.
            self._taskTypeCombo.currentIndexChanged.connect(
                self._emitOptionsChanged
            )

    def getOptions(self):
        '''Return dict of options to store in context.

        .. note::

            Only simple data types (or fully repr-able objects) are supported.

        '''
        options = {}

        if not self._specification.isOfType('group'):
            options[ftrack_connect_foundry.constant.TASK_TYPE_KEY] = str(
                self._taskTypeCombo.currentText()
            )

        return options

    def setOptions(self, options):
        '''Set *options*.'''
        if not self._specification.isOfType('group'):

            taskType = options.get(
                ftrack_connect_foundry.constant.TASK_TYPE_KEY, None
            )
            if taskType:
                index = self._taskTypeCombo.findText(taskType)
                if index > -1:
                    self._taskTypeCombo.setCurrentIndex(index)
