from PySide import QtGui

import FnAssetAPI

__all__ = ['_script_version_all_up', 'confirmClose']


def _script_version_all_up():
  import nuke
  import nukescripts
  for n in nuke.allNodes( 'Write' ):
    n['selected'].setValue ( True )
  nukescripts.version_up()
  nukescripts.script_version_up()
  for n in nuke.allNodes():
    n['selected'].setValue( False )


def confirmClose():

  l = FnAssetAPI.l

  msgBox = QtGui.QMessageBox()
  msgBox.setText(l("Save changes before closing script?"))
  msgBox.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard
      | QtGui.QMessageBox.Cancel)

  button = msgBox.exec_()

  if button == QtGui.QMessageBox.Save:
    return 'save'
  elif button == QtGui.QMessageBox.Discard:
    return 'dontsave'
  else:
    return 'cancel'


