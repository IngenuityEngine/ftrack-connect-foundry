# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack

import ftrack_connect_foundry.ui.web_view


class TasksView(ftrack_connect_foundry.ui.web_view.WebView):
    '''Display user tasks.'''

    _kIdentifier = 'com.ftrack.tasks'
    _kDisplayName = 'Tasks'

    def __init__(self, bridge, parent=None):
        '''Initialise view.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        *parent* should be the owner of this widget.

        '''
        url = ftrack.getWebWidgetUrl('tasks', theme='tf')
        super(TasksView, self).__init__(bridge, parent=parent, url=url)
