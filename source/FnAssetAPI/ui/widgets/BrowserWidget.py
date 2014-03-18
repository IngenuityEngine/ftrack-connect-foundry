from ...ui.toolkit import QtCore
from ...ui import constants

from ...audit import auditApiCall

from .BaseWidget import BaseWidget


__all__ = ['BrowserWidget']


class BrowserWidget(BaseWidget):

  _kIdentifier = constants.kBrowserWidgetId
  _kDisplayName = constants.kBrowserWidgetName

  selectionChanged = QtCore.Signal(list)
  accepted = QtCore.Signal()


  @auditApiCall()
  def __init__(self, specification, context, parent=None):
    """

    The supplied specification and context should be used to customise the
    browser's display. It should be used to filter the items displayed, and
    determine what a 'valid' selection is. The browser should not return any
    entity references that would raise an error if publish/preflight/resolve
    or any other API calls are made, using the same specification/context.

    The specification may also contain name, path or parent hints that should
    be taken into account if possible when populating the UI.

    If the context.access is any of the 'write' modes, then it is advisable to
    present the user with a way to create new target assets, and affect asset
    naming, if applicable to the particular asset management system. In the way
    that a file dialog often allows folder creation etc...

    For example, if in the organisation hierarchy of a Manager, Assets are
    parented under Shots and they are parented under Sequences. If the spec was
    for a Shot, and the context.access was kWriteMultiple, the browser needs to
    make sure it only allows selection of a Sequence - as that's the only place
    it makes sense to 'write multiple shots'. If the spec was for an Image (ie:
    an Asset), and the access was kWrite, then it might make sense to allow the
    user to pick a Shot - to create a new Asset, or an existing Asset - to
    create a new version. What the relationship of the spec, and the context
    access means to a particular Manager is only known by it - and these
    widgets should be implemented to ensure that only 'sensible' selections are
    permitted.

    @note If the widget makes use of any of the 'hints' in the specification, it
    should always treat them as 'optional' and fall back on defaults in case of
    their omission.

    @param specification FnAssetAPI.specifications.EntitySpecifiation The
    'type' of entity to base filtering on.

    @param context FnAssetAPI.Context.Context The context in which the browsing
    is occurring.

    """
    super(BrowserWidget, self).__init__(parent=parent)



  def _emitSelectionChanged(self):
    """

    A convenience to ensure the selection changed signal is always emitted with
    the current selection.

    The widget should email this signal whenever the resulting 'selection' has
    changed. This can be used for several things, but many dialog integrations
    will use it to then call selectionValid to determine if the 'OK' button
    should be enabled, etc...

    """
    self.selectionChanged.emit(self.getSelection())


  def getSelection(self):
    """

    @return list. The selected @ref entity_reference or references.

    """
    raise NotImplementedError


  def setSelection(self, entityReferences):
    """

    A list of one or more @ref entity_reference to select. This is called when
    a Host knows with certainly that the user should see the supplied
    entityReferences as selected. In other less certain cases, the Specification
    'referenceHint' field may contain a reference that 'could be relevant but
    maybe not - see what you think'.

    Invalid selections should log a warning message, but not raise an
    exception.

    """
    raise NotImplementedError


  def selectionValid(self):
    """

    @return bool, Whether or not the current selection is valid for the initial
    Specification and Context. This may be called by a host to enable/disable
    'accept' buttons, etc...

    """
    raise NotImplementedError


  ##
  # @name Selection Conveniences
  # These methods exists as conveniences to the Host application using the
  # widget, and generally don't need implementing in derived classes. Instead
  # getSelection and setSelection should be implemeted.
  #
  ## @{

  def getSelectionSingle(self):
    """

    @Return str The selection as a single @ref entity_reference rather than an
    array, using the first selected Entity if more than one had been selected.

    """
    sel = self.getSelection()
    return sel[0] if sel else ''

  def setSelectionSingle(self, entityReference):
    """

    Sets the selection of the widget to the supplied @ref entity_reference.

    @param entityReference str An @ref entity_reference

    """
    self.setSelection([entityReference,])

  ## @}

