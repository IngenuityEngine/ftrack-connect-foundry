# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import FnAssetAPI.implementation

import ftrack_connect_foundry.bridge


class ManagerInterface(FnAssetAPI.implementation.ManagerInterfaceBase):
    '''FTrack manager interface.

    For the purpose of code reuse, most of the concrete implementation is
    provided by :py:class:`ftrack_connect_foundry.bridge.Bridge`.

    '''

    def __init__(self, bridge):
        '''Initialise interface with *_bridge*.

        *bridge* should be an instance of
        :py:class:`ftrack_connect_foundry.bridge.Bridge`.

        '''
        self._bridge = bridge
        super(ManagerInterface, self).__init__()

    def initialize(self):
        '''Prepare for interaction with the current host.'''
        return self._bridge.initialize()

    @classmethod
    def getIdentifier(cls):
        '''Return unique identifier.'''
        return ftrack_connect_foundry.bridge.Bridge.getIdentifier()

    def getDisplayName(self):
        '''Return human readable name.'''
        return ftrack_connect_foundry.bridge.Bridge.getDisplayName()

    def getInfo(self):
        '''Return dictionary of additional useful information.'''
        return self._bridge.getInfo()

    def managementPolicy(self, specification, context, entityRef=None):
        '''Return level of management this interface provides.'''
        return self._bridge.managementPolicy(
            specification, context, entityRef=entityRef
        )

    def flushCaches(self):
        '''Clear any internal caches.'''
        self._bridge.flushCaches()

    def isEntityReference(self, token, context):
        '''Return whether *token* appears to be an entity reference.

        The calling *context* is also supplied, though this may be None.

        '''
        return self._bridge.isEntityReference(token, context)

    def getDefaultEntityReference(self, specification, context):
        '''Return default entity_reference for *specification* and *context*.'''
        return self._bridge.getDefaultEntityReference(specification, context)

    def resolveEntityReference(self, entityRef, context):
        '''Resolve *entityRef* to a finalized string of data.'''
        return self._bridge.resolveEntityReference(entityRef, context)

    def containsEntityReference(self, string, context):
        '''Return whether *string* contains an entity reference.

        The calling *context* is also supplied, though this may be None.

        '''
        return self._bridge.containsEntityReference(string, context)

    def resolveInlineEntityReferences(self, string, context):
        '''Return copy of input *string* with all references resolved.'''
        return self._bridge.resolveInlineEntityReferences(string, context)

    def getRelatedReferences(self, entityRefs, specs, context, resultSpec=None):
        '''Return related entity references, based on specification.'''
        return self._bridge.getRelatedReferences(
            entityRefs, specs, context, resultSpec=resultSpec
        )

    def setRelatedReferences(self, entityRef, relationshipSpec, relatedRefs,
                             context, append=True):
        '''Create a new relationship between the referenced entities.'''
        return self._bridge.setRelatedReferences(
            entityRef, relationshipSpec, relatedRefs, context, append=append
        )

    def entityExists(self, entityRef, context):
        '''Return whether the entity referenced by *entityRef* exists.'''
        return self._bridge.entityExists(entityRef, context)

    def getEntityName(self, entityRef, context):
        '''Return entity name for *entityRef*.'''
        return self._bridge.getEntityName(entityRef, context)

    def getEntityDisplayName(self, entityRef, context):
        '''Return human readable name for entity referenced by *entityRef*.'''
        return self._bridge.getEntityDisplayName(entityRef, context)

    def getEntityVersionName(self, entityRef, context):
        '''Return version name for entity pointed to by *entityRef*.'''
        return self._bridge.getEntityVersionName(entityRef, context)

    def getEntityVersions(self, entityRef, context, includeMetaVersions=False,
                          maxResults=-1):
        '''Return mapping of version names to entity references.'''
        return self._bridge.getEntityVersions(
            entityRef, context, includeMetaVersions=includeMetaVersions,
            maxResults=maxResults
        )

    def getFinalizedEntityVersion(self, entityRef, context, version=None):
        '''Return concrete entity reference for supplied *entityRef*.'''
        return self._bridge.getFinalizedEntityVersion(
            entityRef, context, version=version
        )

    def getEntityMetadata(self, entityRef, context):
        '''Return metadata for entity referenced by *entityRef*.'''
        return self._bridge.getEntityMetadata(entityRef, context)

    def setEntityMetadata(self, entityRef, data, context, merge=True):
        '''Set metadata for entity referenced by *entityRef*.'''
        return self._bridge.setEntityMetadata(
            entityRef, data, context, merge=merge
        )

    def getEntityMetadataEntry(self, entityRef, key, context,
                               defaultValue=None):
        '''Return the value for the specified metadata *key*.'''
        return self._bridge.getEntityMetadataEntry(
            entityRef, key, context, defaultValue=defaultValue
        )

    def setEntityMetadataEntry(self, entityRef, key, value, context):
        '''Set metadata *key* to *value*.'''
        return self._bridge.setEntityMetadataEntry(
            entityRef, key, value, context
        )

    def preflight(self, targetEntityRef, entitySpec, context):
        '''Prepare for work to be done to the referenced entity.'''
        return self._bridge.preflight(targetEntityRef, entitySpec, context)

    def register(self, stringData, targetEntityRef, entitySpec, context):
        '''Register entity with asset management system (a publish).'''
        return self._bridge.register(
            stringData, targetEntityRef, entitySpec, context
        )

    def thumbnailSpecification(self, specification, context, options):
        '''Return whether a thumbnail should be prepared.'''
        return self._bridge.thumbnailSpecification(
            specification, context, options
        )
