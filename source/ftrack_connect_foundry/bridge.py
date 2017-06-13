# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import urlparse
import itertools

import FnAssetAPI.implementation
import FnAssetAPI.constants
import FnAssetAPI.specifications
import FnAssetAPI.exceptions
import FnAssetAPI.logging
import ftrack

import ftrack_connect.session
import ftrack_connect_foundry.event
import ftrack_connect_foundry.proxy
import ftrack_connect_foundry.constant
import ftrack_connect_foundry.locker


class Bridge(object):
    '''Bridging functionality between core API's.'''

    def __init__(self):
        '''Initialise bridge.'''
        super(Bridge, self).__init__()
        self._initialized = False
        self._memoiser = ftrack.cache.Memoiser()

        self._metamap = {
            'fullname': FnAssetAPI.constants.kField_DisplayName,
            'fstart': FnAssetAPI.constants.kField_FrameStart,
            'fend': FnAssetAPI.constants.kField_FrameEnd
        }

        self._inverseMetamap = dict(
            (value, key)
            for key, value in self._metamap.iteritems()
        )

        self._metakeys = {
            'Project': ['fullname', 'startdate', 'enddate'],
            'Task': ['fstart', 'fend'],
            'AssetVersion': ['comment']
        }

        self.ftrackMetaKeys = []

    # Standard interface to fulfil FnAssetAPI requirements.
    #

    def initialize(self):
        '''Prepare for interaction with the current host.'''
        if not self._initialized:
            self._initialized = True
            self._registerEventHandlers()
            ftrack_connect_foundry.proxy.configure()

    def _registerEventHandlers(self):
        '''Register appropriate event handlers.'''

    @classmethod
    def getIdentifier(cls):
        '''Return unique identifier.'''
        return 'com.ftrack'

    @classmethod
    def getDisplayName(cls):
        '''Return human readable name.'''
        return 'ftrack'

    def getInfo(self):
        '''Return dictionary of additional useful information.'''
        return {
            'server': os.environ.get('FTRACK_SERVER', None),
            'api-key': os.environ.get('FTRACK_APIKEY', None),
            FnAssetAPI.constants.kField_Icon: os.path.join(
                os.path.dirname(__file__), 'ui', 'image', 'ftrack_logo_box.png'
            )
        }

    def managementPolicy(self, specification, context, entityRef=None):
        '''Return level of management this interface provides.'''
        # TODO: Inspect specification and set ignored on the types that are
        # not manageable.
        # TODO: Set path management flag when locations is merged in.
        policy = 0
        return policy ^ FnAssetAPI.constants.kManaged

    def flushCaches(self):
        '''Clear any internal caches.'''
        self._memoiser.cache.clear()

    def isEntityReference(self, token, context):
        '''Return whether *token* appears to be an entity reference.

        The calling *context* is also supplied, though this may be None.

        .. note::

            There is no need to perform a lookup to validate existence of
            the referenced entity at this stage. This is for determining if
            this manager should be involved with future operations against
            the token only.

        '''
        url = urlparse.urlparse(token)
        token = url.netloc
        return len(token) == 36 and token.count('-') == 4

    def getDefaultEntityReference(self, specification, context):
        '''Return default entity reference for *specification* and *context*.'''
        return ''

    def resolveEntityReference(self, entityRef, context):
        '''Resolve *entityRef* to a finalized string of data.'''
        entity = self.getEntityById(entityRef)
        resolved = None

        session = ftrack_connect.session.get_shared_session()

        if isinstance(entity, ftrack.Component):
            # Prevent writing to asset.
            # TODO: Reconsider this when locations is merged.
            if context and context.isForWrite():
                raise FnAssetAPI.exceptions.InvalidEntityReference(
                    'Cannot overwrite an existing asset.', entityRef
                )

            component = session.get(
                'Component', entity.getId()
            )

            location = session.pick_location(
                component
            )

            importPath = location.get_filesystem_path(component)
            resolved = self._conformPath(importPath)

        else:
            try:
                resolved = self.getEntityName(entity.getEntityRef())
            except:
                pass

        if resolved is None:
            raise FnAssetAPI.exceptions.EntityResolutionError(
                'Unable to resolve entity reference.', entityRef
            )

        return resolved

    def _conformPath(self, path):
        '''Return *path* processed for use by current host.'''
        return path

    def containsEntityReference(self, string, context):
        '''Return whether *string* contains an entity reference.

        The calling *context* is also supplied, though this may be None.

        '''
        return False

    def resolveInlineEntityReferences(self, string, context):
        '''Return copy of input *string* with all references resolved.'''
        return string

    def getRelatedReferences(self, entityReferences, specifications, context,
                             resultSpec=None):
        '''Return related entity references, based on specification

        For each pair of entity reference and specification from the
        corresponding list of *entityReferences* and *specifications*, a lookup
        will be done for entities that are related to the reference and also
        match the specification. The result of the lookup (a list of entity
        references) will be added as an entry to the returned list, resulting in
        a list of lists.

        .. note::

            If the number of entries in each list do not match then the last
            entry will be repeated in the shorter list.

        '''
        self.flushCaches()

        if len(entityReferences) > len(specifications):
            filler = specifications[-1]
        else:
            filler = entityReferences[-1]

        related = []
        for entityReference, specification in itertools.izip_longest(
                entityReferences, specifications, fillvalue=filler
        ):
            related.append(
                self._getRelatedReferences(
                    entityReference, specification, context, resultSpec
                )
            )

        return related

    def _getRelatedReferences(self, entityReference, specification, context,
                              resultSpecification):
        '''Return related references for *entityReference* and *specification*.

        The following specification types are supported:

            * group.shot
            * workflow
            * grouping.parent

        '''
        entity = self.getEntityById(entityReference)
        related = []

        if specification.isOfType('group.shot'):
            related = self._getRelatedShotReferences(
                entity, specification, context, resultSpecification
            )

        elif specification.isOfType('workflow'):
            related = self._getRelatedWorkflowReferences(
                entity, specification, context, resultSpecification
            )

        elif specification.isOfType('grouping.parent', includeDerived=False):
            related = self._getRelatedParentReferences(
                entity, specification, context, resultSpecification
            )

        return related

    def _getRelatedShotReferences(self, entity, specification, context,
                                  resultSpecification):
        '''Return related shot references for *entity* and *specification*.

        If the entity is a Sequence then all child shots of the entity will be
        included. Otherwise, if the entity is an Asset, AssetVersion or
        Component only the parent shot of the entity will be returned.

        If *specification* has a FnAssetAPI.constants.kField_HintName field then
        it will be used to restrict the related shots to those that match the
        name hint.

        '''
        nameHint = specification.getField(
            FnAssetAPI.constants.kField_HintName, None
        )
        entityType = self.getEntityType(entity.getEntityRef())

        related = []

        if entityType == 'Sequence':
            children = self._memoiser.call(entity.getChildren)

            if nameHint:
                # Find a shot with a specific name.
                match = children.find('name', nameHint)
                if match and hasattr(match, 'getId'):
                    related.append(match.getEntityRef())

            else:
                # Add all shots.
                for shot in children:
                    if hasattr(shot, 'getId'):
                        related.append(shot.getEntityRef())

        if (
            entityType == 'Asset'
            or entityType == 'AssetVersion'
            or entityType == 'Component'
        ):
            # If entity is of non-task type then get the parent shot.
            # TODO: Does this make sense for Tasks too?
            shot = None
            parent = entity
            parentEntityType = entityType
            while parent and (parentEntityType not in ('Shot', 'Project')):
                try:
                    parent = parent.getParent()
                except AttributeError:
                    parent = None
                else:
                    parentEntityType = self.getEntityType(parent.getEntityRef())

            if parentEntityType == 'Shot':
                shot = parent

            requestedName = nameHint

            if shot and hasattr(shot, 'getId'):
                if not requestedName or (requestedName == shot.getName()):
                    related.append(shot.getEntityRef())

        return related

    def _getRelatedWorkflowReferences(self, entity, specification, context,
                                      resultSpecification):
        '''Return related task references for *entity* and *specification*.

        Raise :py:exc:`ValueError` if the *specification* does not define a
        'criteria' field with which to determine the version and task type.

        '''
        criteria = specification.getField('criteria')
        if not criteria:
            raise ValueError(
                'No criteria specified with Workflow Specification: {0}'
                .format(specification)
            )

        FnAssetAPI.logging.debug(
            'Criterias raw: {0}'.format(criteria)
        )
        splitCriteria = criteria.split(',')
        version = splitCriteria[0]
        taskType = self.getEntityById(splitCriteria[1])
        prefeNukeScript = splitCriteria[2] == 'True'

        FnAssetAPI.logging.debug(
            'Criterias: version={0}, taskType={1}, prefeNukeScript={2}'.format(
                version, taskType, prefeNukeScript
            )
        )

        if isinstance(entity, ftrack.Task):
            tasks = entity.getTasks(taskTypes=[taskType])

        elif isinstance(entity, ftrack.Component):
            shot = entity.getVersion().getAsset().getParent()
            tasks = shot.getTasks(taskTypes=[taskType])

        else:
            tasks = []

        relatedClips = []
        relatedNukeScripts = []
        for task in tasks:
            assets = task.getAssets(assetTypes=['img', 'comp'])

            for asset in assets:
                assetVersions = asset.getVersions()

                if len(assetVersions) > 0:

                    if version == 'latest':
                        targetVersion = assetVersions[-1]

                    elif version == 'latestapproved':
                        for version in reversed(assetVersions):
                            if version.getStatus().getName() == 'Approved':
                                targetVersion = version
                                break

                    components = targetVersion.getComponents()

                    for component in components:
                        if component.get('filetype') == '.nk':
                            relatedNukeScripts.append(component.getEntityRef())

                    for component in components:
                        imgMain = component.getMeta('img_main')
                        if imgMain:
                            relatedClips.append(component.getEntityRef())

        if prefeNukeScript and relatedNukeScripts:
            return relatedNukeScripts

        return relatedClips

    def _getRelatedParentReferences(self, entity, specification, context,
                                    resultSpecification):
        '''Return reference for first contextual parent of *entity*.

        The contextual parent is a non-task such as a Project, Sequence or Shot.

        .. note::

            For compatibility with other 'get' functions the returned result is
            a list.

        '''
        if isinstance(entity, ftrack.Project):
            return []

        if (
            isinstance(entity, ftrack.Task)
            and (
                entity.getObjectType() == 'Shot'
                or entity.getObjectType() == 'Sequence'
            )
        ):
            entity = entity.getParent()

        else:
            # Traverse up to a non-task 'Task'.
            if isinstance(entity, ftrack.Component):
                entity = entity.getVersion()

            if isinstance(entity, ftrack.AssetVersion):
                entity = entity.getAsset()

            if isinstance(entity, ftrack.Asset):
                entity = entity.getParent()

            if (
                isinstance(entity, ftrack.Task)
                and entity.getObjectType() == 'Task'
            ):
                entity = entity.getParent()

        if isinstance(entity, ftrack.Task):
            return [entity.getEntityRef()]
        else:
            return []

    def setRelatedReferences(self, entityRef, relationshipSpec, relatedRefs,
                             context):
        '''Create a new relationship between the referenced entities.'''
        pass

    def entityExists(self, entityRef, context):
        '''Return whether the entity referenced by *entityRef* exists.'''
        if self.getEntityById(entityRef, False):
            return True
        else:
            return False

    def getEntityName(self, entityRef, context=None):
        '''Return entity name for *entityRef*.

        .. note::

            Do not include hierarchical or contextual information.

        '''
        entity = self.getEntityById(entityRef)

        if hasattr(entity, 'getName'):
            return entity.getName()

        elif hasattr(entity, 'getVersion'):
            return 'v' + str(entity.getVersion()).zfill(3)

        else:
            return 'unknown'

    def getEntityDisplayName(self, entityRef, context):
        '''Return human readable name for entity referenced by *entityRef*.'''
        entity = self.getEntityById(entityRef)

        # Return the hierarchy path to this entity.
        # TODO: Will this be horrendously slow?
        nameParts = [str(self.getEntityName(entity.getEntityRef()))]

        parents = entity.getParents()
        for parent in parents:
            nameParts.append(
                str(self.getEntityName(parent.getEntityRef()))
            )

        name = ' / '.join(nameParts[::-1])

        return name

    def getEntityVersionName(self, entityRef, context):
        '''Return version name for entity pointed to by *entityRef*.'''
        entity = self.getEntityById(entityRef)
        version = self._getVersionName(entity)
        return str(version)

    def getEntityVersions(self, entityRef, context, includeMetaVersions=False,
                          maxResults=-1):
        '''Return mapping of version names to entity references.'''
        entity = self.getEntityById(entityRef)

        try:
            versionEntities = self._getVersions(entity)
        except Exception, error:
            raise FnAssetAPI.exceptions.EntityResolutionError(error)

        # Limit to most recent up to maxResults.
        versionCount = len(versionEntities)
        if 0 < maxResults < versionCount:
            versionEntities = versionEntities[versionCount - maxResults:]

        versions = {}
        for version in versionEntities:
            versionName = str(self._getVersionName(version))
            versions[versionName] = version.getEntityRef()

        return versions

    def getFinalizedEntityVersion(self, entityRef, context, version=None):
        '''Return concrete entity reference for supplied *entityRef*.'''
        entity = self.getEntityById(entityRef)
        versionName = self.getEntityVersionName(entityRef, context)

        if not version:
            # For now just assume when no version is specified that the input
            # reference should be returned.
            # TODO: Implement support for 'latest' etc.
            return entityRef

        if versionName == version:
            return entityRef

        versions = self._getVersions(entity)
        versionsMapping = {}
        for version in versions:
            versionsMapping[str(self._getVersionName(version))] = version

        matchingVersion = versionsMapping.get(version, None)
        if not matchingVersion:
            raise FnAssetAPI.exceptions.EntityResolutionError(
                'Unable to find a version matching "{0}" for "{1}"'
                .format(version, self.getEntityDisplayName(entityRef, context))
            )

        if matchingVersion:
            return matchingVersion.getEntityRef()
        else:
            raise FnAssetAPI.exceptions.EntityResolutionError(
                'Unable to resolve the version "{0}" for "{1}"'
                .format(version, self.getEntityDisplayName(entityRef, context))
            )

    def _getVersions(self, entity):
        '''Return list of versions relevant to *entity*.'''
        versionEntities = []
        versions = []

        # Default to main component.
        name = 'main'

        if isinstance(entity, ftrack.Component):
            # Keep track of the component name.
            name = entity.getName()
            versions = entity.getVersion().getParent().getVersions()

        elif isinstance(entity, ftrack.AssetVersion):
            versions = entity.getParent().getVersions()

        elif isinstance(entity, ftrack.Asset):
            versions = entity.getVersions()

        for version in versions:
            try:
                component = version.getComponent(name=name)
            except ftrack.FTrackError:
                continue

            versionEntities.append(component)

        return versionEntities

    def _getVersionName(self, entity):
        '''Return name of version associated with *entity*.'''
        name = ''
        if isinstance(entity, ftrack.Component):
            entity = entity.getParent()
            name = entity.getVersion()

        elif isinstance(entity, ftrack.AssetVersion):
            name = entity.getVersion()

        elif isinstance(entity, ftrack.Asset):
            entity = entity.getVersions()[-1]
            name = entity.getVersion()

        return name

    def getEntityMetadata(self, entityRef, context):
        '''Return metadata for entity referenced by *entityRef*.'''
        entity = self.getEntityById(entityRef)
        metadata = entity.getMeta()

        # Map metadata keys into specific properties.
        try:
            mapkey = entity.__class__.__name__
            for key in self._metakeys.get(mapkey, []):
                metadata[self._metamap.get(key, key)] = entity.get(key)

        except AttributeError:
            pass

        return dict(metadata)

    def setEntityMetadata(self, entityRef, data, context, merge=True):
        '''Set metadata for entity referenced by *entityRef*.'''
        entity = self.getEntityById(entityRef)

        if (
            data.get(FnAssetAPI.constants.kField_FrameIn, None)
            and data.get(FnAssetAPI.constants.kField_FrameStart, None)
        ):
            frameStart = int(
                data.get(FnAssetAPI.constants.kField_FrameStart, 0)
            )
            frameIn = int(data.get(FnAssetAPI.constants.kField_FrameIn, 0))
            handleWidth = frameIn - frameStart
            entity.set('handles', handleWidth)

        # Detect mapped properties in metadata and set as appropriate.
        try:
            mapkey = entity.__class__.__name__
            keys = self._metakeys.get(mapkey, [])

            for key in keys:
                mappedKey = self._metamap.get(key, key)
                if mappedKey in data:
                    value = data.pop(mappedKey)
                    value = self._preProcessMeta(key, value)
                    entity.set(key, value)

        except AttributeError:
            pass

        if merge:
            existing = entity.getMeta()
            existing.update(data)
            data = existing

        entity.setMeta(data)

    def _preProcessMeta(self, key, value):
        '''Pre-process metadata *key* and *value* to strong types.

        For example, a key of 'status' would be converted to a strong TaskStatus
        object in ftrack.

        '''
        if key == 'status':
            value = str(value)
            nativeStatus = None
            available = []

            for status in ftrack.getTaskStatuses():
                available.append(status.getName())
                if status.getName() == status:
                    nativeStatus = status
                    break

            if not nativeStatus:
                raise ValueError(
                    'Unable to find the status "{0}" in {1}'
                    .format(value, available)
                )

            value = nativeStatus

        return value

    def getEntityMetadataEntry(self, entityRef, key, context):
        '''Return the value for the specified metadata *key*.'''
        entity = self.getEntityById(entityRef)
        value = None

        try:
            mapkey = entity.__class__.__name__
            keys = self._metakeys.get(mapkey, [])
            mappedKey = self._inverseMetamap.get(key, key)

            if mappedKey in keys:
                value = entity.get(mappedKey)

        except AttributeError:
            value = entity.getMeta(key)

        return value

    def setEntityMetadataEntry(self, entityRef, key, value, context):
        '''Set metadata *key* to *value*.'''
        entity = self.getEntityById(entityRef)
        try:
            mapkey = entity.__class__.__name__
            keys = self._metakeys.get(mapkey, [])
            mappedKey = self._inverseMetamap.get(key, key)

            if mappedKey in keys:
                entity.set(mappedKey, value)

        except AttributeError:
            entity.setMeta(mappedKey, value)

    def preflight(self, targetEntityRef, entitySpec, context):
        '''Prepare for work to be done to the referenced entity.

        .. warning::

            Potential assets cannot yet be represented by this manager (due to
            use of server side generated UUID as reference). As a result, cannot
            operate on non-existant entities and will raise
            :py:exc:`FnAssetAPI.exceptions.PreflightError` if the entity does
            not yet exist.

        '''
        # TODO: Consider the impact of allowing people to publish to existing
        # assets.
        if not self.entityExists(targetEntityRef, context):
            raise FnAssetAPI.exceptions.PreflightError(
                'The referenced entity does not exist and so unable to '
                'write to this asset', targetEntityRef
            )

        return targetEntityRef

    def register(self, stringData, targetEntityRef, entitySpec, context):
        '''Register entity with asset management system (a publish).'''
        try:
            # Projects.
            if entitySpec.isOfType(
                    FnAssetAPI.specifications.ProjectSpecification
            ):
                return self._registerProject(
                    stringData, targetEntityRef, entitySpec, context
                )

            # Groups such as Shots, Sequences etc.
            elif entitySpec.isOfType(
                    FnAssetAPI.specifications.GroupingSpecification
            ):
                return self._registerGrouping(
                    stringData, targetEntityRef, entitySpec, context
                )

            # Images.
            elif entitySpec.isOfType(
                    FnAssetAPI.specifications.ImageSpecification
            ):
                return self._registerImageFile(
                    stringData, targetEntityRef, entitySpec, context
                )

            # Nuke scripts.
            elif entitySpec.isOfType('file.nukescript'):
                return self._registerNukeScript(
                    stringData, targetEntityRef, entitySpec, context
                )

            # Hiero projects.
            elif entitySpec.isOfType('file.hrox'):
                return self._registerHieroProject(
                    stringData, targetEntityRef, entitySpec, context
                )

            # Files.
            elif entitySpec.isOfType('file'):
                return self._registerGenericFile(
                    stringData, targetEntityRef, entitySpec, context
                )

            else:
                raise FnAssetAPI.exceptions.RegistrationError(
                    'Unknown entity Specification: {0}'.format(entitySpec),
                    targetEntityRef
                )

        except ftrack.FTrackError, error:
            raise FnAssetAPI.exceptions.RegistrationError(
                error, targetEntityRef
            )

    def _registerProject(self, shortName, targetReference, specification,
                         context):
        '''Register a project with *shortName*.

        .. note::

            *targetReference* is ignored as a project is always a top-level
            item.

        '''
        schemes = ftrack.getProjectSchemes()
        scheme = None
        if schemes:
            scheme = schemes[0]

        project = ftrack.createProject(shortName, shortName, scheme)
        return project.getEntityRef()

    def _registerGrouping(self, shortName, targetReference, specification,
                          context):
        '''Register a grouping entity with *shortName*.

        A grouping entity could be a Sequence, Shot etc.

        '''
        # TODO: if targetReference == getRootEntityReference() then make a
        # project

        entity = self.getEntityById(targetReference)
        wrongDestinationMsg = ('Groupings can only be created under a Project '
                               'or a Sequence.')

        createFunction = None
        if isinstance(entity, ftrack.Project):
            createFunction = entity.createSequence

        elif (
            isinstance(entity, ftrack.Task)
            and entity.getObjectType() == 'Sequence'
        ):
            createFunction = entity.createShot

        if createFunction is None:
            raise FnAssetAPI.exceptions.RegistrationError(
                wrongDestinationMsg, targetReference
            )

        # For a grouping, the 'resolved string' is to be considered the name
        # if not overriden by a name hint.

        # TODO: Store the shortName somewhere as it is needed to pass back to
        # resolve later. Currently resolving using the name.
        name = specification.getField(
            FnAssetAPI.constants.kField_HintName, shortName
        )
        grouping = createFunction(name=name)

        # Upload thumbnail if provided.
        thumbnailPath = specification.getField('thumbnailPath', None)
        if thumbnailPath:
            grouping.createThumbnail(thumbnailPath)

        # Ensure correct tasks are created as well.
        # TODO: Make this configurable, possbily using task templates.
        compositingTaskType = ftrack.TaskType(
            ftrack_connect_foundry.constant.COMPOSITING_TASK_TYPE
        )
        grouping.createTask(
            ftrack_connect_foundry.constant.COMPOSITING_TASK_NAME,
            compositingTaskType
        )

        editingTaskType = ftrack.TaskType(
            ftrack_connect_foundry.constant.EDIT_TASK_TYPE
        )
        grouping.createTask(
            ftrack_connect_foundry.constant.EDIT_TASK_NAME, editingTaskType
        )

        # Return grouping id as currently don't know which task is applicable.
        # That is determined at registration when the host/specification is
        # known.
        return grouping.getEntityRef()

    def _registerNukeScript(self, path, targetReference, specification,
                            context):
        '''Register a Nuke script with *path*.'''
        return self._register(
            path, targetReference, specification, context, 'comp',
            defaultName='nukeScript', component='nukescript'
        )

    def _registerImageFile(self, path, targetReference, specification, context):
        '''Register an image file with *path*.'''
        return self._register(
            path, targetReference, specification, context, 'img',
            defaultName='imageAsset'
        )

    def _registerHieroProject(self, path, targetReference, specification,
                              context):
        '''Register a Hiero project with *path*.'''
        return self._register(
            path, targetReference, specification, context, 'edit',
            defaultName='hieroProject', component='hieroproject'
        )

    def _registerGenericFile(self, path, targetReference, specification,
                             context):
        '''Register a generic file with *path*.'''
        return self._register(
            path, targetReference, specification, context,
            specification.getType(), 'asset'
        )

    def _register(self, path, targetReference, specification, context,
                  assetType, component='main', defaultName='file',
                  readOnly=True):
        '''Register component with *path*.

        Try to find an asset using the following rules:

            #. When *targetReference* is a Task, look for/create an asset with
               matching name.
            #. When *targetReference* is an Asset, use it directly.
            #. When *targetReference* is an AssetVersion get its parent Asset.

        Then create a new AssetVersion with a component under that asset

        '''
        name = specification.getField(
            FnAssetAPI.constants.kField_HintName, defaultName
        )

        # Check for asset name.
        assetName = None
        url = urlparse.urlparse(targetReference)
        query = urlparse.parse_qs(url.query)
        if 'assetName' in query:
            assetName = query.get('assetName')[0]

        if assetName:
            name = assetName

        entity = self.getEntityById(targetReference)
        targetReference = self._getTaskId(entity, specification, context)
        entity = self.getEntityById(targetReference)

        asset = None
        if isinstance(entity, ftrack.Task):
            if entity.getObjectType() == 'Task':
                taskId = entity.getId()
                parentShot = entity.getParent()

                if parentShot.get('entityType') == 'show':
                    raise FnAssetAPI.exceptions.RegistrationError(
                        'Can not publish on a task directly below a project.'
                    )

                existing = parentShot.getAssets(
                    assetTypes=[assetType], names=[name]
                )

                if existing:
                    asset = existing[0]
                else:
                    asset = parentShot.createAsset(name, assetType)

        elif isinstance(entity, ftrack.Asset):
            asset = entity
            taskId = asset.getVersions()[-1].get('taskid')

        elif isinstance(entity, ftrack.Component):
            asset = entity.getVersion().getAsset()
            component = entity.getName()
            taskId = asset.getVersions()[-1].get('taskid')

        if not asset:
            raise FnAssetAPI.exceptions.RegistrationError(
                'Unable to find a suitable asset relating to {0}.'
                .format(entity),
                targetReference
            )
        session = ftrack_connect.session.get_shared_session()

        version = session.create('AssetVersion', {
            'asset_id':asset.getId(),
            'task_id': taskId
        })

        session.commit()

        thumbnailPath = specification.getField('thumbnailPath', None)
        if thumbnailPath:
            version.create_thumbnail(
                thumbnailPath
            )

        location = session.pick_location()

        mainComponent = version.create_component(
            path, data={'name': component}, location=location
        )

        if assetType == 'img':
            mainComponent['metadata']['img_main'] = True

        # Make readOnly so that it cannot be overwritten by anyone else.
        if readOnly and os.path.isfile(path):
            # TODO: Re-consider this when locations is merged. This is here
            # for now to stop accidents.
            ftrack_connect_foundry.locker.lockFile(path)


        # Return a reference to the main component as it is a unique address
        # when an asset contains multiple components.
        return (
            'ftrack://{0}?entityType=component'.format(
                mainComponent.get('id')
            )
        )

    def _getTaskId(self, entity, specification, context):
        '''Return task reference for *entity*.'''
        taskType, taskName = self.getTaskTypeAndName(
            specification, entity, context
        )

        if (
            hasattr(entity, 'getObjectType')
            and entity.getObjectType() in ['Shot', 'Sequence']
        ):
            ftrackTasks = entity.getTasks(taskTypes=[taskType, ])
            if len(ftrackTasks) > 0:
                task = ftrackTasks[0]
                reference = task.getEntityRef()
            else:
                taskTypeEntity = ftrack.TaskType(taskType)
                task = entity.createTask(taskName, taskTypeEntity)
                reference = task.getEntityRef()

        else:
            reference = entity.getEntityRef()

        return reference

    def thumbnailSpecification(self, specification, context, options):
        '''Return whether a thumbnail should be prepared.'''
        if specification and specification.isOfType(('file', 'group.shot')):
            return True

        return False

    # Additional interface.
    #

    def getEntityById(self, identifier, throw=True):
        '''Return an entity represented by the given *identifier*.

        If *throw* is True then raise
        :py:exc:`FnAssetAPI.exceptions.InvalidEntityReference` if no entity can
        be found, otherwise return None.

        '''
        entity = None

        if identifier != '':
            if 'ftrack://' in identifier:
                url = urlparse.urlparse(identifier)
                query = urlparse.parse_qs(url.query)
                entityType = query.get('entityType')[0]

                identifier = url.netloc

                try:
                    return self._memoiser.cache.get(identifier)
                except KeyError:
                    pass

                try:
                    if entityType == 'component':
                        entity = ftrack.Component(identifier)

                    elif entityType == 'asset_version':
                        entity = ftrack.AssetVersion(identifier)

                    elif entityType == 'asset':
                        entity = ftrack.Asset(identifier)

                    elif entityType == 'show':
                        entity = ftrack.Project(identifier)

                    elif entityType == 'task':
                        entity = ftrack.Task(identifier)

                    elif entityType == 'tasktype':
                        entity = ftrack.TaskType(identifier)
                except:
                    pass

            else:
                ftrackObjectClasses = [
                    ftrack.Task,
                    ftrack.Asset, ftrack.AssetVersion, ftrack.Component,
                    ftrack.Project,
                    ftrack.TaskType
                ]

                try:
                    return self._memoiser.cache.get(identifier)
                except KeyError:
                    pass

                for cls in ftrackObjectClasses:
                    try:
                        entity = cls(id=identifier)
                        break

                    except ftrack.FTrackError as error:
                        if error.message.find('was not found') == -1:
                            raise
                        pass

                    except Exception, error:
                        FnAssetAPI.logging.log(
                            'Exception caught trying to create {0}: {1}'.format(
                                cls.__name__, error
                            ),
                            FnAssetAPI.logging.kError
                        )
                        raise

        if not entity and throw:
            raise FnAssetAPI.exceptions.InvalidEntityReference(
                entityReference=identifier
            )

        self._memoiser.cache.set(identifier, entity)

        return entity

    def getEntityType(self, entityReference):
        '''Return a string identifying type for *entityReference*.

        Return an empty string if the type is unknown.

        '''
        entity = self.getEntityById(entityReference)
        
        if hasattr(entity, 'getObjectType'):
            return entity.getObjectType()

        elif isinstance(entity, ftrack.Asset):
            return 'Asset'

        elif isinstance(entity, ftrack.AssetVersion):
            return 'AssetVersion'

        elif isinstance(entity, ftrack.Component):
            return 'Component'

        elif isinstance(entity, ftrack.Project):
            return 'Project'

        return ''

    def getEntityPath(self, entityReference, unders=False, slash=False,
                      includeAssettype=False):
        '''Return path to entity referenced by *entityReference*.'''
        entity = self.getEntityById(entityReference)

        if entity.get('entityType') == 'show':
            return entity.getName()
        else:
            parents = entity.getParents()
            parents = [parent for parent in reversed(parents)]
            entities = parents + [entity]
            pathSegments = []

            for entity in entities:
                if isinstance(entity, ftrack.Asset) and includeAssettype:
                    pathSegment = (
                        '{0}.{1}'.format(
                            self.getEntityName(entity.getEntityRef()),
                            entity.getType().getShort()
                        )
                    )
                else:
                    pathSegment = self.getEntityName(entity.getEntityRef())

                pathSegments.append(pathSegment)

            if unders:
                path = '_'.join(pathSegments)
            elif slash:
                path = ' / '.join(pathSegments)
            else:
                path = '.'.join(pathSegments)

            return path

    def getTaskTypeAndName(self, specification, entity=None, context=None):
        '''Return task type and name for *entity*.'''
        ## TODO: Is entity already a task?
        session = FnAssetAPI.SessionManager.currentSession()

        # Fallback default
        taskType = ftrack_connect_foundry.constant.COMPOSITING_TASK_TYPE

        # Host specific defaults
        host = session.getHost()
        hostId = host.getIdentifier()

        if hostId == 'uk.co.foundry.nuke':
            taskType = ftrack_connect_foundry.constant.COMPOSITING_TASK_TYPE

        elif hostId == 'uk.co.foundry.hiero':
            taskType = ftrack_connect_foundry.constant.EDIT_TASK_TYPE

        # Asset Type specific overrides

        # Several applications can make Nuke scripts, but they should all be
        # registered against 'comp' tasks for now.
        if specification.isOfType('file.nukescript'):
            taskType = ftrack_connect_foundry.constant.COMPOSITING_TASK_TYPE

        elif specification.isOfType('file.hrox'):
            taskType = ftrack_connect_foundry.constant.EDIT_TASK_TYPE

        # Check for locale override.
        if context and context.managerOptions:
            taskType = context.managerOptions.get(
                ftrack_connect_foundry.constant.TASK_TYPE_KEY, taskType
            )

        taskName = ftrack_connect_foundry.constant.TASK_TYPE_NAME_MAPPING.get(
            taskType, taskType
        )

        return taskType, taskName
