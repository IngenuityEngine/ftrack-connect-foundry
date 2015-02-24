# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

import FnAssetAPI.ui.implementation
import FnAssetAPI.ui.constants
import FnAssetAPI.ui

import ftrack_connect_foundry.ui.tasks_view
import ftrack_connect_foundry.ui.info_view
import ftrack_connect_foundry.ui.browser
import ftrack_connect_foundry.ui.inline_picker
import ftrack_connect_foundry.ui.workflow_relationship
import ftrack_connect_foundry.ui.registration_options


class Delegate(FnAssetAPI.ui.implementation.ManagerUIDelegate):

    def __init__(self, bridge):
        '''Initialise delegate with *bridge*.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        '''
        self._bridge = bridge

        # Store mapping of widgets to their identifiers.
        # Note: The widget classes are partialed with this delegate's bridge
        # to provide them access to common functionality whilst maintaining
        # compatibility with their parent class interfaces.
        self._widgetMapping = {}
        for widgetClass in (
            ftrack_connect_foundry.ui.info_view.InfoView,
            ftrack_connect_foundry.ui.info_view.WorkingTaskInfoView,
            ftrack_connect_foundry.ui.tasks_view.TasksView,
            ftrack_connect_foundry.ui.browser.Browser,
            ftrack_connect_foundry.ui.inline_picker.InlinePicker,
            ftrack_connect_foundry.ui.workflow_relationship.WorkflowRelationship,
            ftrack_connect_foundry.ui.registration_options.RegistrationOptions
        ):
            identifier = widgetClass.getIdentifier()

            # Bind bridge as first argument to class on instantiation.
            boundWidgetClass = functools.partial(widgetClass, self._bridge)

            # The returned callable is expected to be a class with certain
            # class methods available. Therefore, also dynamically assign
            # original class methods to wrapper.
            for name in ('getIdentifier', 'getDisplayName', 'getAttributes'):
                setattr(boundWidgetClass, name, getattr(widgetClass, name))

            self._widgetMapping[identifier] = boundWidgetClass

        super(Delegate, self).__init__()

    def getWidget(self, identifier):
        '''Return appropriate widget class for *identifier*.'''
        FnAssetAPI.logging.info(identifier)

        if identifier == FnAssetAPI.ui.constants.kBrowserWidgetId:
            FnAssetAPI.logging.info('HERE IT IS')
            return self._widgetMapping['uk.co.foundry.asset.api.ui.browser']

        return self._widgetMapping.get(identifier, None)

    def getWidgets(self, host):
        '''Return mapping of classes for all supported widgets.'''
        return self._widgetMapping.copy()
