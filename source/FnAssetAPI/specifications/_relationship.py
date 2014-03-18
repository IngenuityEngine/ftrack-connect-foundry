from .Specification import Specification, TypedProperty


__all__ = ['RelationshipSpecification', 'ParentGroupingRelationship',
  'WorkflowRelationship']


class RelationshipSpecification(Specification):
  """

  RelationshipSpecifications are used mainly with \ref
  python.implementation.ManagerInterfaceBase.ManagerInterfaceBase.getRelatedReferences
  "ManagerInterface.getRelatedReferences", in order to describe the kind of
  relation that is being requested, when a simply EntitySpecification will not
  suffice.

  """
  _prefix = "core.relationship"


class ParentGroupingRelationship(RelationshipSpecification):
  """

  This relationship can be used to query the organisational parent of any given
  entity. If called with an asset, or a version, etc.. it should give the Shot,
  Sequence or other part of the hierarchy under which the Entity resides. If
  called with some other group entity, then it should return the logical parent
  of that group. For example, a Shot may return a Sequence, etc...

  This is essential to allow cross-discipline publishing to take place. For
  example, to determine the Shot that an asset resides under, so that a
  different kind of asset can be published to the same place.

  If you're asset system adds intermediate sub-groups underneath something
  logically analgous to a 'Shot', (for example a 'compositing task', etc..)
  then this should not be considered when determining the 'parent'.
  Alternatively, if you do consider it, you may need additional logic in
  'register' to verify the target task is suitable for the published asset.

  An example being an ImageSpecification asset published under an 'editorial'
  task type, under a Shot, may use this query to find the shot that a Nuke
  Script should be published too to perform 'comp work' for the Shot.

  """
  _type = "grouping.parent"



## @todo think of a better name
class WorkflowRelationship(RelationshipSpecification):
  """

  A workflow relationship is used to build tracks of related media, etc... in
  timeline contexts. The relationship is defined by a criteria string, (usually
  supplied by a Manager UI element), that describes the relationship. For
  example, it might be 'latest approved comps, by Bob'.

  """

  _type = "workflow"

  criteria = TypedProperty(str, doc="A description of the relationship that "
      +"makes sense to the manager. This is generally derived from the "
      +"manager itself, so could be any serialised/understood string.")

