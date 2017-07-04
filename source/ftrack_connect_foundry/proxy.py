# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import re

from FnAssetAPI.ui.toolkit import QtNetwork


def getProxy():


    '''Return network proxy for ftrack server if applicable.'''
    ftrackProxy = os.getenv('FTRACK_PROXY', '')

    if ftrackProxy != '':
        proxyRegex = re.compile(
            ('^(http(s)?(:)?//)?(?P<host>[^:]*)(:(?P<port>[0-9]*))?')
        )
        proxy_data = proxyRegex.match(
            ftrackProxy
        ).groupdict()

        proxyAdress = proxy_data.get(
            'host', None
        )

        try:
            proxyPort = int(proxy_data.get(
                'port'
            ))

        except TypeError:
            proxyPort = 8080


        print proxyAdress, proxyPort

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

