import os
from . import logging
from .core import PluginManager
from .Manager import Manager


__all__ = ['ManagerFactory',]



class ManagerFactory(object):
  """

  A Factory to manage @ref python.implementation.ManagerPlugin derived plugins
  and instantiation of Manager and UIDelegate instances. Not usually used
  directly by a @ref Host, which instead uses the @ref python.SessionManager

  @envvar **FOUNDRY_ASSET_PLUGIN_PATH** *str* A PATH-style list of directories to
  search for @ref python.implementation.ManagerPlugin based plugins. It uses
  the platform-native delimiter.  Searched left to right.

  """

  ## The Environment Variable to read the plug-in search path from
  kPluginEnvVar = "FOUNDRY_ASSET_PLUGIN_PATH"

  __instance = None

  @classmethod
  def instance(cls):
    """

    @return ManagerFactory, returns a lazily-constructed singleton instance of
    the ManagerFactory.

    """
    if not cls.__instance:
      cls.__instance = ManagerFactory()
    return cls.__instance

  def __init__(self):
    super(ManagerFactory, self).__init__()

    self.__pluginManager = None
    self.__instances = {}
    self.__delegates = {}


  def scan(self, paths=None):
    """

    Scans for ManagerPlugins, and registers them with the factory instance.

    @param paths str, A searchpath string to search for plug-ins. If None, then
    the contents of the Environment Variable @ref kPluginEnvVar is used instead.

    """

    if not paths:
      paths = os.environ.get(self.kPluginEnvVar, "")
      if not paths:
        logging.warning(("%s is not set. Its somewhat unlikely that you will "
          +"find any plugins...") % self.kPluginEnvVar)


    if not self.__pluginManager:
      self.__pluginManager = PluginManager.instance()

    # We do this after instantiating, so that the lifetime of the manager is
    # consistent with cases where some paths were set.
    if not paths:
      return

    self.__pluginManager.scan(paths)


  def identifiers(self):
    """

    @return list, all identifiers known to the factory.
    @see python.implementation.ManagerPlugin

    """
    if not self.__pluginManager:
      return []

    return self.__pluginManager.identifiers()


  def managers(self):
    """

    @return dict, Keyed by identifiers, each value is a dict containing
    information about the Manager provided by the plugin. This dict has the
    following keys:
      @li **name** The display name of the Manager suitable for UI use.
      @li **identifier** It's identifier
      @li **info** The info dict from the Manager (see: @ref
      python.implementation.ManagerInterfaceBase.getInfo
      "ManagerInterfaceBase.getInfo()")
      @li **plugin** The plugin class that represents the Manager (see: @ref
      python.implementation.ManagerPlugin)

    """

    if not self.__pluginManager:
      return {}

    managers = {}

    identifiers = self.__pluginManager.identifiers()
    for i in identifiers:

      try:
        p = self.__pluginManager.getPlugin(i)
        interface = p.getInterface()
      except Exception as e:
        logging.critical("Error loading plugin for '%s': %s" % (i, e))
        continue

      managerIdentifier = interface.getIdentifier()
      managers[i] = {
          'name' : interface.getDisplayName(),
          'identifier' : managerIdentifier,
          'info' : interface.getInfo(),
          'plugin' : p
      }

      if i != managerIdentifier:
        msg = ("Manager '%s' is not registered with the same identifier as "+\
          "it's plugin ('%s' instead of '%s')") % (interface.getDisplayName(),
        managerIdentifier, i)
        logging.log(msg, logging.kWarning)

    return managers


  def managerRegistered(self, identifier):
    """

    @return bool, True if the supplied identifier is known to the factory.

    """
    return identifier in self.__pluginManager.identifiers()


  def instantiate(self, identifier, cache=True):
    """

    Creates an instance of the @ref ManagerInterfaceBase with the specified
    identifier, and wraps it as a @ref Manager.

    @param cache bool, When True the created instance will be cached, and
    immediately returned by subsequence calls to this function with the same
    identifier - instead of creating a new instance. If False, a new instance
    will be created each, and never retained.

    """

    if not self.__pluginManager:
      raise RuntimeError, "No plugins have been scanned for"

    if cache and identifier in self.__instances:
      return self.__instances[identifier]

    plugin = self.__pluginManager.getPlugin(identifier)
    interface = plugin.getInterface()
    manager = Manager(interface)

    if cache:
      self.__instances[identifier] = manager

    return manager


  def instantiateUIDelegate(self, managerInterfaceInstance, cache=True):
    """

    Creates an instance of the @ref ManagerUIDelegate for the specified
    identifier.

    @param the instance of a ManagerInterface to retrieve the UI delegate for.

    @param cache bool, When True the created instance will be cached, and
    immediately returned by subsequence calls to this function with the same
    identifier - instead of creating a new instance. If False, a new instance
    will be created each, and never retained.

    """

    if not self.__pluginManager:
      raise RuntimeError, "No plugins have been scanned for"

    ## @todo This probably has some retention issues we need to deal with
    if cache and managerInterfaceInstance in self.__delegates:
      return self.__delegates[managerInterfaceInstance]

    identifier = managerInterfaceInstance.getIdentifier()
    plugin = self.__pluginManager.getPlugin(identifier)
    delegateInstance = plugin.getUIDelegate(managerInterfaceInstance)

    if cache:
      self.__delegates[managerInterfaceInstance] = delegateInstance

    return delegateInstance











