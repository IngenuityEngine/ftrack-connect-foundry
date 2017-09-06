from QtExt import QtGui, QtWidgets, QtCore

import hiero.core
import hiero.ui

import FnAssetAPI.exceptions
import FnAssetAPI.specifications


import widgets
import commands as uiCommands

from .. import utils as cmdUtils
from .. import specifications

# Bring these larger actions into the namespace
from managerActions import ManagerPolicyDependentAction
from buildAssetTrackActions import BuildAssetTrackAction, RefreshAssetTrackAction


#################################################

## @todo Many of these need re-factoring to use the approach of the prototype,
## whereby work/publishing is separated, to allow the UI to preview the result

## @todo Many of these dialogs/UIs etc... should be suitably delegatable to the
## asset plug-in, to allow them to make PRETTY things, and things that look
## like the rest of their integration.

## @todo UNDO grouping


class AssetPreferencesAction(QtWidgets.QAction):

  def __init__(self, name="Preferences...", parent=None):
    super(AssetPreferencesAction, self).__init__(name, parent)
    self.triggered.connect(self.go)

  def go(self):
    s = FnAssetAPI.SessionManager.currentSession()
    self.w = widgets.AssetPreferencesDialog(self.parent())
    self.w.setSession(s)
    self.w.show()


class OpenPublishedProjectAction(ManagerPolicyDependentAction):

  def __init__(self, parent=None):

    name = "Open {published} Project..."
    spec = specifications.HieroProjectSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kRead

    super(OpenPublishedProjectAction, self).__init__(name, spec, context, parent=parent)

    self.triggered.connect(uiCommands.openPublishedProjectUI)




class PublishProjectAction(ManagerPolicyDependentAction):

  def __init__(self, parent=None):

    name = "{publish} Project..."
    spec = specifications.HieroProjectSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(PublishProjectAction, self).__init__(name, spec, context, parent)

    self.triggered.connect(self.go)

    self.__selection = []


  def setSelection(self, selection):

    self.__selection = cmdUtils.object.projectsFromSelection(selection)
    self.setEnabled(bool(self.__selection) and self._allowedByPolicy)

    l = FnAssetAPI.l

    numProjects = len(self.__selection)
    if numProjects == 1:
      self.setText(l("{publish} %s..." % self.__selection[0].name()))
    elif numProjects > 1:
      self.setText(l("{publish} %d projects..." % numProjects))
    else:
      self.setText(l("{publish} Project..."))


  def go(self):
    if self.__selection:
      uiCommands.publishProjectsUI(self.__selection)



class ImportClipsAction(ManagerPolicyDependentAction):

  @staticmethod
  def __filterToBins(item):
    return isinstance(item, hiero.core.Bin)


  def __init__(self, parent=None):

    name = "Import {published} Clips..."
    spec = specifications.HieroProjectSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(ImportClipsAction, self).__init__(name, spec, context, parent=parent)
    self.triggered.connect(self.go)
    self.__selection = None


  def setSelection(self, selection):

    self.__selection = filter(self.__filterToBins, selection)


  def go(self):

    target = None

    if self.__selection:
      target = self.__selection[0]

    uiCommands.importClipsUI(target)


class LinkSequenceToGroupingAction(ManagerPolicyDependentAction):

  def __init__(self, parent=None):

    name = "Associate Sequence with {manager}..."
    spec = FnAssetAPI.specifications.ShotSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(LinkSequenceToGroupingAction, self).__init__(name, spec, context, parent=parent)

    self.triggered.connect(self.go)


  def setSelection(self, selection):

    self.__selection = None

    if selection:
      # See if we have a single sequence
      if len(selection) == 1 and isinstance(selection[0], hiero.core.Sequence):
        self.__selection = selection[0]
      else:
        # See if they have a parent sequence (ie. TrackItems)
        for s in selection:
          if hasattr(s, 'parentSequence'):
            self.__selection = s.parentSequence()
            break
      if not self.__selection:
        # See if they're bin items instead
        sequences = cmdUtils.object.binItemsToObjs(selection, hiero.core.Sequence)
        if len(sequences) == 1:
          self.__selection = sequences[0]

    self.setEnabled(bool(self.__selection) and self._allowedByPolicy)


  def go(self):

    if self.__selection:
      uiCommands.linkToSequenceUI(self.__selection)



