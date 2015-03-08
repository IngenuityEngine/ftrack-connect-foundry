import threading
import traceback
import time
import weakref
import inspect
from collections import deque
from datetime import datetime as datetime

from . import decorators


__all__ = ['EventManager', 'EventProcessor', 'RateLimitedEventProcessor',
  'DelayedEventProcessor']


class EventManager(object):
  """

  Provides callbacks for asset-related actions in a Host. It is not restricted
  to UI sessions, and is available in batch contexts, etc... Weak references
  are used to hold listeners so there are no retention issues.

  @todo Prune dead weakrefs to listeners

  """

  class WeakBoundMethod:
    """

    Because weakref.ref(obj.method) is taking a weakref to what is effectively
    a temporary lambda that binds the instance to 'self' in the method
    signature, we need a way to take a weakref of the instance, and the
    function, not this transient function, and mimic a bound method upon call.
    Otherwise, its gone before we can use it.

    """

    class _callable:
      """
      Mimics a bound method.
      """
      def __init__(self, obj, method):
        self.im_self = obj
        self.im_func = method
      def __call__(self, *args, **kwargs):
        return self.im_func(self.im_self, *args, **kwargs)

    def __init__(self, boundmethod):
      # Find the underlying instance, and function of the bound method
      self.objRef = weakref.ref(boundmethod.im_self)
      self.methodRef = weakref.ref(boundmethod.im_func)

    def __call__(self):
      # When were called, check both weakrefs are still around, and return a
      # new _callable to mimic the original bound method we weakref'd
      obj = self.objRef()
      method = self.methodRef()
      if obj and method:
        return EventManager.WeakBoundMethod._callable(obj, method)
      else:
        return None


  class Event(object):
    """

    An Internal class that represents an Event when its on the queue. It
    timestamps it self on creation, so that we can uniquely identify any given
    event.

    """

    def __init__(self, eventType, *args, **kwargs):
      super(EventManager.Event, self).__init__()

      self.type = eventType
      self.args = args
      self.kwargs = kwargs
      self.timestamp = datetime.now()

    def __str__(self):

      return "Event(%r, %r, %r, '%s')" % (self.type, self.args, self.kwargs,
          self.timestamp)

    def __repr__(self):
      return str(self)


  __instance = None

  @classmethod
  def singletonInstance(cls):
    """
    Returns the singleton instance of the EventManager class, or derived class.
    """
    if not cls.__instance:
      cls.__instance = cls()
    return cls.__instance


  def __init__(self):
    super(EventManager, self).__init__()

    self.__events = deque()
    self.__globalProcessors = []
    self.__eventProcessors = {}

    self.__listeners = {}

    self.__allowMainThreadExec = False
    self.__mainThreadExecFn = None
    self.__mainThreadEventTypes = set()

    self.__eventsPending = threading.Event()
    self.__eventThread = None

    ## The logger, if set, will be used to print any messages
    self.logger = None


  ## @name Event Listeners
  ## @{


  def registerListener(self, eventType, callable):
    """

    Registers the supplied callable for the specified eventType.
    The callable will be called for any events of that type, with what ever
    args/kwargs are applicable to the event. Only a weak reference to the
    callable is taken.

    """

    listeners = self.__listeners.setdefault(eventType, [])

    # First make sure the listener isn't already registered
    for i in listeners:
      if i() == callable:
        return

    # If its new, make sure we have a weakref, see notes on WeakBoundMethod
    if inspect.ismethod(callable):
      ref = EventManager.WeakBoundMethod(callable)
    else:
      ref = weakref.ref(callable)

    listeners.append(ref)


  def unregisterListener(self, eventType, callable):
    """

    Removes the specified callable as a listener for the specified event type.
    If it is not registered, nothing happens.

    """
    listeners = self.__listeners.setdefault(eventType, [])
    weakref = None
    for i in listeners:
      if i() == callable:
        weakref = i
    if weakref:
      listeners.remove(weakref)


  ## @}


  ## @name Event Queueing
  ## @{

  @decorators.debugApiCall
  def queueEvent(self, eventOrType, *args, **kwargs):
    """

    Submits an event to the queue. This is the main entry point for any clients
    wishing to submit events. Events are processed by any registered
    EventProcessors before being added to the actual queue.

    @param eventOrType str or Event, If a string, an Event object is
    constructed using the string as the event type, and any args, or kwargs are
    bound to the event. If an Event object is passed, any additional args or
    kwargs are ignored.

    @return Bool True if the event is successfully queued, False if any
    registered event processor consumes the event.

    @see @ref addEventProcessor
    @see @ref addGlobalEventProcessor

    """

    if isinstance(eventOrType, EventManager.Event):
      event = eventOrType
    else:
      event = EventManager.Event(eventOrType, *args, **kwargs)

    eventProcessors = self.__eventProcessors.get(event.type, [])
    for p in eventProcessors:
      event = p.processEvent(event, self)
      if not event:
        return False
    for p in self.__globalProcessors:
      event = p.processEvent(event, self)
      if not event:
        return False

    self.injectEvent(event)
    return True


  @decorators.debugApiCall
  def blockingEvent(self, calledFromMainThread, eventType, *args, **kwargs):
    """

    Processes the supplied event without involving the queue. The function
    blocks until the event has been processed.

    @param calledFromMainThread bool, Must be set to False if this call is node
    made from the main thread - this is to ensure that any events are re-routed
    to the main thread where applicable, and that errors are correctly handled.
    Because we don't know the nature of the event loop at this point, it hard
    to automatically know which thread we're on.

    @todo Is there any way to programatically determine which thread we're on?

    @see @ref queueEvent

    """
    event = EventManager.Event(eventType, *args, **kwargs)
    self.__dispatchEvent(event, calledFromMainThread=calledFromMainThread)


  @decorators.debugApiCall
  def injectEvent(self, event):
    """

    Inserts an event into the queue, without any processing by registered event
    processors. Generally @ref queueEvent should be used instead.

    @see @ref queueEvent

    """
    self.__events.append(event)
    self.__eventsPending.set()


  @decorators.debugApiCall
  def clear(self):
    """

    Clears the event queue without processing any outstanding events.

    """
    self.__events = deque()


  def dispatchEvents(self, calledFromMainThread=True):
    """

    Invoke event listeners for all events in the event queue before returning.

    @param calledFromMainThread bool [True], when True, will prevent any
    main thread events using the main thread execution function and causing a
    deadlock.

    @see @ref setRunOnMainThread

    """
    while self.__events:
      self.__dispatchEvent(self.__events.popleft(), calledFromMainThread=calledFromMainThread)
    self.__eventsPending.clear()

  ## @}


  ## @name Event Processors
  # Event processors will be called for relevant event types before the event
  # is submitted to the queue. Global event processors will be called for all
  # events.
  ## @{

  def addGlobalEventProcessor(self, processor):
    self.__globalProcessors.append(processor)


  def addEventProcessor(self, eventType, processor):
    processors = self.__eventProcessors.setdefault(eventType, [])
    processors.append(processor)

  ## @}


  ## @name Threaded event processing
  # The EventManager can be run on a separate thread to monitor and clear the
  # queue.
  ## @{


  def run(self):
    """

    Spawns a thread, and calls dispatchEvents whenever there is an event in the
    queue. Subsequent calls do nothing if there EventManager is already running
    on another thread.

    @warning Its not possible to run the event loop thread in a host
    application that doesn't have the ability to run events back on the main
    thread. Many of the listeners are required to manipulate UI elements,
    etc... that must run on that thread.

    """

    if not self.__mainThreadExecFn:
      raise RuntimeError("Can't tun the EventManager on a background thread "+
          "as no main thread callback function has been registered.")

    if self.__eventThread:
      return

    self.__eventThread = threading.Thread(target=self.__run)
    self.__eventThread.daemon = True
    self.__eventThread.start()


  def setMainThreadExecFn(self, callable):
    """

    When using @ref run the EventManager will spawn a thread to process the
    event queue.  If it is desired for event listeners to be run on the main
    thread, the host application needs to provide a callback to allow a method
    to be run on the main thread.

    @param callable, A callable object that will be called with a callable, an
    args list, and a kwarg dictionary, to run on the main thread. Ie: the
    arguments are *not* unpacked to this call handler.

    """
    if callable is not None:
      self.__allowMainThreadExec = True
      self.__mainThreadExecFn = callable
    else:
      self.__allowMainThreadExec = False
      self.__mainThreadExecFn = None


  def setRunOnMainThread(self, eventType, runOnMain):
    """

    Call to request that the specified eventType should be run on the main
    thread if the event manager is running on its own thread.

    @param runOnMain bool, if True, then the supplied eventType will be run on
    the main thread if a main thread exec function has been registered.

    @see @ref run
    @see @ref setMainThreadExecFn

    """
    if runOnMain:
      self.__mainThreadEventTypes.add(eventType)
    elif eventType in self.__mainThreadEventTypes:
      self.__mainThreadEventTypes.remove(eventType)

  ## @}



  def __run(self):
    self.__eventsPending.wait()
    self.dispatchEvents(calledFromMainThread=False)
    self.__run()


  def __dispatchEvent(self, event, calledFromMainThread=True):

    listeners = self.__listeners.get(event.type, None)

    if listeners:
      for l in listeners:
        # l is a weakref
        callable = l()
        if callable:
          try:
            if not calledFromMainThread and self.__allowMainThreadExec and \
                event.type in self.__mainThreadEventTypes:
              self.__mainThreadExecFn(callable, event.args, event.kwargs)
            else:
              callable(*event.args, **event.kwargs)
          except Exception as e:
            if self.logger:
              msg = "Exception caught in event listener for '%s': %s" % \
                (event.type, e)
              tb = traceback.format_exc()
              if calledFromMainThread:
                self.logger.warning(msg)
                self.logger.debug(tb)
              elif self.__allowMainThreadExec:
                self.__mainThreadExecFn(self.logger.warning, [msg,], {})
                self.__mainThreadExecFn(self.logger.debug, [tb,], {})



