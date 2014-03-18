from .Specification import Specification, TypedProperty


__all__ = ['ParameterSpecification']


class ParameterSpecification(Specification):
  """

  The ParameterSpecification is a base class to define speficications that
  relate to a Parameter in a Host. These will be made available to the @ref
  ManagerUIDelegate to allow customisation of widgets (such as the @ref
  python.ui.widgets.ParameterDelegate) as neccesary.

  """
  _prefix = "core.parameter"



