from QtExt import QtGui, QtWidgets, QtCore

import FnAssetAPI
import FnAssetAPI.ui
from FnAssetAPI.ui.widgets import ItemSpreadsheetWidget

## @todo Implement setOptions

class ItemCreateDialog(QtGui.QDialog):

  def __init__(self, specification, context, embedBrowser=False, session=None,
      parent=None, embedDetails=True):
    super(ItemCreateDialog, self).__init__(parent=parent)

    l = FnAssetAPI.l

    self._specification = specification
    self._context = context

    if not session:
      session = FnAssetAPI.SessionManager.currentSession()
    self._session = session

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    self.itemCreateWidget = ItemCreateWidget(specification, context,
        embedBrowser=embedBrowser, embedDetails=embedDetails, session=session)
    layout.addWidget(self.itemCreateWidget)

    self._managerOptions = None
    self._drawOptions(layout)

    buttons = QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
    self._buttons = QtGui.QDialogButtonBox(buttons)

    if not embedDetails:
      detailsButton = self._buttons.addButton("Details...",
          QtGui.QDialogButtonBox.HelpRole)
      detailsButton.clicked.connect(self.showDetails)

    self._buttons.button(QtGui.QDialogButtonBox.Ok).setText(l('{publish}'))

    self.connect(self._buttons, QtCore.SIGNAL('accepted()'), self.accept)
    self.connect(self._buttons, QtCore.SIGNAL('rejected()'), self.reject)

    layout.addWidget(self._buttons)


  def setItems(self, items):
    self.itemCreateWidget.setItems(items)

  def getItems(self):
    return self.itemCreateWidget.getItems()


  def setTargetEntityRefrence(self, ref):
    return self.itemCreateWidget.setTargetEntityRefrence(ref)

  def getTargetEntityReference(self):
    return self.itemCreateWidget.getTargetEntityReference()


  def setTitle(self, title):
    self.setWindowTitle(FnAssetAPI.l(title))


  def setGroupTitle(self, title):
    self.itemCreateWidget.setGroupTitle(FnAssetAPI.l(title))
    self._itemDetailsTitle = title


  def setCreateButtonTitle(self, title):
    self._buttons.button(QtGui.QDialogButtonBox.Ok).setTitle(FnAssetAPI.l(title))


  def getOptions(self):

    options = {}

    managerOptions = {}
    if self._managerOptions:
      managerOptions = self._managerOptions.getOptions()
    options['managerOptions'] = managerOptions

    return options

  def setOptions(self, options):

    if self._managerOptions:
      managerOptions = options.get('managerOptions', {})
      self._managerOptions.setOptions(managerOptions)


  def showDetails(self):

    detailsDialog = ItemDetailsDialog(parent=self)
    detailsDialog.setItems(self.getItems())
    detailsDialog.setWindowTitle(self._itemDetailsTitle)
    detailsDialog.exec_()


  def sizeHint(self):
    return QtCore.QSize(700, 550)


  def _drawOptions(self, layout):

    optionsBox = QtGui.QGroupBox("Options")
    optionsLayout = QtGui.QVBoxLayout()
    optionsBox.setLayout(optionsLayout)
    layout.addWidget(optionsBox)

    # See if we have any options from the manager

    self._managerOptions = self._session.getManagerWidget(
        FnAssetAPI.ui.constants.kRegistrationManagerOptionsWidgetId,
        throw=False, args=(self._specification, self._context))

    if self._managerOptions:
      optionsLayout.addWidget(self._managerOptions)
      optionsLayout.addSpacing(10)

    return optionsLayout


class ItemDetailsDialog(QtGui.QDialog):

  def __init__(self, parent=None):
    super(ItemDetailsDialog, self).__init__(parent=parent)

    self.setWindowTitle("Item Details")

    self.__items = []

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    self.itemSpreadsheet = ItemSpreadsheetWidget()
    self.itemSpreadsheet.setMaxColumnWidth(800)

    layout.addWidget(self.itemSpreadsheet)

    self._buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
    layout.addWidget(self._buttons)

    self.connect(self._buttons, QtCore.SIGNAL('accepted()'), self.accept)
    self.connect(self._buttons, QtCore.SIGNAL('rejected()'), self.reject)

  def setItems(self, items):
    self.__items = items
    self.itemSpreadsheet.setItems(items)

  def getItems(self):
    return self.__items

  def sizeHint(self):
    return QtCore.QSize(700,500)



