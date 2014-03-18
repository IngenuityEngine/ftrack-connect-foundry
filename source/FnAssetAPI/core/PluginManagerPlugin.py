
class PluginManagerPlugin(object):

  @classmethod
  def getIdentifier(cls):
    """

    This method is required by all plugins, in order to uniquely identify this
    plugin. If there are duplicate plugins with the same identifier, the first
    one encountered will be used, and all others will be ignored.

    """
    raise NotImplementedError



