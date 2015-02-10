# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWebKit
import FnAssetAPI.ui.widgets
import FnAssetAPI.ui.widgets.attributes


class WebView(FnAssetAPI.ui.widgets.BaseWidget):
    '''Display a web view.'''

    def __init__(self, bridge, parent=None, url=None):
        '''Initialise view.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        *parent* should be the owner of this widget.

        *url* should reference a page to display.

        '''
        self._bridge = bridge
        super(WebView, self).__init__(parent)
        self._build()
        self._postBuild()

        self.setUrl(url)

    def _build(self):
        '''Build and layout widget.'''
        self.setMinimumHeight(400)
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        )

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._webView = QtWebKit.QWebView()
        layout.addWidget(self._webView)

    def _postBuild(self):
        '''Perform post build operations.'''
        self.setWindowTitle(self.getDisplayName())
        self.setObjectName(self.getIdentifier())

    def setUrl(self, url):
        '''Load *url* and display result in web view.'''
        self._webView.load(QtCore.QUrl(url))

    def getUrl(self):
        '''Return current url.'''
        url = self._webView.url().toString()
        if url in ('about:blank', ):
            return None

        return url

    @classmethod
    def getAttributes(cls):
        '''Return attributes of this widget.'''
        attributes = super(WebView, cls).getAttributes()
        return (
            attributes
            | FnAssetAPI.ui.widgets.attributes.kCreateApplicationPanel
        )

