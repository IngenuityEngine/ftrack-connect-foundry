# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import traceback

import FnAssetAPI.logging
import FnAssetAPI.exceptions
import FnAssetAPI.ui.widgets
import ftrack

import ftrack_connect_foundry.ui.web_view


class InfoView(ftrack_connect_foundry.ui.web_view.WebView,
               FnAssetAPI.ui.widgets.InfoWidget):
    '''Display information about item.'''

    def __init__(self, bridge, parent=None, entityReference=None):
        '''Initialise view.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        *parent* should be the owner of this widget.

        *entityReference* should refer to the item to display information about.

        '''
        super(InfoView, self).__init__(bridge, parent=parent)
        self.setEntityReference(entityReference)

    def setEntityReference(self, entityReference):
        '''Display information about entity referred to by *entityReference*.'''
        entity = None
        if entityReference is not None:
            try:
                entity = self._bridge.getEntityById(entityReference)
            except FnAssetAPI.exceptions.InvalidEntityReference:
                tb = traceback.format_exc()
                FnAssetAPI.logging.debug(tb)

        self.setEntity(entity)

    def setEntity(self, entity):
        '''Display information about specific *entity*.'''
        if entity is None:
            # TODO: Display nothing to display message.
            return

        if isinstance(entity, ftrack.Component):
            entity = entity.getVersion()

        if not self.getUrl():
            # Load initial page using url retrieved from entity.

            # TODO: Some types of entities don't have this yet, eg
            # assetversions. Add some checking here if it's not going to be
            # available from all entities.
            if hasattr(entity, 'getWebWidgetUrl'):
                url = entity.getWebWidgetUrl(name='info', theme='tf')
                FnAssetAPI.logging.debug(url)

                self.setUrl(url)

        else:
            # Send javascript to currently loaded page to update view.
            entityId = entity.getId()

            # NOTE: get('entityType') not supported on assetversions so
            # using private _type attribute.
            entityType = entity._type

            javascript = (
                'FT.WebMediator.setEntity({{'
                '   entityId: "{0}",'
                '   entityType: "{1}"'
                '}})'
                .format(entityId, entityType)
            )
            self.evaluateJavaScript(javascript)


class WorkingTaskInfoView(InfoView):
    '''Display information about current working task.'''

    _kIdentifier = 'com.ftrack.working_task'
    _kDisplayName = 'Working Task'

    def __init__(self, bridge, parent=None, taskId=None):
        '''Initialise view.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        *parent* should be the owner of this widget.

        *taskId* is the task to display information about. If not specified,
        look up value from :envvar:`FTRACK_TASKID`.

        '''
        if taskId is None:
            taskId = os.environ.get('FTRACK_TASKID', None)

        super(WorkingTaskInfoView, self).__init__(
            bridge, parent=parent, entityReference=taskId
        )
