import time


__all__ = ['Timer']


class Timer(object):
  """

  A simple timer object that can be used, for, er, timing things from a
  wall-clock point of view.

  """

  def __init__(self):
    object.__init__(self)
    self.start = 0
    self.end = None

  def __enter__(self):
    self.start = time.time()
    return self

  def __exit__(self, *args):
    self.end = time.time()

  def interval(self):
    end = self.end if self.end is not None else time.time()
    return end - self.start

  def __str__(self):
    return "%.05fs" % self.interval()


