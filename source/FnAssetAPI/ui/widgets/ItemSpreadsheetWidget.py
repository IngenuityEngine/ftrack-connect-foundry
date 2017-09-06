import os
from ...ui.toolkit import QtGui, QtWidgets


__all__ = ['ItemSpreadsheetWidget', 'ItemTreeWidgetItem']


class ItemSpreadsheetWidget(QtWidgets.QTreeWidget):
  """

  This class provides a Tree widget, that displays the properties of a number
  of \ref python.items.Item "Items". Multiple Item classes can be presented,
  and the columns will be a union of the unique property names. The columns
  will be ordered by the natrual ordering of the properties (if set), with the
  first column containing the \ref primary_string.

  This widget is sometimes used by a Host as a quick preview of what will be
  published from a set of Items, it is used directly, and consequently doesn't
  derive from BaseWidget, so there is no point in subclassing this as part of a
  Manager's implementation.

  @note This widget should not be sub-classed by Manager implementations.

  """

  _clsProperyCache = {}

  def __init__(self, parent=None, tidyText=True, maxColumnWidth=200):
    """

    @param tidyText Bool [True], when True, values will be cleaned up prior to
    display (for example, floats may be rounded to a smaller number of decimal
    places, long text truncated etc...).

    @param maxColumnWidth int [200] Prevents columns from being made wider than
    the specified size when they are adjusted to fit their content.

    """

    super(ItemSpreadsheetWidget, self).__init__(parent=parent)

    self._items = []
    self._forcedProperties = []
    self._hiddenProperties = []

    self._tidyText = tidyText
    self._maxColWidth = maxColumnWidth

    # Items, grouped by type, so we can create a tree item for each class.
    # Note: The keys are the classes, not class names.
    self._itemMap = {}

    # This stores the names of the aggregated columns, in an ordered list.
    self._headerNames = []


  def setTidyText(self, tidy):
    """

    When True, values will be cleaned up prior to
    display (for example, floats may be rounded to a smaller number of decimal
    places, long text truncated etc...).

    """
    self._tidyText = tidy

  def getTidyText(self):
    return self._tidyText


  def setMaxColumnWidth(self, pixels):
    """

    Prevents columns from being made wider than
    the specified size when they are adjusted to fit their content.

    """
    self._maxColWidth = pixels

  def getMaxColumnWidth(self):
    return self._maxColWidth


  def setItems(self, items):
    """

    Sets the Items displayed in the widget, this will cause it to update.

    """
    self._items = items
    self.refresh()

  def getItems(self):
    return self._items


  def setHiddenProperties(self, hidden):
    """

    @param hidden list(str), Sets a list of property names that should be
    hidden even if they are present on the supplied Items.

    """
    self._hiddenProperties = list(hidden)

  def getHiddenProperties(self):
    return self._hiddenProperties


  def setForcedProperties(self, forced):
    """

    @param list(str) Sets a list of property names that should be displayed as
    a column, regardless of whether it has any non-None values.

    @note If a property named here does not exist on any Item, it will not be
    displayed.

    """
    self._forcedProperties = list(forced)

  def getForcedProperties(self):
    return self._forcedProperties


  def refresh(self):
    """

    Re-drawers the entire tree in a school-boy simplistic way.

    """

    self.setSortingEnabled(False)

    # Sort the items by their class
    self._itemMap = self.__sortItems(self._items)

    # Inspect the properties of the items, and create a set of unique property
    # names - so we only have a single column for each property other than the
    # primary property of each represented Item class.
    self._uniquePropertyNames =  self._buildHeaderList(self._itemMap)

    self.clear()

    self._buildHeaders()
    self._populate()

    self.tidyColumns()

    self.setSortingEnabled(True)


  def tidyColumns(self, hide=True):
    """

    Resizes columns to fit their contents, up to the maximum specified width.

    @param hide Bool [True] if True, then empty columns will be hidden unless
    they are in the 'forced properties' list.

    @see setMaxColumnWidth
    @see setForcedProperties

    """

    numColumns = self.header().count()

    if hide:
      self.hideEmptyColumns()
    else:
      for i in range(numColumns):
        self.setColumnHidden(i, False)

    for i in range(numColumns):
      self.resizeColumnToContents(i)
      # This always makes them a bit tight
      self.setColumnWidth(i, min(self._maxColWidth, self.columnWidth(i)+10))


  def hideEmptyColumns(self):
    """

    Hides empty columns, unless they are on the 'forced properties' list.

    """
    numColumns = self.header().count()
    for i in range(numColumns):
      hide = self.__shouldHideColumn(i)
      self.setColumnHidden(i, hide)


  def _buildHeaders(self):

    names = []

    # Try and find a name for the primary property column (0), if we have
    # multiple primary property names, just leave it blank.

    primaryNames = set()
    for cls in self._itemMap.keys():
      primaryNames.add(cls._primaryProperty)

    if len(primaryNames) == 1:
      names.append(primaryNames.pop())
    else:
      names.append("")

    names.extend(self._uniquePropertyNames)
    self.setHeaderLabels(names)


  def _populate(self):

    if len(self._itemMap) == 1:

      parent = self.invisibleRootItem()
      self._populateClass(parent, self._items)

    else:

      treeItems = []

      for cls, items in self._itemMap.iteritems():
        parent = ClassGroupTreeWidgetItem(cls)
        self._populateClass(parent, items)
        treeItems.append(parent)

      self.addTopLevelItems(treeItems)


  def _populateClass(self, parentItem, items):

    treeItems = []

    for i in items:
      t = self._createTreeItem(i)
      if t:
        treeItems.append(t)

    parentItem.addChildren(treeItems)


  def _createTreeItem(self, item):
    return ItemTreeWidgetItem(item, self._uniquePropertyNames, self._tidyText)


  def __sortItems(self, items):

    itemMap = {}

    for i in items:
      t = type(i)
      if t not in itemMap:
        itemMap[t] = []
      itemMap[t].append(i)

    return itemMap


  def _buildHeaderList(self, itemMap):

    headerNames = []

    for cls in itemMap.iterkeys():

      # Filter out the primary property as we'll always put
      # this in the first column
      predicate = lambda n : n != cls._primaryProperty
      secondaryNames = filter(predicate, cls.getDefinedPropertyNames())

      # Cache these for later too
      ItemSpreadsheetWidget._clsProperyCache[cls] = secondaryNames

      for n in secondaryNames:
        if n not in headerNames:
          headerNames.append(n)

    return headerNames



  def __shouldHideColumn(self, columnIndex):

    def hasContent(i, colIndex):
      childCount = i.childCount()
      if childCount:
        for j in range(childCount):
          c = i.child(j)
          if hasContent(c, colIndex):
            return True
        return False
      else:
        if i.text(columnIndex):
          return True
        return False

    label = self.headerItem().text(columnIndex)
    if not label:
      return False
    if label in self._forcedProperties:
      return False
    if label in self._hiddenProperties:
      return True

    i = self.invisibleRootItem()
    return not hasContent(i, columnIndex)



class ClassGroupTreeWidgetItem(QtWidgets.QTreeWidgetItem):

  def __init__(self, cls):
    super(ClassGroupTreeWidgetItem, self).__init__()
    self.setText(0, cls.__name__)



class ItemTreeWidgetItem(QtWidgets.QTreeWidgetItem):

  def __init__(self, item, headerList, tidy=True):
    super(ItemTreeWidgetItem, self).__init__()

    self._item = item
    self._headerList = headerList
    self._tidy = tidy

    # Primary property is always in col 0
    self.setText(0, self.tidyValue(item.getString()))

    cls = item.__class__
    # We cached the names to save inspecting each item here
    for n in ItemSpreadsheetWidget._clsProperyCache[cls]:
      # 0 is primary property, which was pre-filtered
      index = self._headerList.index(n) + 1
      value = getattr(item, n)
      if value is not None:
        self.setText(index, self.tidyValue(value))


  def tidyValue(self, value):

    if not self._tidy:
      return str(value)

    if isinstance(value, float):
      return ("%.4f" % value).rstrip('0').rstrip('.')

    return str(value)


















