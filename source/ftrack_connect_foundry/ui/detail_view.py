# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import urllib2

from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets
import ftrack


class DetailView(QtWidgets.QWidget):
    '''Display detailed information for an entity.'''

    def __init__(self, bridge, parent=None):
        '''Initialise widget.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        '''
        self._bridge = bridge
        QtWidgets.QWidget.__init__(self, parent)

        self._placholderThumbnail = (
            os.environ['FTRACK_SERVER'] + '/img/thumbnail2.png'
        )
        self._thumbnailCache = ftrack.cache.MemoryCache()

        self._build()
        self._postBuild()

    def _build(self):
        '''Create and layout widget.'''
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Thumbnail.
        self._thumbnail = QtWidgets.QLabel()
        self._thumbnail.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self._thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self._thumbnail.setFixedHeight(160)
        layout.addWidget(self._thumbnail)

        # Properties.
        self._propertyTable = QtWidgets.QTableWidget()
        self._propertyTable.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self._propertyTable.setColumnCount(1)

        headers = (
            'Name', 'Author', 'Version', 'Date', 'Comment', 'Status', 'Priority'
        )
        self._propertyTable.setRowCount(len(headers))
        self._propertyTable.setVerticalHeaderLabels(headers)

        horizontalHeader = self._propertyTable.horizontalHeader()
        horizontalHeader.hide()
        horizontalHeader.setResizeMode(QtWidgets.QHeaderView.Stretch)

        verticalHeader = self._propertyTable.verticalHeader()
        verticalHeader.setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        layout.addWidget(self._propertyTable)

    def _postBuild(self):
        '''Perform post build operations.'''

    def updateDetails(self, identifier):
        '''Update view for entity referenced by *identifier*.'''
        self.setEnabled(True)

        entity = self._bridge.getEntityById(identifier)

        name = self._bridge.getEntityName(entity.getEntityRef())
        self._propertyTable.setItem(0, 0, QtWidgets.QTableWidgetItem(name))

        assetVersion = None
        thumbnailUrl = None
        if isinstance(entity, ftrack.Asset):
            assetVersion = entity.getVersions()[-1]

        elif isinstance(entity, ftrack.AssetVersion):
            assetVersion = entity

        elif isinstance(entity, ftrack.Component):
            assetVersion = entity.getVersion()

        if assetVersion:
            thumbnailUrl = assetVersion.getThumbnail()
            authorUser = assetVersion.getUser()
            version = str(assetVersion.getVersion())
            comment = assetVersion.getComment()
            date = str(assetVersion.getDate())
            author = authorUser.getName().encode('utf-8')

            self._propertyTable.setRowHidden(1, False)
            self._propertyTable.setRowHidden(2, False)
            self._propertyTable.setRowHidden(3, False)
            self._propertyTable.setRowHidden(4, False)
            self._propertyTable.setRowHidden(5, True)
            self._propertyTable.setRowHidden(6, True)

            self._propertyTable.setItem(0, 1, QtWidgets.QTableWidgetItem(author))
            self._propertyTable.setItem(0, 3, QtWidgets.QTableWidgetItem(date))
            self._propertyTable.setItem(0, 2, QtWidgets.QTableWidgetItem(version))
            self._propertyTable.setItem(0, 4, QtWidgets.QTableWidgetItem(comment))

        else:
            if hasattr(entity, 'getThumbnail'):
                thumbnailUrl = entity.getThumbnail()

            statusName = ''
            if hasattr(entity, 'getStatus'):
                status = entity.getStatus()
                if status:
                    statusName = status.getName()

            priorityName = ''
            if hasattr(entity, 'getPriority'):
                priority = entity.getPriority()
                if priority:
                    priorityName = priority.getName()

            self._propertyTable.setRowHidden(1, True)
            self._propertyTable.setRowHidden(2, True)
            self._propertyTable.setRowHidden(3, True)
            self._propertyTable.setRowHidden(4, True)
            self._propertyTable.setRowHidden(5, False)
            self._propertyTable.setRowHidden(6, False)

            self._propertyTable.setItem(
                0, 5, QtWidgets.QTableWidgetItem(statusName)
            )
            self._propertyTable.setItem(
                0, 6, QtWidgets.QTableWidgetItem(priorityName)
            )

        if not thumbnailUrl:
            thumbnailUrl = self._placholderThumbnail

        self._updateThumbnail(self._thumbnail, thumbnailUrl)

        self._propertyTable.resizeRowsToContents()

    def _updateThumbnail(self, label, url):
        '''Update thumbnail for *label* with image at *url*.'''
        label.setText('')
        pixmap = self._pixmapFromUrl(url)

        scaledPixmap = pixmap.scaledToWidth(
            label.width(),
            mode=QtCore.Qt.SmoothTransformation
        )

        if scaledPixmap.height() > label.height():
            scaledPixmap = pixmap.scaledToHeight(
                label.height(),
                mode=QtCore.Qt.SmoothTransformation
            )

        label.setPixmap(scaledPixmap)

    def _pixmapFromUrl(self, url):
        '''Retrieve *url* and return data as a pixmap.'''
        try:
            pixmap = self._thumbnailCache.get(url)
        except KeyError:
            data = self._getFileFromUrl(url)
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            self._thumbnailCache.set(url, pixmap)

        # Handle null pixmaps. E.g. JPG on Windows.
        if pixmap.isNull():
            try:
                pixmap = self._thumbnailCache.get(self._placholderThumbnail)
            except KeyError:
                pass

        return pixmap

    def _getFileFromUrl(self, url, toFile=None, returnResponse=None):
        '''Return contents at *url*.

        If *returnResponse* is True then return the response object directly.
        Otherwise, return the html string read from the response.

        '''
        proxy = os.getenv('FTRACK_PROXY', '')
        server = os.getenv('FTRACK_SERVER', '')

        if proxy != '':
            if server.startswith('https'):
                httpHandle = 'https'
            else:
                httpHandle = 'http'

            proxy = urllib2.ProxyHandler({httpHandle: proxy})
            opener = urllib2.build_opener(proxy)
            response = opener.open(url)
            html = response.read()
        else:
            response = urllib2.urlopen(url)
            html = response.read()

        if toFile:
            output = open(toFile, 'wb')
            output.write(html)
            output.close()

        if returnResponse:
            return response

        return html