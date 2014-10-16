# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import FnAssetAPI.implementation

import ftrack_connect_foundry.bridge
import ftrack_connect_foundry.manager


class Plugin(FnAssetAPI.implementation.ManagerPlugin):
    '''FTrack manager plugin.'''

    _bridge = None

    @classmethod
    def _initialiseBridge(cls):
        '''Initialise bridge.'''
        if cls._bridge is None:
            cls._bridge = ftrack_connect_foundry.bridge.Bridge()

    @classmethod
    def getIdentifier(cls):
        '''Return unique identifier for plugin.'''
        return ftrack_connect_foundry.bridge.Bridge.getIdentifier()

    @classmethod
    def getInterface(cls):
        '''Return instance of manager interface.'''
        cls._initialiseBridge()
        return ftrack_connect_foundry.manager.ManagerInterface(cls._bridge)

    @classmethod
    def getUIDelegate(cls, interfaceInstance):
        '''Return instance of UI delegate.'''
        cls._initialiseBridge()

        # This import is here as certain ui modules should not be loaded
        # unless a ui delegate is requested.
        import ftrack_connect_foundry.ui.delegate

        return ftrack_connect_foundry.ui.delegate.Delegate(cls._bridge)
