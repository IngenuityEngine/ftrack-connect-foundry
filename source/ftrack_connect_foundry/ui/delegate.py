# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

import FnAssetAPI.ui.implementation
import FnAssetAPI.ui.constants
import FnAssetAPI.ui

import ftrack_connect_foundry.ui.browser
import ftrack_connect_foundry.ui.inline_picker
import ftrack_connect_foundry.ui.workflow_relationship
import ftrack_connect_foundry.ui.registration_options

from FnAssetAPI.ui.toolkit import is_webwidget_supported
has_webwidgets = is_webwidget_supported()


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

        import ftrack_connect_foundry
        compatible_widgets = [
            ftrack_connect_foundry.ui.browser.Browser,
            ftrack_connect_foundry.ui.inline_picker.InlinePicker,
            ftrack_connect_foundry.ui.workflow_relationship.WorkflowRelationship,
            ftrack_connect_foundry.ui.registration_options.RegistrationOptions
        ]

        if has_webwidgets:
            import ftrack_connect_foundry.ui.tasks_view
            import ftrack_connect_foundry.ui.info_view

            incompatible_widgets = [
                ftrack_connect_foundry.ui.info_view.InfoView,
                ftrack_connect_foundry.ui.info_view.WorkingTaskInfoView,
                ftrack_connect_foundry.ui.tasks_view.TasksView,
            ]
            all_widgets = compatible_widgets + incompatible_widgets
        else:
            all_widgets = compatible_widgets

        self._widgetMapping = {}
        for widgetClass in all_widgets:
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
        return self._widgetMapping.get(identifier, None)

    def getWidgets(self, host):
        '''Return mapping of classes for all supported widgets.'''
        return self._widgetMapping.copy()
