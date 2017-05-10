# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from QtExt import QtCore, QtWidgets, QtGui

import hiero.ui

from hiero.exporters import FnNukeShotExporter
from hiero.exporters import FnAdditionalNodesDialog
from hiero.ui.FnUIProperty import UIPropertyFactory

import FnAssetAPI


class NukeShotExporterUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """UI for NukeShotExporter task."""
    hiero.ui.TaskUIBase.__init__(self, FnNukeShotExporter.NukeShotExporter, preset, "Nuke Project File")

    self._uiProperties = []
    self._tags = []

    self._collateTimeProperty = None
    self._collateNameProperty = None

  def initialise(self, preset, exportStructure):
    """When Parent ExportStructure is opened in the ui,
    initialise is called for each preset. Register any callbacks here"""
    paths = preset.properties()["readPaths"] + preset.properties()["writePaths"]
    for path in paths:
      element = exportStructure.childElement(path)

      if element is not None:
        element.addCallback(preset.pathChanged)


  def readPresetChanged (self, topLeft, bottomRight):
    hiero.core.log.debug( "readPresetChanged" )
    presetValue = self._preset.properties()["readPaths"] = []
    model = self._readModel
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())
        element = self._exportTemplate.childElement(item.text())
        if element is not None:
          element.addCallback(self._preset.pathChanged)


    if len(presetValue) > 0:
      if self._collateTimeProperty._widget.checkState() == QtCore.Qt.Checked or self._collateNameProperty._widget.checkState() == QtCore.Qt.Checked:
        QtWidgets.QMessageBox.information(hiero.ui.mainWindow(), "Conflicting Options", "Overriding the Read node paths will disable the 'Collate' options. Currently these features are incompatible.")
        self._collateTimeProperty._widget.setChecked(False)
        self._collateNameProperty._widget.setChecked(False)

    self._collateTimeProperty.setEnabled(len(presetValue) == 0)
    self._collateNameProperty.setEnabled(len(presetValue) == 0)

    hiero.core.log.debug( "readPaths (%s)" % str(presetValue) )

  def writePresetChanged (self, topLeft, bottomRight):
    hiero.core.log.debug( "writePresetChanged" )
    presetValue = self._preset.properties()["writePaths"] = []

    model = self._writeModel
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())
        element = self._exportTemplate.childElement(item.text())
        if element is not None:
          element.addCallback(self._preset.pathChanged)

    hiero.core.log.debug( "writePaths (%s)" % str(presetValue) )

  def populateUI (self, widget, exportTemplate):
    if exportTemplate:

      self._exportTemplate = exportTemplate

      properties = self._preset.properties()

      layout = QtWidgets.QFormLayout()

      self._readList = QtWidgets.QListView()
      self._writeList = QtWidgets.QListView()

      self._readList.setMinimumHeight(50)
      self._writeList.setMinimumHeight(50)
      self._readList.resize(200,50)
      self._writeList.resize(200,50)


      self._readModel = QtWidgets.QStandardItemModel()
      self._writeModel = QtWidgets.QStandardItemModel()

      # Default to the empty item unless the preset has a value set.
      for model, presetValue in ((self._readModel, properties["readPaths"]), (self._writeModel, properties["writePaths"])):
        for path, preset in exportTemplate.flatten():

          if model is self._writeModel:
            if not hasattr(preset._parentType, 'nukeWriteNode'):
              continue

          item = QtWidgets.QStandardItem(path)
          item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

          item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
          if path in presetValue:
            item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

          model.appendRow(item)

      self._readList.setModel(self._readModel)
      self._writeList.setModel(self._writeModel)

      readNodeListToolTip = """Select multiple entries within the shot template to be used as inputs for the read nodes (i.e. symlink, transcode.. etc).\n No selection will mean that read nodes are created in the nuke script pointing directly at the source media.\n"""
      writeNodeListToolTip = """Add one or more "Nuke Write Node" tasks to your export structure to define the path and codec settings for the nuke script.\nIf no write paths are selected, no write node will be added to the nuke script."""

      self._readList.setToolTip(readNodeListToolTip)
      self._writeList.setToolTip(writeNodeListToolTip)
      self._readModel.dataChanged.connect(self.readPresetChanged)

      publishScriptTip = """When enabled, if there is a known shot in the asset that matches the shot in Hiero, the Nuke script will be published there."""
      key, value, label = "publishScript", True, FnAssetAPI.l("{publish} Script")
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label, tooltip=publishScriptTip)
      self._uiProperties.append(uiProperty)
      layout.addRow(uiProperty._label + ":", uiProperty)

      ## @todo Think of a better name
      useAssetsTip = """If enabled, any Clips that point to managed Assets will reference the Asset, rather than their files."""
      key, value, label = "useAssets", True, "Use Assets"
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label, tooltip=useAssetsTip)
      self._uiProperties.append(uiProperty)
      layout.addRow(uiProperty._label + ":", uiProperty)

      layout.addRow("Read Nodes:", self._readList)
      self._writeModel.dataChanged.connect(self.writePresetChanged)
      layout.addRow("Write Nodes:", self._writeList)


      retimeToolTip = """Sets the retime method used if retimes are enabled.\n-Motion - Motion Estimation.\n-Blend - Frame Blending.\n-Frame - Nearest Frame"""
      key, value = "method", ("None", "Motion", "Frame", "Blend")
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label="Retime Method", tooltip=retimeToolTip)
      self._uiProperties.append(uiProperty)
      layout.addRow(uiProperty._label + ":", uiProperty)


      collateTracksToolTip = """Enable this to include other shots which overlap the sequence time of each shot within the script. Cannot be enabled when Read Node overrides are set."""

      key, value, label = "collateTracks", False, "Collate Shot Timings"
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateTracksToolTip)
      layout.addRow(label+":", uiProperty)
      self._uiProperties.append(uiProperty)
      self._collateTimeProperty = uiProperty

      collateShotNameToolTip = """Enable this to include other shots which have the same name in the Nuke script. Cannot be enabled when Read Node overrides are set."""
      key, value, label = "collateShotNames", False, "Collate Shot Name"
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateShotNameToolTip)
      layout.addRow(label+":", uiProperty)
      self._collateNameProperty = uiProperty
      self._uiProperties.append(uiProperty)
      self.readPresetChanged(None, None)

      additionalNodesToolTip = """When enabled, allows custom Nuke nodes to be added into Nuke Scripts.\n Click Edit to add nodes on a per Shot, Track or Sequence basis.\n Additional Nodes can also optionally be filtered by Tag."""

      additionalNodesLayout = QtWidgets.QHBoxLayout()
      additionalNodesCheckbox = QtWidgets.QCheckBox()
      additionalNodesCheckbox.setToolTip(additionalNodesToolTip)
      additionalNodesCheckbox.stateChanged.connect(self._additionalNodesEnableClicked)
      if self._preset.properties()["additionalNodesEnabled"]:
        additionalNodesCheckbox.setCheckState(QtCore.Qt.Checked)
      additionalNodesButton = QtWidgets.QPushButton("Edit")
      additionalNodesButton.setToolTip(additionalNodesToolTip)
      additionalNodesButton.clicked.connect(self._additionalNodesEditClicked)
      additionalNodesLayout.addWidget(additionalNodesCheckbox)
      additionalNodesLayout.addWidget(additionalNodesButton)
      layout.addRow("Additional Nodes:", additionalNodesLayout)

      widget.setLayout(layout)


  def _additionalNodesEnableClicked(self, state):
    self._preset.properties()["additionalNodesEnabled"] = state == QtCore.Qt.Checked
    pass

  def _additionalNodesEditClicked(self):
    dialog = FnAdditionalNodesDialog.AdditionalNodesDialog(self._preset.properties()["additionalNodesData"], self._tags)
    if dialog.exec_():
      self._preset.properties()["additionalNodesData"] = dialog.data()
    pass


  def setTags ( self, tags ):
    """setTags passes the subset of tags associated with the selection for export"""
    self._tags = tags


