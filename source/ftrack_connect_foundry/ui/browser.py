# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import with_statement

import os
import traceback
import functools
import getpass

from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets
import FnAssetAPI.ui.widgets
import FnAssetAPI.ui.dialogs
import FnAssetAPI.specifications
import FnAssetAPI.exceptions
import FnAssetAPI.logging
import ftrack
import ftrack_connect.ui.widget.header

import ftrack_connect_foundry.ui.detail_view


class BrowserDialog(FnAssetAPI.ui.dialogs.TabbedBrowserDialog):
    '''Tabbed dialog that displays a browser.'''

    def __init__(self, bridge, specification, context):
        '''Initialise dialog.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        The *specification* and *context* will be stored and passed to contained
        widgets.

        '''
        self._bridge = bridge
        FnAssetAPI.ui.dialogs.TabbedBrowserDialog.__init__(
            self, specification, context
        )

        self._build()
        self._postBuild()

    def _build(self):
        '''Build and layout widget.'''
        # Bind current bridge as first argument to browser class.
        browserCls = functools.partial(Browser, self._bridge)

        # Must also manually bind class methods that may be called.
        for name in ('getIdentifier', 'getDisplayName', 'getAttributes'):
            setattr(browserCls, name, getattr(Browser, name))

        self.addTab(browserCls, 'ftrack')

    def _postBuild(self):
        '''Perform post build operations.'''
        super(BrowserDialog, self)._postBuild()


