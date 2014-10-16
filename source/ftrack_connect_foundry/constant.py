# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

'''Useful constants.'''

#: Task type key.
TASK_TYPE_KEY = 'taskType'

#: Compositing task type.
COMPOSITING_TASK_TYPE = 'Compositing'

#: Compositing task name.
COMPOSITING_TASK_NAME = 'compositing'

#: Edit task type.
EDIT_TASK_TYPE = 'Editing'

#: Edit task name.
EDIT_TASK_NAME = 'editing'

#: Mapping of task types to task names.
TASK_TYPE_NAME_MAPPING = {
    COMPOSITING_TASK_TYPE: COMPOSITING_TASK_NAME,
    EDIT_TASK_TYPE: EDIT_TASK_NAME
}
