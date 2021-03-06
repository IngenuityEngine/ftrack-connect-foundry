from ..core import PluginManagerPlugin
from .ManagerInterfaceBase import ManagerInterfaceBase


__all__ = ['ManagerPlugin']


class ManagerPlugin(PluginManagerPlugin):
  """

  This class represents the various derived classes that make up the binding to
  a @ref asset_management_system.

  It used by the dynamic plug-in discovery mechanism (@ref
  python.PluginManager) to instantiate the main classes in an implementation.

  The class will never be instantiated itself, so all functionality is via
  class methods.

  In order to register a new asset management system, simply place a python
  package on the appropriate search path, that has a top-level attribute called
  'plugin', that holds a class derived from this.

  @warning This class, may be used in a batch, or UI session, so consequently,
  it is imperative that no ui libraries (QtCore, QtGui etc...) are imported
  unless @ref getUIDelegate() is called, and ideally, even then, this should be
  deferred until something is requested from the @ref
  python.ui.implementation.ManagerUIDelegate.

  """


  @classmethod
  def getIdentifier(cls):
    """

    Returns an identifier to uniquely identify the plug-in.
    Generally, this should be the identifier used by the manager.
    The identifier should use only alpha-numeric characters and '.', '_' or '-'.
    For example:

        "uk.co.foundry.asset.testManager"

    @return str

    @see python.implementation.ManagerInterfaceBase

    """
    raise NotImplementedError


  @classmethod
  def getInterface(cls):
    """

    Constructs an instance of the @ref python.implementation.ManagerInterfaceBase.

    This is an instance of some class derived from ManagerInterfaceBase to be
    bound to the Host-facing @ref python.Manager and @ref python.Entity
    objects.

    Generally this is only directly called by the @ref python.ManagerFactory.
    It may be called multiple times in a session, but there as the
    ManagerInterfaceBase API itself is specified as being stateless (aside from
    any internal caching/etc...) then there is no pre-requisite to always
    return a new instance.

    @return ManagerInterfaceBase instance

    """
    return ManagerInterfaceBase()


  @classmethod
  def getUIDelegate(cls, interfaceInstance):
    """

    Constructs an instance of the @ref
    python.ui.implementation.ManagerUIDelegate

    This is an instance of some class derived from ManagerUIDelegate that is
    used by the @ref UISessionManager to provide widgets to a host that may
    bind into panels in the application, or to allow the application to
    delegate asset browsing/picking etc...

    @param interfaceInstance An instance of the plugins interface as returned
    by @ref getInterface(), this is to allow UI to be configured in relation to
    a specific instantiation, which may perhaps target a different endpoint due
    to its settings, etc...

    @note It is safe to import any UI toolkits, etc... *within in this call*,
    but generally you may want to deffer this to methods in the delegate.

    @return An instance of some class derived from @ref ManagerUIDelegate.

    """
    return None

