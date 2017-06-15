..
    :copyright: Copyright (c) 2015 ftrack

.. _release/release_notes:


*************
Release notes
*************

.. release:: next
    .. change:: change
        :tags: API

        The Connect Foundry integration has changed to use the `ftrack-python-api`
        instead of the `legacy api`. Since custom locations are not compatible between
        the different APIs all users running from source with custom locations for
        the `legacy api` must either:

        #.  Use the
            `Location compatibility layer <https://bitbucket.org/ftrack/ftrack-location-compatibility/>`_
            by putting it's resource folder on the `FTRACK_EVENT_PLUGIN_PATH`.
        #.  Or, re-write the location using the `ftrack-python-api`.

        for more information about the migration process please look at the main `ftrack-connect`
        `Documentation <http://ftrack-connect.rtd.ftrack.com/en/latest/release/migration.html>

    .. change:: new
        :tags: Build track, User interface

        Added checkbox to build track from nuke scripts.

.. release:: 0.1.0
    :date: 2015-03-18

    .. change:: new
        :tags: Browse, User interface

        Added header from ftrack connect to browse window.
