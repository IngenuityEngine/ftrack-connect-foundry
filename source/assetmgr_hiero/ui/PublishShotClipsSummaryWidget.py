from QtExt import QtGui, QtWidgets, QtCore
import FnAssetAPI

from .. import utils as cmdUtils
from .. import items

__all__ = ['PublishShotClipsSummaryWidget']


class PublishShotClipsSummaryWidget(QtGui.QTreeWidget):

  def __init__(self, context=None, parent=None):
    super(PublishShotClipsSummaryWidget, self).__init__(parent=parent)

    self.__shotItems = []
    self.__options = {}
    self.__context = context

    self._setupTree()


  def setShotItems(self, shotItems):
    self.__shotItems = shotItems

  def getShotItems(self):
    return self.__shotItems


  def setOptions(self, options):
    self.__options = options

  def getOptions(self):
    return self.__options


  def refresh(self):

    session = FnAssetAPI.SessionManager.currentSession()
    if not self.__context:
      self.__context = session.createContext()

    self.clear()

    shotParentRef = self.__options.get('targetEntityRef', None)
    sharedParentRef = self.__options.get('sharedClipTargetEntityRef', None)

    with self.__context.scopedOverride():

      self.__context.access = self.__context.kRead

      shotParentEntity = None
      if shotParentRef:
        shotParentEntity = session.getEntity(shotParentRef, self.__context,
            mustExist=True, throw=False)

      sharedParentEntity = None
      if sharedParentRef:
        sharedParentEntity = session.getEntity(sharedParentRef, self.__context,
            mustExist=True, throw=False)

      if shotParentEntity:
        shotTreeItems = self._buildClipsTree(self.__shotItems,
            shotParentEntity, sharedParentEntity, self.__context)
        for s in shotTreeItems:
          self.addTopLevelItem(s)
          self._expandAll(s)

        self._tidyColumns()


  def _setupTree(self):
    self.setHeaderLabels(("Name", "Kind", "", "Action", "Original Clip"))
    self.setUniformRowHeights(True)
    self.setAlternatingRowColors(True)

  def _tidyColumns(self):

    numColumns = self.header().count()

    for i in range(numColumns):
      self.resizeColumnToContents(i)
      # This always makes them a bit tight
      self.setColumnWidth(i, self.columnWidth(i)+10)


  def _buildClipsTree(self, shotItems, parentEntity, sharedParentEntity, context):

    tickIcon = QtGui.QIcon("icons:TagGood.png")
    crossIcon = QtGui.QIcon("icons:status/TagBad.png")
    blockIcon = QtGui.QIcon("icons:status/TagOnHold.png")
    addIcon = QtGui.QIcon("icons:Add.png")

    l = FnAssetAPI.l

    shotParentTreeItem = GroupingTreeItem()
    shotParentTreeItem.setSizeHint(0, QtCore.QSize(300, 22))
    shotParentTreeItem.setSizeHint(1, QtCore.QSize(120, 22))
    shotParentTreeItem.setSizeHint(4, QtCore.QSize(120, 22))
    shotParentTreeItem.setEntity(parentEntity, context)

    boldFont = shotParentTreeItem.font(0)
    boldFont.setBold(True)
    italicFont = shotParentTreeItem.font(0)
    italicFont.setItalic(True)

    shotParentTreeItem.setFont(0, boldFont)

    newShots, existingShots, unused = cmdUtils.shot.analyzeHieroShotItems(
      shotItems, parentEntity, context, checkForConflicts=False)

    clips, sharedClips = cmdUtils.shot.analyzeHeiroShotItemClips(
      shotItems, asItems=False)

    ignorePublished = self.__options.get('ignorePublishedClips', True)
    publishShared = self.__options.get('publishSharedClips', False)
    customName = ''
    if self.__options.get('clipsUseCustomName', False):
      customName = self.__options.get('customClipName', '')


    processsedSharedClips = set()

    allSharedClips = []

    for s in shotItems:

      shotTreeItem = GroupingTreeItem()
      shotTreeItem.setItem(s)
      shotTreeItem.setText(1, l("{shot}"))

      status = ""
      shotDisabled = False
      if s in newShots:
        status = l("Unable to find matching {shot}")
        shotDisabled = True
        shotTreeItem.setIcon(2, blockIcon)
      shotTreeItem.setText(3, status)

      clips = cmdUtils.shot.clipsFromHieroShotTrackItem(s)
      for c in clips:

        clipItem = items.HieroClipItem(c)
        clipIsAssetised = bool(clipItem.getEntity())

        clipTreeItem = ClipTreeItem()
        clipTreeItem.setItem(clipItem)

        status = l("{publish}")
        disabled = False
        icon = addIcon
        if clipIsAssetised:
          if ignorePublished:
            status = l("Already {published}")
            disabled = True
            icon = tickIcon
          else:
            status = l("{publish} New Version")

        clipTreeItem.setText(3, status)
        clipTreeItem.setDisabled(disabled)
        clipTreeItem.setIcon(2, icon)
        clipTreeItem.setText(1, "Clip")

        if c in sharedClips:

          clipTreeItem.setText(1, "Shared Clip")

          if c not in processsedSharedClips:
            if publishShared:
              if not clipIsAssetised or (clipIsAssetised and not ignorePublished):
                if not shotDisabled:
                  allSharedClips.append(clipTreeItem)
                  processsedSharedClips.add(c)

          placeholderTreeItem = ClipTreeItem()
          placeholderTreeItem.setItem(clipItem)
          placeholderTreeItem.setText(1, "Shared Clip")
          placeholderTreeItem.setFont(0, italicFont)

          if not clipTreeItem.isDisabled():
            if publishShared:
              if sharedParentEntity:
                msg = l("{publish} to '%s'") % sharedParentEntity.getName(context)
                icon = tickIcon
              else:
                msg = "No Shared Clip destination chosen"
                icon = blockIcon
              placeholderTreeItem.setText(3, msg)
            else:
              placeholderTreeItem.setText(3, l("Shared Clip {publish} disabled"))
              icon = crossIcon
          else:
            placeholderTreeItem.setText(3, clipTreeItem.text(3))

          placeholderTreeItem.setIcon(2, icon)

          if shotDisabled:
            placeholderTreeItem.setText(3, '')
            placeholderTreeItem.setIcon(2, QtGui.QIcon())

          placeholderTreeItem.setDisabled(True)
          shotTreeItem.addChild(placeholderTreeItem)

        else:

          if shotDisabled:
            clipTreeItem.setText(3, '')
            clipTreeItem.setIcon(2, QtGui.QIcon())
            clipTreeItem.setDisabled(True)

          if customName and len(clips)==1:
            origName = clipTreeItem.text(0)
            clipTreeItem.setText(4, origName)
            clipTreeItem.setText(0, customName)

          shotTreeItem.addChild(clipTreeItem)

      if shotDisabled:
        shotTreeItem.setDisabled(True)

      shotTreeItem.stopExpand = shotDisabled

      shotParentTreeItem.addChild(shotTreeItem)

    # We need to figure out if our sharedParentEntity is either the same
    # as parentEntity, or one of its (for now, immediate) children.
    sharedInTree = False
    sharedParentTreeItem = None
    if sharedParentEntity:
      if parentEntity.reference == sharedParentEntity.reference:
        sharedParentTreeItem = shotParentTreeItem
        sharedInTree = True
      else:
        for i in range(shotParentTreeItem.childCount()):
          treeItem = shotParentTreeItem.child(i)
          shotEntity = treeItem.entity
          if shotEntity and shotEntity.reference == sharedParentEntity.reference:
            sharedParentTreeItem = treeItem
            sharedInTree = True
            break

    if sharedParentEntity and not sharedParentTreeItem:
      sharedParentTreeItem = GroupingTreeItem()
      sharedParentTreeItem.setFont(0, boldFont)
      sharedParentTreeItem.setEntity(sharedParentEntity, context)

    if allSharedClips and sharedParentTreeItem:
      sharedParentTreeItem.insertChildren(0, allSharedClips)

    treeItems = []
    treeItems.append(shotParentTreeItem)
    if sharedParentTreeItem and not sharedInTree:
      treeItems.append(sharedParentTreeItem)

    return treeItems


  def _expandAll(self, item):

    if hasattr(item, 'stopExpand') and item.stopExpand:
      return

    item.setExpanded(True)
    for i in range(item.childCount()):
      c = item.child(i)
      self._expandAll(c)


class GroupingTreeItem(QtGui.QTreeWidgetItem):

  def __init__(self):
    super(GroupingTreeItem, self).__init__()
    managerIcon = FnAssetAPI.SessionManager.currentSession().getManagerIcon(small=True)
    if managerIcon:
      self.setIcon(0, managerIcon)

    self.stopExpand = False
    self.entity = None
    self.item = None


  def setItem(self, item):
    self.setText(0, item.nameHint)
    self.entity = item.getEntity()
    self.item = item

  def setEntity(self, entity, context):
    self.setText(0, entity.getName(context))
    self.entity = entity


class ClipTreeItem(QtGui.QTreeWidgetItem):

  def setItem(self, item):
    self.setText(0, item.nameHint)

    clip = item.getClip()
    if clip:
      thumbnail = clip.thumbnail()
      if thumbnail:
        self.setIcon(0, QtGui.QPixmap.fromImage(thumbnail))