class PublishClipsAction(ManagerPolicyDependentAction):

  def __init__(self, parent=None):

    name = "{publish} Clips..."
    spec = FnAssetAPI.specifications.ImageSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(PublishClipsAction, self).__init__(name, spec, context, parent=parent)

    self.triggered.connect(self.go)
    self.__selection = []


  def setSelection(self, selection):

    self.__selection = []

    enabled = False

    clips = []

    if selection:

      if isinstance(selection[0], (hiero.core.TrackItem, hiero.core.TrackBase)):
        trackItems = cmdUtils.object.trackItemsFromSelection(selection)
        for t in trackItems:
          clip = cmdUtils.object.clipFromTrackItem(t)
          if clip:
            clips.append(clip)
      else:
        clips = cmdUtils.object.binItemsToObjs(selection, hiero.core.Clip)

    if clips:
      enabled = True

    self.__selection = clips

    enabled = bool(clips)
    self.setEnabled(enabled and self._allowedByPolicy)


  def go(self):
    if self.__selection:
      uiCommands.publishClipsUI(self.__selection)


class TrackItemBasedAction(ManagerPolicyDependentAction):

  def __init__(self, name, spec, context, parent=None):
    super(TrackItemBasedAction, self).__init__(name, spec, context, parent=parent)
    self.triggered.connect(self.go)
    self._selection = []


  def _reduceSelection(self, selection):
    return cmdUtils.object.trackItemsFromSelection(selection)



class GenerateShotsAction(TrackItemBasedAction):

  def __init__(self, parent=None):

    name = "Create {shots}..."
    spec = FnAssetAPI.specifications.ShotSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(GenerateShotsAction, self).__init__(name, spec, context, parent=parent)


  def setSelection(self, selection):

    # These seem to be sorted by chronologically
    self._selection = self._reduceSelection(selection)

    self.setEnabled(len(self._selection) and self._allowedByPolicy)


  def go(self):

    if self._selection:
      uiCommands.createShotsFromTrackItemsUI(self._selection)



class UpdateShotsAction(TrackItemBasedAction):

  def __init__(self, parent=None):

    name = "Update {shot} timings..."
    spec = FnAssetAPI.specifications.ShotSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(UpdateShotsAction, self).__init__(name, spec, context, parent=parent)


  def setSelection(self, selection):
    # These seem to already be sorted by chronologically
    self._selection = self._reduceSelection(selection)
    self.setEnabled(len(self._selection) and self._allowedByPolicy)


  def go(self):
    if self._selection:
      uiCommands.updateShotsFromTrackItemsUI(self._selection)


class PublishShotsClipsAction(TrackItemBasedAction):

  def __init__(self, parent=None):

    name = "{publish} Clips to {shots}..."
    spec = FnAssetAPI.specifications.ImageSpecification()
    context = FnAssetAPI.SessionManager.currentSession().createContext()
    context.access = context.kWrite

    super(PublishShotsClipsAction, self).__init__(name, spec, context, parent=parent)


  def setSelection(self, selection):

    self._selection = self._reduceSelection(selection)
    self.setEnabled(bool(self._selection) and self._allowedByPolicy)


  def go(self):

    if self._selection:
      uiCommands.publishShotClipsFromTrackItemsUI(self._selection)



class StartAuditAction(QtWidgets.QAction):

  def __init__(self, parent=None):
    super(StartAuditAction, self).__init__("Restart", parent)
    self.triggered.connect(self.go)

  def go(self):
    FnAssetAPI.audit.auditCalls = True
    FnAssetAPI.audit.auditor().reset()



class StopAuditAction(QtWidgets.QAction):

  def __init__(self, parent=None):
    super(StopAuditAction, self).__init__("Stop", parent)
    self.triggered.connect(self.go)

  def go(self):
    FnAssetAPI.audit.auditCalls = False
    print FnAssetAPI.audit.auditor().sprintCoverage()


class PrintAuditAction(QtWidgets.QAction):

  def __init__(self, parent=None):
    super(PrintAuditAction, self).__init__("Print", parent)
    self.triggered.connect(self.go)

  def go(self):
    print FnAssetAPI.audit.auditor().sprintCoverage()


