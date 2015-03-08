from .Specification import Specification, TypedProperty

__all__ = ['CommandSpecification']


class CommandSpecification(Specification):
  """

  CommandSpecifications are used to define commands that may be executed
  thought the API's command mechanism. Not all Hosts or Managers may support a
  particular command.

  \see python.implementation.ManagerInterfaceBase.ManagerInterfaceBase.commandSupported
  \see python.implementation.ManagerInterfaceBase.ManagerInterfaceBase.commandAvailable
  \see python.implementation.ManagerInterfaceBase.ManagerInterfaceBase.runCommand

  \see python.Host.Host.commandSupported
  \see python.Host.Host.commandAvailable
  \see python.Host.Host.runCommand

  """
  _prefix = "core.command"

