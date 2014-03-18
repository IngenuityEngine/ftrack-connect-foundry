from FnNukeShotExporter import NukeShotExporter
from FnNukeShotExporterUI import NukeShotExporterUI
from FnNukeShotPreset import NukeShotPreset

# Overwrite existing functions
import FnNukeHelpers

from hiero.exporters.FnExternalRender import NukeRenderPreset
from hiero.exporters.FnShotProcessor import ShotProcessorPreset

def register():

  import hiero.core
  import hiero.ui

  hiero.core.log.debug( "Registering Assetised NukeShotExporter" )
  hiero.core.taskRegistry.registerTask(NukeShotPreset, NukeShotExporter)
  hiero.ui.taskUIRegistry.registerTaskUI(NukeShotPreset, NukeShotExporterUI)

  shottemplate = (("{shot}", None),
                  ("{shot}/nuke/script/{shot}_comp_{version}.nk", NukeShotPreset( "",  {'readPaths': [], 'writePaths': ['{shot}/nuke/renders/{shot}_comp_{version}.####.{ext}']	} ) ),
                  ("{shot}/nuke/renders/{shot}_comp_{version}.####.{ext}", NukeRenderPreset( "", {'file_type' : 'dpx', 'dpx' : {'datatype' : '10 bit'}} ) ) )

  name = "Assetised Nuke Shot"
  preset = ShotProcessorPreset( name,
      { "exportTemplate" : shottemplate, "cutLength" : True })

  registry = hiero.core.taskRegistry

  existing = [p.name() for p in registry.localPresets()]
  if name in existing:
    registry.removeProcessorPreset(name)

  registry.addProcessorPreset(name, preset)