class ItemCreateWidget(QtGui.QWidget):

  def __init__(self, specification, context, parent=None, embedBrowser=False,
      embedDetails=True ,session=None):
    super(ItemCreateWidget, self).__init__(parent=parent)

    l = FnAssetAPI.l

    self._embedBrowser = embedBrowser
    self._embedDetails = embedDetails

    layout = QtGui.QVBoxLayout()
    self.setLayout(layout)

    if not session:
      session = FnAssetAPI.ui.UISessionManager.currentSession()

    if embedBrowser:
      widgetIdentifier = FnAssetAPI.ui.constants.kBrowserWidgetId
    else:
      widgetIdentifier = FnAssetAPI.ui.constants.kInlinePickerWidgetId

    pickerCls = session.getManagerWidget(widgetIdentifier, instantiate=False)
    self.parentPicker = pickerCls(specification, context)

    if embedDetails:
      destGbox = QtGui.QGroupBox(l("{publish} To"))
      layout.addWidget(destGbox)
      destLayout = QtGui.QVBoxLayout()
      destGbox.setLayout(destLayout)
      destLayout.addWidget(self.parentPicker)
    else:
      layout.addWidget(self.parentPicker)

    self.itemSpreadsheet = None

    if embedDetails:
      self.itemSpreadsheet = ItemSpreadsheetWidget()
      self.itemsGbox = QtGui.QGroupBox("Items")
      itemsLayout = QtGui.QVBoxLayout()
      self.itemsGbox.setLayout(itemsLayout)
      itemsLayout.addWidget(self.itemSpreadsheet)
      layout.addWidget(self.itemsGbox)

    self.__items= []


  def setGroupTitle(self, title):
    if self.itemSpreadsheet:
      self.itemsGbox.setTitle("Items")
    self._itemDetailsTitle = title

  def getGroupTitle(self):
    return self._itemDetailsTitle


  def setItems(self, items):
    self.__items = items
    if self.itemSpreadsheet:
      self.itemSpreadsheet.setItems(self.__items)
      self.itemSpreadsheet.hideEmptyColumns()

  def getItems(self):
    return self.__items


  def setTargetEntityRefrence(self, ref):
    self.parentPicker.setSelectionSingle(ref)

  def getTargetEntityReference(self):
    return self.parentPicker.getSelectionSingle()

  def sizeHint(self):
    return QtCore.QSize(400,300)




class ClipPublishDialog(ItemCreateDialog):

  def __init__(self, specification, context, session=None, parent=None):
    super(ClipPublishDialog, self).__init__(specification, context,
        embedBrowser=True, session=session, parent=parent, embedDetails=False)

    self.setTitle("{publish} Clips to {manager}")
    self.setGroupTitle("Clips")


  def _drawOptions(self, layout):

    l = FnAssetAPI.l

    optionsLayout = super(ClipPublishDialog, self)._drawOptions(layout)

    self._replaceMediaSource = QtGui.QCheckBox(
        l("Link Clips with {published} {assets}"))
    self._replaceMediaSource.setChecked(True)
    optionsLayout.addWidget(self._replaceMediaSource)

    self._ignorePublished = QtGui.QCheckBox(
        l("Ignore Clips that are already {published}"))
    self._ignorePublished.setChecked(True)
    optionsLayout.addWidget(self._ignorePublished)
    self._ignorePublished.toggled.connect(self._optionsChanged)


  def getOptions(self):

    opts = super(ClipPublishDialog, self).getOptions()

    opts['usePublishedClips'] = self._replaceMediaSource.isChecked()
    opts['ignorePublishedClips'] = self._ignorePublished.isChecked()

    return opts


  def setOptions(self, options):

    super(ClipPublishDialog, self).setOptions(options)

    replace = options.get('usePublishedClips', None)
    if replace is not None:
      self._replaceMediaSource.setChecked(replace)

    ignore = options.get('ignorePublishedClips', None)
    if ignore is not None:
      self._ignorePublished.setChecked(ignore)


  def setItems(self, items):

    self.__origItems = items

    # As our options are quite simple at the moment, we can just do this on the
    # way in
    if self._ignorePublished.isChecked():
      actionableItems = filter(lambda i: not i.getEntity(), self.__origItems)
    else:
      actionableItems = items

    super(ClipPublishDialog, self).setItems(actionableItems)

    enabled = bool(self.getItems())
    self._buttons.button(QtGui.QDialogButtonBox.Ok).setEnabled(enabled)


  def _optionsChanged(self):
    # re-set the items, which will re-apply the options
    self.setItems(self.__origItems)




