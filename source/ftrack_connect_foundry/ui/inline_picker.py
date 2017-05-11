# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import traceback

from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets
import FnAssetAPI.exceptions
import FnAssetAPI.logging
import FnAssetAPI.ui.widgets

import ftrack_connect_foundry.ui.browser


class InlinePicker(FnAssetAPI.ui.widgets.InlinePickerWidget):
    '''Picker to launch a browser and pick an item.'''

    def __init__(self, bridge, specification, context, parent=None):
        '''Initialise widget.'''
        self._bridge = bridge
        super(InlinePicker, self).__init__(
            specification, context, parent
        )

        self._selection = ''
        self._noSelectionMessage = 'No valid ftrack destination selected.'

        self._build()
        self._postBuild()

    def _build(self):
        '''Build and layout widget.'''
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        icon = QtWidgets.QPixmap(':icon-ftrack-box')
        smallIcon = icon.scaled(
            QtCore.QSize(24, 24),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        iconLabel = QtWidgets.QLabel()
        iconLabel.setPixmap(smallIcon)
        layout.addWidget(iconLabel)

        self._label = QtWidgets.QLabel(self._noSelectionMessage)
        self._label.setEnabled(False)
        layout.addWidget(self._label)

        layout.addStretch()

        self._browseButton = QtWidgets.QPushButton('Browse...')
        layout.addWidget(self._browseButton)

    def _postBuild(self):
        '''Perform post build operations.'''
        self._browseButton.clicked.connect(self.browse)

    def browse(self):
        '''Display browser and store selected item as current selection.

        If a selection is made then also emit selection changed signal.

        '''
        current = self.getSelection()

        # Note: The context passed here is possibly a clone of the original
        # context passed in the constructor of this widget. This ensures that
        # any exterior mutations of the context do not affect the generation
        # of the inline browser.
        browser = ftrack_connect_foundry.ui.browser.BrowserDialog(
            self._bridge, self._specification, self._context
        )
        browser.setSelection(current)

        if browser.exec_():
            self.setSelection(browser.getSelection())
            self._emitSelectionChanged()

    def getSelection(self):
        '''Return current selection as a list of entity references.'''
        if self._selection:
            return [self._selection]
        else:
            return []

    def setSelection(self, entityReferences):
        '''Set current selection from list of *entityReferences*.'''
        self._selection = None
        path = None

        if entityReferences:
            entityReference = entityReferences[0]

            try:
                path = self._bridge.getEntityPath(entityReference, slash=True)
                self._selection = entityReference

            except FnAssetAPI.exceptions.InvalidEntityReference:
                FnAssetAPI.logging.debug(traceback.format_exc())

        if path:
            self._label.setText(path)
            self._label.setEnabled(True)
        else:
            self._label.setText(self._noSelectionMessage)
            self._label.setEnabled(False)