class EventProcessor(object):
  """

  The EventProcessor (or any class that implements processEvent) will be called
  to process any events it has been registered for, before they are injected
  into the event queue.

  """

  def processEvent(self, event, queue):
    """

    Called by the EventManager before an Event is injected to the queue.

    @return Event or None. If an EventManager.Event is returned, it will be
    passed to the next processor registered for that event type, or injected
    into the queue. If None is returned no further processing is carried out
    and the Event is effectively discarded.

    """
    return event



class RateLimitedEventProcessor(EventProcessor):
  """

  An EventProcessor that ignores any events that occur more frequently than a
  specified maximum rate.

  An Event will only be queued if it occurs after the minimum interval defined
  by the specified eventsPerSec.

  """

  def __init__(self):
    super(RateLimitedEventProcessor, self).__init__()

    self.__rate = -1
    self.__minInterval = 0
    self.__lastEventTime = 0


  def getMaxRate(self):
    return self.__rate


  def setMaxRate(self, eventsPerSec):

    self.__rate = eventsPerSec

    if eventsPerSec > 0:
      self.__minInterval = 1.0/eventsPerSec
    else:
      self.__minInterval = 0


  def processEvent(self, event, queue):
    """
    """
    now = self._now()
    interval = now - self.__lastEventTime
    self.__lastEventTime = now

    if interval > self.__minInterval:
      return event
    else:
      return None


  def _now(self):
    t = datetime.now()
    return ((t.hour * 60 * 60) + t.second) * 1000 + (t.microsecond/1000.0)



