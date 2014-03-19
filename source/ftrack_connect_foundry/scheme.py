# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import urlparse


def registerScheme(scheme):
    '''Register a *scheme*.'''
    for method in filter(
            lambda value: value.startswith('uses_'), dir(urlparse)
    ):
        getattr(urlparse, method).append(scheme)
