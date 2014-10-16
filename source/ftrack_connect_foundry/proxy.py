# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

from FnAssetAPI.ui.toolkit import QtNetwork


def getProxy():
    '''Return network proxy for ftrack server if applicable.'''
    ftrackProxy = os.getenv('FTRACK_PROXY', '')
    if ftrackProxy != '':
        proxyAdress = ftrackProxy.split(':')[0]
        proxyPort = int(ftrackProxy.split(':')[1])
        proxy = QtNetwork.QNetworkProxy(
            QtNetwork.QNetworkProxy.HttpProxy, proxyAdress, proxyPort
        )

        return proxy

    return None


def configure():
    '''Set application level ftrack server proxy if appropriate.'''
    proxy = getProxy()
    if proxy is not None:
        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
