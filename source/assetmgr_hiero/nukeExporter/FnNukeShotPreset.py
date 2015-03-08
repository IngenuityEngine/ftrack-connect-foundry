import hiero.core

from FnNukeShotExporter import NukeShotExporter

class NukeShotPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    """Initialise presets to default values"""
    hiero.core.TaskPresetBase.__init__(self, NukeShotExporter, name)

    # Set any preset defaults here
    self.properties()["readPaths"] = []
    self.properties()["writePaths"] = []
    self.properties()["collateTracks"] = False
    self.properties()["collateShotNames"] = False

    # Asset properties
    self.properties()["useAssets"] = True
    self.properties()["publishScript"] = True

    # Not exposed in UI
    self.properties()["collateSequence"] = False    # Collate all trackitems within sequence
    self.properties()["collateCustomStart"] = True  # Start frame is inclusive of handles

    self.properties()["additionalNodesEnabled"] = False
    self.properties()["additionalNodesData"] = []
    self.properties()["method"] = "Blend"

    # Update preset with loaded data
    self.properties().update(properties)

  def addCustomResolveEntries(self, resolver):
    resolver.addResolver("{ext}", "Extension of the file to be output", "nk")

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kAllItems

  def pathChanged(self, oldPath, newPath):
    for pathlist in (self.properties()["readPaths"], self.properties()["writePaths"]):
      for path in pathlist:
        if path == oldPath:
          pathlist.remove(oldPath)
          pathlist.append(newPath)