class DelayedEventProcessor(EventProcessor):
    """

    Queues the last submitted event after a specified delay. Subsequent events
    reset the delay timer, in such a fashion that only a single event is ever
    submitted after the required idle period.

    """

    # If an attribute is set on an event with this name, it will be passed
    # straight through the processor with no delay
    kBypassAttribute = '_DEP_processed'

    def __init__(self):
      super(DelayedEventProcessor, self).__init__()

      self.__lastEvent = None
      self.__recipientQueue = None
      self.__delayTime = 1

      self.__previousEventId = None
      self.__eventPending = threading.Event()

      # We need a thread to continuously run our callback, so that we can keep
      # receiving events on the main event thread.
      self.__thread = threading.Thread(target=self.__threadCallback)
      self.__thread.daemon = True
      self.__thread.start()


    def getDelay(self):
      return self.__delayTime


    def setDelay(self, seconds):
      self.__delayTime = seconds


    @decorators.debugApiCall
    def processEvent(self, event, queue):

      if hasattr(event, self.kBypassAttribute):
        return event

      self.__lastEvent = event
      self.__recipientQueue = queue

      # Set the threading Event so that the __threadCallback will un-lock
      self.__eventPending.set()

      return None


    def __threadCallback(self):

      # We're continuously called on a background thread, once an event has been
      # queued. Once we've been called twice with the same __lastEvent, we'll
      # actually emit it. Otherwise, we hold on for __delayTime again

      # Wait on this event so we're not needlessly consuming cycles when no
      # events have been queued.
      self.__eventPending.wait()

      time.sleep(self.__delayTime)

      if self.__lastEvent:
        # We cant just use id/etc... as they get reused
        eventId = "%s%s" % (id(self.__lastEvent), self.__lastEvent.timestamp)
        # We have had the same event for the delay time, so we can emit it
        if eventId == self.__previousEventId:
          # As we need to ensure the event is processed correctly, we use
          # queueEvent, rather than injectEvent, so lets set an attribute so
          # we'll just pass it trough later rather than delaying it again.
          e = self.__lastEvent
          setattr(e, self.kBypassAttribute, True)
          self.__recipientQueue.queueEvent(e)
          # Unset out lock event so we'll block until another event has been
          # received.
          self.__eventPending.clear()

        self.__previousEventId = eventId

      self.__threadCallback()






