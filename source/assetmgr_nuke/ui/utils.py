from FnAssetAPI.ui.toolkit import QtCore, QtGui, QtWidgets

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

  msgBox = QtWidgets.QMessageBox()
  msgBox.setText(l("Save changes before closing script?"))
  msgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard
      | QtWidgets.QMessageBox.Cancel)

  button = msgBox.exec_()

  if button == QtWidgets.QMessageBox.Save:
    return 'save'
  elif button == QtWidgets.QMessageBox.Discard:
    return 'dontsave'
  else:
    return 'cancel'


