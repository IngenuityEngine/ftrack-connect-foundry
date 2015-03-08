from . import logging
from . import exceptions


__all__ = ['ScopedContextOverride', 'ScopedActionGroup', 'ScopedProgressManager']


class ScopedContextOverride(object):
  """

  A convenience context manager to allow locale, access and retention to be
  overridden within a scope.

  """

  def __init__(self, context):

    super(ScopedContextOverride, self).__init__()
    self.context = context

  def __enter__(self, *args, **kwargs):

    if self.context:
      self.oldLocale = self.context.locale
      self.oldAccess = self.context.access
      self.oldRetention = self.context.retention

    return self

  def __exit__(self, *args, **kwargs):

    if self.context:
      self.context.locale = self.oldLocale
      self.context.access = self.oldAccess
      self.context.retention = self.oldRetention



class ScopedActionGroup(object):
  """

  A convenience class to push/pop an action group based on the lifetime of the
  object, useful when combined with a 'with' statement.

  """

  def __init__(self, session, context, cancelOnException=True):

    super(ScopedActionGroup, self).__init__()
    self.__session = session
    self.__context = context
    self.__cancelOnException = cancelOnException


  def __enter__(self):
    self.__session.pushActionGroup(self.__context)


  def __exit__(self, exceptionType, exceptionValue, traceback):

    if exceptionType is not None and self.__cancelOnException:
        self.__session.cancelActions(self.__context)
    else:
        self.__session.popActionGroup(self.__context)



class ScopedProgressManager(object):
  """

  Helps manage progress steps in iterated code. Allows simple with statements
  to be used to signal, update and cancel progress. It will automatically end
  progress if an exception is raised.

  @todo Check the exception -> cancel behaviour as it isn't always happening

  @todo The actual submitted progress values are off at present I think.

  @code
  items = ...
  with ScopedProgressManager(len(items)) as progress:
    for i in items:
      with progress.step("Doing something to %s" % i):
        i.doSomething()
  @endcode

  """

  class ProgressItem(object):

    def __init__(self, manager, msg):
      super(ScopedProgressManager.ProgressItem, self).__init__()
      self.manager = manager
      self.msg = msg

    def __enter__(self, *args, **kwargs):
      self.manager.startStep(self.msg)

    def __exit__(self, *args, **kwargs):
      self.manager.finishStep()


  def __init__(self, itemCount):
    super(ScopedProgressManager, self).__init__()
    self.numItems = float(itemCount)
    self.currentItem = 0
    self.lastMsg = ''

  def __enter__(self, *args, **kwargs):
    return self

  def __exit__(self, *args, **kwargs):
    logging.progress(-1)

  def step(self, msg=None):
    return ScopedProgressManager.ProgressItem(self, msg)

  def startStep(self, msg):
    self.lastMsg = msg
    cancelled = logging.progress(self.currentItem/self.numItems, msg)
    if cancelled:
      raise exceptions.UserCanceled
    return cancelled

  def finishStep(self):
    self.currentItem += 1
    cancelled = logging.progress(self.currentItem/self.numItems,
        self.lastMsg)
    if cancelled:
      raise exceptions.UserCanceled
    return cancelled