class Browser(FnAssetAPI.ui.widgets.BrowserWidget):
    '''Browse entities.'''

    clickedIdSignal = QtCore.Signal(str, name='clickedIdSignal')

    def __init__(self, bridge, specification, context, parent=None):
        '''Initialise widget.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        '''
        self._bridge = bridge
        self._specification = specification
        self._context = context

        super(Browser, self).__init__(specification, context, parent=parent)

        self._selectionValid = False
        self._componentNamesFilter = None
        self._metaFilters = None

        self._showAssets = True
        self._showTasks = True
        self._showAssetVersions = True
        self._showShots = True
        self._shotsEnabled = True

        self._currentBrowsingId = None
        self._selection = []

        self._build()
        self._postBuild()

    def _build(self):
        '''Build and layout widget.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = ftrack_connect.ui.widget.header.Header(getpass.getuser(), self)
        header.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(header)

        secondaryHeader = QtWidgets.QFrame()
        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        secondaryHeader.setLayout(headerLayout)
        layout.addWidget(secondaryHeader)

        self._createButton = QtWidgets.QToolButton()
        self._createButton.setIcon(
            QtGui.QIcon.fromTheme('plus', QtGui.QIcon(':icon-plus'))
        )
        headerLayout.addWidget(self._createButton)

        self._navigateUpButton = QtWidgets.QToolButton()
        self._navigateUpButton.setIcon(
            QtGui.QIcon.fromTheme('go-up', QtGui.QIcon(':icon-arrow-up'))
        )
        headerLayout.addWidget(self._navigateUpButton)

        headerLayout.addStretch(1)

        # Bookmarks
        contentSplitter = QtWidgets.QSplitter()
        layout.addWidget(contentSplitter)

        self._bookmarksView = QtWidgets.QTableWidget()
        self._bookmarksView.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self._bookmarksView.setGridStyle(QtCore.Qt.NoPen)
        self._bookmarksView.setColumnCount(1)
        self._bookmarksView.setColumnCount(1)
        self._bookmarksView.setRowCount(0)
        self._bookmarksView.horizontalHeader().setVisible(False)
        self._bookmarksView.horizontalHeader().setStretchLastSection(True)
        self._bookmarksView.verticalHeader().setVisible(False)
        self._bookmarksView.verticalHeader().setDefaultSectionSize(25)
        contentSplitter.addWidget(self._bookmarksView)

        # Navigation
        self._navigator = QtWidgets.QTableWidget()
        self._navigator.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._navigator.setGridStyle(QtCore.Qt.NoPen)
        self._navigator.setColumnCount(1)
        self._navigator.horizontalHeader().setStretchLastSection(True)
        self._navigator.verticalHeader().hide()
        self._navigator.setHorizontalHeaderLabels(['Name'])
        contentSplitter.addWidget(self._navigator)

        self._versionsNavigator = QtWidgets.QTableWidget()
        self._versionsNavigator.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self._versionsNavigator.setGridStyle(QtCore.Qt.NoPen)
        self._versionsNavigator.setColumnCount(1)
        self._versionsNavigator.verticalHeader().hide()
        self._versionsNavigator.setSortingEnabled(False)
        self._versionsNavigator.setHorizontalHeaderLabels(['Version'])
        contentSplitter.addWidget(self._versionsNavigator)

        self._componentsNavigator = QtWidgets.QTableWidget()
        self._componentsNavigator.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self._componentsNavigator.setColumnCount(1)
        self._componentsNavigator.horizontalHeader().setStretchLastSection(True)
        self._componentsNavigator.verticalHeader().hide()
        self._componentsNavigator.verticalHeader().setStretchLastSection(False)
        self._componentsNavigator.setHorizontalHeaderLabels(['Component'])
        contentSplitter.addWidget(self._componentsNavigator)

        # Details
        self._detailView = ftrack_connect_foundry.ui.detail_view.DetailView(
            self._bridge
        )
        contentSplitter.addWidget(self._detailView)

        # Location
        self._locationField = QtWidgets.QLineEdit()
        layout.addWidget(self._locationField)

        self._locationOptions = QtWidgets.QFrame()
        layout.addWidget(self._locationOptions)

        locationOptionsLayout = QtWidgets.QHBoxLayout()
        locationOptionsLayout.setContentsMargins(0, 0, 0, 0)
        self._locationOptions.setLayout(locationOptionsLayout)

        self._assetNameField = QtWidgets.QLineEdit()
        self._assetNameField.setEnabled(False)
        locationOptionsLayout.addWidget(self._assetNameField)

        self._overrideNameHintOption = QtWidgets.QCheckBox('Specify Asset Name')
        locationOptionsLayout.addWidget(self._overrideNameHintOption)

    def _postBuild(self):
        '''Perform post build operations.'''
        # Event handling
        self._createButton.clicked.connect(self._showCreateDialog)
        self._navigateUpButton.clicked.connect(self.navigateUp)

        self._bookmarksView.cellClicked.connect(self._onBookmarkCellClicked)

        self._navigator.cellClicked.connect(self._onNavigatorCellClicked)
        self._versionsNavigator.cellClicked.connect(self._onVersionCellClicked)
        self._componentsNavigator.cellClicked.connect(
            self._onComponentCellClicked
        )

        self._overrideNameHintOption.toggled.connect(
            self._assetNameField.setEnabled
        )

        self.clickedIdSignal.connect(self._onSelection)

        # Customise views using context and specification.
        #
        isGrouping = self._specification.isOfType(
            FnAssetAPI.specifications.GroupingSpecification
        )

        isShot = self._specification.isOfType(
            FnAssetAPI.specifications.ShotSpecification
        )

        isFile = self._specification.isOfType(
            FnAssetAPI.specifications.FileSpecification
        )
        isImage = self._specification.isOfType(
            FnAssetAPI.specifications.ImageSpecification
        )

        # Location options.
        displayLocationOptions = True
        if self._context.isForMultiple():
            displayLocationOptions = False

        if not isGrouping:
            if self._context.isForRead():
                self._showTasks = False
                displayLocationOptions = False
            else:
                if (
                    self._context
                    and self._context.locale
                    and self._context.locale.isOfType('ftrack.publish')
                ):
                    displayLocationOptions = False

        if isShot:
            displayLocationOptions = False

        if self._context.isForWrite() and not isFile:
            displayLocationOptions = False

        if not displayLocationOptions:
            self._locationOptions.hide()

        # Filters.
        if self._specification.getType() == 'file.nukescript':
            self._componentNamesFilter = ['nukescript']

        elif self._specification.getType() == 'file.hrox':
            self._componentNamesFilter = ['hieroproject']

        if isImage:
            self._metaFilters = ['img_main']

        # Navigators.
        if self._context.isForWrite():
            self._showAssetVersions = False

        if isShot:
            if self._context.isForWrite():
                self._shotsEnabled = False
                self._showTasks = False
                self._showAssets = False

            elif self._context.isForRead():
                self._shotsEnabled = False
                self._showTasks = False
                self._showAssets = False

        elif isFile or isImage or self._specification.isOfType('file.hrox'):

            if self._context.access in ['write']:
                self._showTasks = True
                self._showAssets = True

            elif self._context.access in ['writeMultiple']:
                self._showTasks = True
                self._showAssets = False

            if (
                self._context
                and self._context.locale
                and self._context.locale.isOfType('ftrack.publish')
            ):
                self._showAssets = False

        # Load bookmarks.
        self._populateBookmarks()

        # Set start location.
        referenceHint = self._specification.getField('referenceHint')
        if referenceHint:
            self.setStartLocation(referenceHint)

        elif 'FTRACK_TASKID' in os.environ:
            task = ftrack.Task(os.environ['FTRACK_TASKID'])
            self.setStartLocation(task.getEntityRef())

    def setStartLocation(self, startTargetHref):
        '''Set initial location to *startTargetHref*.'''
        try:
            entity = self._bridge.getEntityById(startTargetHref)
        except FnAssetAPI.exceptions.InvalidEntityReference:
            FnAssetAPI.logging.debug(traceback.format_exc())
            return

        # Determine appropriate reference.
        targetHref = None
        if isinstance(entity, ftrack.Component):
            ancestor = entity.getVersion().getAsset().getParent()
            targetHref = ancestor.getEntityRef()

        elif isinstance(entity, ftrack.Task):
            if entity.getObjectType() == 'Task':
                targetHref = entity.getParent().getEntityRef()
            else:
                targetHref = entity.getEntityRef()

        if targetHref:
            self._updateNavigator(targetHref)

            entity = self._bridge.getEntityById(targetHref)
            entityType = self._bridge.getEntityType(targetHref)
            self._selectionValid = self._isValid(entityType, entity)
            self.clickedIdSignal.emit(self._currentBrowsingId)

    def navigateUp(self):
        '''Navigate up one level from current location.'''
        entity = self._bridge.getEntityById(self._currentBrowsingId)
        if hasattr(entity, 'getParent'):
            parent = entity.getParent()
            self._updateNavigator(parent.getEntityRef())

    def _onSelection(self, selection):
        '''Process *selection* and store store result as current selection.

        Emit selection changed signal.

        '''
        if self._context.isForRead():
            entity = self._bridge.getEntityById(selection)

            # If current selection refers to an asset or version then store
            # appropriate component reference as selection. For an asset, first
            # try to retrieve the latest version.
            if (
                isinstance(entity, ftrack.Asset)
                or isinstance(entity, ftrack.AssetVersion)
            ):
                if isinstance(entity, ftrack.Asset):
                    version = entity.getVersions()[-1]
                elif isinstance(entity, ftrack.AssetVersion):
                    version = entity

                componentName = None
                if self._specification.isOfType('file.nukescript'):
                    componentName = 'nukescript'
                elif self._specification.isOfType('file.hrox'):
                    componentName = 'hieroproject'

                component = None
                if componentName is not None:
                    component = version.getComponent(name=componentName)
                else:
                    components = version.getComponents()
                    if components and len(components) == 1:
                        component = components[0]
                    else:
                        self._selectionValid = False

                if component:
                    selection = component.getEntityRef()

        self._selection = [selection]
        self.selectionChanged.emit(self._selection)

    def getSelection(self):
        '''Return list of currently selected entity references.'''
        assetName = None

        if self._overrideNameHintOption.checkState():
            assetNameText = self._assetNameField.text()
            if assetNameText != '':
                assetName = assetNameText

        if assetName:
            for index in range(len(self._selection)):
                self._selection[index] = (
                    self._selection[index] + '&assetName=' + assetName
                )

        return self._selection

    def setSelection(self, selection):
        '''Set selection from list of entity references in *selection*.

        .. note::

            Only supports setting Component selection in write mode, but this
            should be the only case.

        '''
        if len(selection) > 0 and selection[0] != '':
            if len(selection) > 1:
                FnAssetAPI.logging.debug('Multi selection not yet supported.')

            selection = selection[0]
            if self._context.access in ['write', 'writeMultiple']:
                try:
                    entity = self._bridge.getEntityById(selection)
                    if isinstance(entity, ftrack.Component):
                        asset = entity.getVersion().getAsset()
                        assetId = asset.getEntityRef()

                        rowCount = self._navigator.rowCount()
                        for index in range(rowCount):
                            item = self._navigator.item(index, 0)
                            targetReference = item.data(QtCore.Qt.UserRole)

                            if targetReference == assetId:
                                self._updateNavigator(targetReference)
                                self._navigator.setCurrentCell(index, 0)

                except FnAssetAPI.exceptions.InvalidEntityReference:
                    FnAssetAPI.logging.debug(traceback.format_exc())
        else:
            FnAssetAPI.logging.debug('Could not set selection.')

    def selectionValid(self):
        '''Return whether selection is valid for context and specification.'''
        return self._selectionValid

    def _populateBookmarks(self):
        '''Populate bookmarks view.'''
        # TODO: Extract bookmarks to separate widget.
        # For now just display non-editable list of projects from ftrack.
        projects = ftrack.getProjects()
        self._bookmarksView.setRowCount(len(projects))

        # Sort projects by display name.
        projects = sorted(projects, key=lambda project: project.getName())

        for index, project in enumerate(projects):
            item = QtWidgets.QTableWidgetItem(project.getName())
            item.setData(
                QtCore.Qt.UserRole,
                project.getEntityRef()
            )

            icon = QtGui.QIcon()
            icon.addPixmap(
                QtGui.QPixmap(':icon-home'),
                QtGui.QIcon.Normal,
                QtGui.QIcon.Off
            )
            item.setIcon(icon)

            self._bookmarksView.setItem(index, 0, item)

    def _onBookmarkCellClicked(self, x, y):
        '''Handle click on bookmarks view at *x* and *y* coordinates.'''
        item = self._bookmarksView.item(x, y)
        self._updateNavigator(targetReference=item.data(QtCore.Qt.UserRole))

    def _onNavigatorCellClicked(self, x, y):
        '''Handle click on navigator view at *x* and *y* coordinates.'''
        item = self._navigator.item(x, y)
        flags = item.flags()
        if not (flags & QtCore.Qt.ItemIsEnabled):
            return

        self._updateNavigator(targetReference=item.data(QtCore.Qt.UserRole))

    def _onVersionCellClicked(self, x, y):
        '''Handle click on versions view at *x* and *y* coordinates.'''
        item = self._versionsNavigator.item(x, y)
        self._updateNavigator(targetReference=item.data(QtCore.Qt.UserRole))

    def _onComponentCellClicked(self, x, y):
        '''Handle click on components view at *x* and *y* coordinates.'''
        item = self._componentsNavigator.item(x, y)
        self._updateNavigator(targetReference=item.data(QtCore.Qt.UserRole))

    def _updateNavigator(self, targetReference):
        '''Update navigator to display entries under *targetReference*.'''
        entity = self._bridge.getEntityById(targetReference)

        # Display path to entity.
        self._locationField.setText(
            self._bridge.getEntityPath(
                targetReference, slash=True, includeAssettype=True
            )
        )

        # Update selection.
        self._currentBrowsingId = targetReference
        entityType = self._bridge.getEntityType(targetReference)
        self._selectionValid = self._isValid(entityType, entity)
        self.clickedIdSignal.emit(self._currentBrowsingId)

        # Update details view.
        self._detailView.updateDetails(self._currentBrowsingId)

        # Update other navigators.
        if hasattr(entity, 'getVersions'):
            if self._showAssetVersions == True:
                self._updateVersionsNavigator(entity)
                self._versionsNavigator.show()
            return

        elif hasattr(entity, 'getComponents'):
            components = entity.getComponents()
            importableComponents = []
            self._componentsNavigator.hide()

            for component in components:
                if self._componentNamesFilter:
                    if not component in self._componentNamesFilter:
                        continue

                if self._metaFilters:
                    metaData = component.getMeta()

                    # img_main to be replaced by settable option
                    for metaFilter in self._metaFilters:
                        if metaFilter in metaData:
                            importableComponents.append(component)

                else:
                    importableComponents.append(component)

            if len(importableComponents) > 1:
                self._updateComponentsNavigator(importableComponents)
                self._componentsNavigator.show()

            elif len(importableComponents) == 1:
                self._updateNavigator(importableComponents[0].getEntityRef())

            return

        elif entityType == 'Task':
            return

        elif isinstance(entity, ftrack.Component):
            return

        else:
            self._versionsNavigator.hide()
            self._componentsNavigator.hide()

        # Update main navigator view.
        self._navigator.setRowCount(0)
        self._versionsNavigator.setRowCount(0)

        self._navigator.setHorizontalHeaderLabels(
            [self._bridge.getEntityName(targetReference)]
        )

        children = []
        tasks = []
        assets = []

        if isinstance(entity, ftrack.Project) or isinstance(entity, ftrack.Task):
            children = entity.getChildren()

        if hasattr(entity, 'getTasks') and self._showTasks == True:
            tasks = entity.getTasks()

        if hasattr(entity, 'getAssets'):
            if (not isinstance(entity, ftrack.Project)
                and entity.getObjectType() in ['Shot', 'Sequence']
                and self._showAssets == True
            ):
                if self._componentNamesFilter:
                    assets = entity.getAssets(
                        componentNames=self._componentNamesFilter
                    )
                else:
                    assets = entity.getAssets()

        entities = children + tasks + assets
        entities = sorted(
            entities,
            key=lambda entity: self._bridge.getEntityName(
                entity.getEntityRef()
            ).lower()
        )

        self._navigator.setRowCount(len(entities))
        for index, entity in enumerate(entities):
            makeBold = None
            makeItalic = None
            makeDisabled = None

            if (
                isinstance(entity, ftrack.Task)
                and entity.getObjectType() in ['Shot', 'Sequence']
            ):
                text = self._bridge.getEntityName(
                    entity.getEntityRef()
                ) + '/'
                makeBold = True

            elif (
                isinstance(entity, ftrack.Task)
                and entity.getObjectType() in ['Task']
            ):
                text = self._bridge.getEntityName(
                    entity.getEntityRef()
                )
                makeItalic = True
                if isinstance(entity.getParent(), ftrack.Project):
                    makeDisabled = True

            elif isinstance(entity, ftrack.Asset):
                text = (
                    self._bridge.getEntityName(entity.getEntityRef())
                    + '.'
                    + entity.getType().getShort()
                )

            else:
                text = self._bridge.getEntityName(
                    entity.getEntityRef()
                )

            if entityType == 'Sequence' and self._shotsEnabled == False:
                makeDisabled = True

            item = QtWidgets.QTableWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, entity.getEntityRef())

            icon = self._getIcon(entity)
            if icon:
                item.setIcon(icon)

            if makeDisabled:
                item.setFlags(QtCore.Qt.NoItemFlags)

            self._navigator.setItem(index, 0, item)

            if makeBold:
                font = QtGui.QFont()
                font.setBold(True)
                self._navigator.item(index, 0).setFont(font)

            elif makeItalic:
                font = QtGui.QFont()
                font.setItalic(True)
                self._navigator.item(index, 0).setFont(font)

    def _updateVersionsNavigator(self, asset):
        '''Update versions navigator to display versions for *asset*.'''
        self._versionsNavigator.setRowCount(0)

        if self._componentNamesFilter:
            versions = asset.getVersions(
                componentNames=self._componentNamesFilter
            )
        else:
            versions = asset.getVersions()

        self._versionsNavigator.setRowCount(len(versions))
        self._detailView.updateDetails(asset.getEntityRef())

        for index, version in enumerate(reversed(versions)):
            text = self._bridge.getEntityName(version.getEntityRef())
            item = QtWidgets.QTableWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, version.getEntityRef())
            self._versionsNavigator.setItem(index, 0, item)

        self._versionsNavigator.setCurrentCell(0, 0)
        self._updateNavigator(versions[-1].getEntityRef())

    def _updateComponentsNavigator(self, importableComponents=[]):
        '''Update versions navigator to display *importableComponents*.'''
        self._componentsNavigator.setRowCount(0)
        self._componentsNavigator.setRowCount(len(importableComponents))

        for index, component in enumerate(importableComponents):
            text = self._bridge.getEntityName(
                component.getEntityRef()
            )
            item = QtWidgets.QTableWidgetItem(text)
            item.setData(
                QtCore.Qt.UserRole,
                component.getEntityRef()
            )
            self._componentsNavigator.setItem(index, 0, item)

        self._componentsNavigator.setCurrentCell(0, 0)
        self._updateNavigator(importableComponents[0].getEntityRef())

    def _getIcon(self, entity):
        '''Retrieve appropriate icon for *entity*.'''
        iconPath = None

        if isinstance(entity, ftrack.Project):
            iconPath = ':icon-home'

        elif isinstance(entity, ftrack.Task):
            objectType = entity.getObjectType()
            if objectType == 'Sequence':
                iconPath = ':icon-folder_open'

            elif objectType == 'Shot':
                iconPath = ':icon-movie'

            elif objectType == 'Task':
                iconPath = ':icon-signup'

            elif objectType == 'Asset Build':
                iconPath = ':icon-box'

            elif objectType is None:
                # Check for asset build id until getObjectType fixed
                if (
                    entity.get('object_typeid')
                    == 'ab77c654-df17-11e2-b2f3-20c9d0831e59'
                ):
                    iconPath = ':icon-box'

        elif isinstance(entity, ftrack.Asset):
            iconPath = ':icon-layers'

        if iconPath:
            icon = QtGui.QIcon()
            icon.addPixmap(
                QtGui.QPixmap(iconPath),
                QtGui.QIcon.Normal,
                QtGui.QIcon.Off
            )
            return icon

        return None

    def _isValid(self, entityType, entity):
        '''Return whether selection is valid for specification and context.'''
        validSelection = False

        isImage = isinstance(
            self._specification, FnAssetAPI.specifications.ImageSpecification
        )
        isFile = isinstance(
            self._specification, FnAssetAPI.specifications.FileSpecification
        )
        isShot = isinstance(
            self._specification, FnAssetAPI.specifications.ShotSpecification
        )

        if isShot:
            if self._context.access in ['write', 'writeMultiple']:
                if entityType in ['Sequence']:
                    validSelection = True

            elif self._context.access in ['read', 'readMultiple']:
                if entityType in ['Sequence']:
                    validSelection = True

        elif isImage or isFile or self._specification.getType() == 'file.hrox':
            if entityType in ['Task']:
                if self._context.access in ['write', 'writeMultiple']:
                    parentEntity = entity.getParent().get('entityType')
                    if parentEntity != 'show':
                        validSelection = True

            elif entityType in ['Sequence', 'Shot']:
                if self._context.access in ['write', 'writeMultiple']:
                    validSelection = True

            elif isinstance(entity, ftrack.Asset):
                if self._context.access in ['write']:
                    validSelection = True

            if self._context.access in ['read', 'readMultiple']:
                if (isinstance(entity, ftrack.Asset)
                    or isinstance(entity, ftrack.AssetVersion)
                    or isinstance(entity, ftrack.Component)
                ):
                    validSelection = True

            if (self._context
                and self._context.locale
                and self._context.locale.getType().startswith('ftrack.publish')
            ):
                if entityType != 'Task':
                    validSelection = False
                else:
                    validSelection = True

        return validSelection

    def _showCreateDialog(self):
        '''Display create dialog and update navigator with result.'''
        dialog = CreateDialog(
            self._bridge, self, currentHref=self._currentBrowsingId
        )
        result = dialog.exec_()
        if result == 1:
            entity = self._bridge.getEntityById(dialog.currentHref)
            entityType = dialog.getEntityType()
            entityName = dialog.getEntityName()

            if entityType == 'seq':
                entity.createSequence(name=entityName)

            elif entityType == 'shot':
                entity.createShot(name=entityName)

            elif entityType == 'task':
                taskType = ftrack.TaskType(dialog.getTaskType())
                entity.createTask(name=entityName, taskType=taskType)

            self._updateNavigator(entity.getEntityRef())


class CreateDialog(QtWidgets.QDialog):
    '''Display options for creating new entities.'''

    def __init__(self, bridge, parent=None, currentHref=None):
        '''Initialise bridge.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        '''
        self._bridge = bridge
        self._currentHref = currentHref
        self.currentHref = None

        QtWidgets.QDialog.__init__(self, parent)

        if not self._currentHref:
            self.reject()

        self._build()
        self._postBuild()

    def _build(self):
        '''Build and layout widget.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(layout)

        formLayout = QtWidgets.QGridLayout()
        layout.addLayout(formLayout)

        self._nameLabel = QtWidgets.QLabel('Name')
        formLayout.addWidget(self._nameLabel, 2, 0, 1, 1)

        self._nameInput = QtWidgets.QLineEdit()
        formLayout.addWidget(self._nameInput, 2, 1, 1, 1)

        self._typeLabel = QtWidgets.QLabel('Type')
        self._typeLabel.setEnabled(True)
        formLayout.addWidget(self._typeLabel, 1, 0, 1, 1)

        self._typeSelector = QtWidgets.QComboBox()
        self._typeSelector.setEnabled(True)
        formLayout.addWidget(self._typeSelector, 1, 1, 1, 1)

        self._objectLabel = QtWidgets.QLabel('Object')
        formLayout.addWidget(self._objectLabel, 0, 0, 1, 1)

        self._objectSelector = QtWidgets.QComboBox()
        formLayout.addWidget(self._objectSelector, 0, 1, 1, 1)

        controlsLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(controlsLayout)

        spacerItem = QtWidgets.QSpacerItem(
            10, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        controlsLayout.addItem(spacerItem)

        self._cancelButton = QtWidgets.QPushButton('Cancel')
        controlsLayout.addWidget(self._cancelButton)

        self._createButton = QtWidgets.QPushButton('Create')
        self._createButton.setAutoDefault(True)
        self._createButton.setDefault(True)
        controlsLayout.addWidget(self._createButton)

    def _postBuild(self):
        '''Perform post build operations.'''
        self.setWindowTitle('New Entity')

        # Determine and store current reference.
        entity = self._bridge.getEntityById(self._currentHref)
        entityType = self._bridge.getEntityType(self._currentHref)
        self.currentHref = self.setWhereToCreate(entity)
        entity = self._bridge.getEntityById(self.currentHref)

        # Events.
        self._objectSelector.currentIndexChanged[int].connect(
            self.objectTypeChanged
        )
        self._createButton.clicked.connect(self.accept)
        self._cancelButton.clicked.connect(self.reject)

        # Populate selectors and decide which to enable.
        disableType = None
        if hasattr(entity, 'createSequence'):
            self._objectSelector.addItem('Sequence', 'seq')
            disableType = True

        if hasattr(entity, 'createShot'):
            if entityType in ['Project', 'Sequence']:
                self._objectSelector.addItem('Shot', 'shot')
                disableType = True

        if hasattr(entity, 'createTask'):
            self._objectSelector.addItem('Task', 'task')

        taskTypes = ftrack.getTaskTypes()
        for taskType in taskTypes:
            self._typeSelector.addItem(
                taskType.getName(), taskType.getEntityRef()
            )

        if disableType:
            self._typeSelector.setEnabled(False)
            self._typeLabel.setEnabled(False)

    def getEntityName(self):
        '''Return name of entity to create.'''
        return self._nameInput.text()

    def getEntityType(self):
        '''Return type of entity to create.'''
        currentIndex = self._objectSelector.currentIndex()
        return self._objectSelector.itemData(currentIndex)

    def getTaskType(self):
        '''Return task type.'''
        currentIndex = self._typeSelector.currentIndex()
        return self._typeSelector.itemData(currentIndex)

    def objectTypeChanged(self, currentIndex):
        '''Handle change of entity type.'''
        itemData = self._objectSelector.itemData(currentIndex)
        if itemData == 'task':
            self._typeSelector.setEnabled(True)
            self._typeLabel.setEnabled(True)
        else:
            self._typeSelector.setEnabled(False)
            self._typeLabel.setEnabled(False)

    def setWhereToCreate(self, entity):
        '''Return entity reference for appropriate ancestor of *obj*.'''
        entityType = self._bridge.getEntityType(entity.getEntityRef())

        if entityType == 'Component':
            entity = entity.getVersion().getAsset().getParent()

        elif entityType == 'AssetVersion':
            entity = entity.getAsset().getParent()

        elif entityType == 'Asset':
            entity = entity.getParent()

        elif entityType == 'Task':
            entity = entity.getParent()

        return entity.getEntityRef()
