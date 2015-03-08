from .. import logging
from .. import exceptions


__all__ = ['PluginManager']


class PluginManager(object):
  """

  Loads Python Packages on a custom search path. If they manager a top-level
  'plugin' attribute, that holds a class derived from PluginManagerPlugin,
  it will be registered with its identifier.
  Once a plug-in has registered an identifier, any subsequent registrations
  with that id will be skipped.

  """

  __instance = None

  @classmethod
  def instance(cls):
    if not cls.__instance:
      cls.__instance = PluginManager()
    return cls.__instance


  def __init__(self):
    self.__map = {}
    self.__paths = {}


  def scan(self, paths):
    import os
    import os.path
    import imp
    import hashlib

    logging.log("PluginManager: Looking for packages on: %s" % paths, logging.kDebug)

    for path in paths.split(os.pathsep):

      if not os.path.isdir(path):
        logging.log(("PluginManager: Omitting '%s' from plug-in search as its not a "+\
            "directory") % path, logging.kDebug)

      for bundle in os.listdir(path):

        bundlePath = os.path.join(path, bundle)
        if not os.path.isdir(bundlePath):
          logging.log(("PluginManager: Omitting '%s' as its not a package "+\
            "directory") % path, logging.kDebug)
          continue

        # Make a unique namespace to ensure the plugin identifier is all that
        # really matters
        moduleName = hashlib.md5(bundlePath).hexdigest()

        try:

          module = imp.load_module(moduleName, None, bundlePath, ("","",imp.PKG_DIRECTORY))
          if hasattr(module, 'plugin'):
            self.register(module.plugin, bundlePath)

        except Exception, e:
          msg = "PluginManager: Caught exception loading plug-in from '%s':\n%s" % (bundlePath, e)
          logging.log(msg, logging.kError)


  def identifiers(self):
    return self.__map.keys()


  def getPlugin(self, identifier):

    if identifier not in self.__map:
      msg = "PluginManager: No plug-in registered with the identifier '%s'" % identifier
      raise exceptions.PluginError(msg)

    return self.__map[identifier]


  def register(self, cls, path="<unknown>"):

    identifier = cls.getIdentifier()
    if identifier in self.__map:
      msg = "PluginManager: Skipping class '%s' defined in '%s'. Already registered by '%s'" \
          % (cls, path, self.__paths[identifier] )
      logging.log(msg, logging.kDebug)
      return

    msg = "PluginManager: Registered plug-in '%s' from '%s'" % (cls, path)
    logging.log(msg, logging.kDebug)

    self.__map[identifier] = cls
    self.__paths[identifier] = path





