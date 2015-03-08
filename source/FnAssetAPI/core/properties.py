import re


__all__ = ['UntypedProperty', 'TypedProperty', 'TimecodeProperty']


class UntypedProperty(object):
  """

  The Property classes form the basis for the FixedInterfaceObject. They
  implement a Python property, and store the data in the instances dataVar.
  Docstrings can also be provided to improve help() output.

  @param initVal, An initial value for the property if None is not supported.

  @param doc str, A docstring for the property that will be printed when
  help() is called on the object.

  @param dataVar str ['__dict__'] The instance dict attribute that should be
  used to hold the properties data. It defaults to the objects __dict__, but
  could be something else if de-coupled storage is desired.

  @param dataName str ['__<id(self)>'] The key to use when storing a value in
  dataVar. If ommited, this defaults to a prefixed version of the id of the
  object, though this may cause serialisation issues - so its recommended that
  this is set to something meaningful. Some objects use Metaclasses to take care 
  of this automatically to avoid the developer having to manually match the
  dataName to the actual attribute name.

  @oaram order int [-1] A UI hint as to the 'natural ordering' for this
  property when it's displayed in a list.

  """

  def __init__(self, initVal=None, doc=None, dataVar=None, dataName=None, order=-1):
    super(UntypedProperty, self).__init__()
    self.__doc__ = doc
    self.value = initVal
    self.dataVar = dataVar if dataVar else '__dict__'
    # I don't know how well this will serialize but its to avoid you always
    # having to name it twice. Though most Factories take care of this now.
    self.dataName = dataName if dataName else "__%s" % id(self)
    # This may be used for positioning in the ui, this should be > 0
    # as -1 indicates that it is unordered or ordering is not important
    self.order = order

  def __get__(self, obj, cls):
    # Allow access to ourself if we're called on the class
    if obj is None:
      return self
    return getattr(obj, self.dataVar).get(self.dataName, None)

  def __set__(self, obj, value):
    getattr(obj, self.dataVar)[self.dataName] = value


class TypedProperty(UntypedProperty):
  """

  Extends the UntypedProperty to allow strict type checking of values.

  @param typ Class, Sets will be conformed to being instances of this type of
  None.

  @exception ValueError or other as per constructing an instance of the
  property's typ from the supplied value. ie: typ(value).

  """

  def __init__(self, typ, initVal=None, doc=None, dataVar=None, dataName=None,
      order=-1):
    super(TypedProperty, self).__init__(initVal, doc, dataVar, dataName, order)
    self.__doc__ = "[%s]" % typ.__name__
    if doc:
      self.__doc__ += " %s" % doc
    self.typ = typ

  def __set__(self, obj, value):
    if not isinstance(value, self.typ) and value is not None:
      value = self.typ(value)
    super(TypedProperty, self).__set__(obj, value)


class TimecodeProperty(TypedProperty):
  """

  A specialised property to hold SMPTE timecode values. Valid formats are:

    HH:MM:SS:FF (non-drop)
    HH:MM:SS;FF or HH:MM:SS.FF (drop)

  Any of the above can be suffixed with a floating point frame rate (R) or
  prefixed with a sign.

    [+-]HH:MM:SS:FF@R

  """

  ## A regex that can be used to match timecode values, groups are named
  ## 'hours', 'minutes', 'seconds', 'frames', 'dropFrame' and 'frameRate'
  timecodeRegex = re.compile(r'(?P<sign>[+\-]?)(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})(?P<dropFrame>[:;.])(?P<frames>[0-9]{2})(?:@(?P<frameRate>[0-9.]+)|$)')


  def __init__(self, doc=None, dataVar=None, dataName=None, order=-1):
    super(TimecodeProperty, self).__init__(str, None, doc, dataVar,
        dataName, order)


  def __set__(self, obj, value):
    if value is not None:
      if not isinstance(value, str):
        raise ValueError("Timecodes must be a string (%s)" % type(value))
      if not self.timecodeRegex.match(value):
        raise ValueError("Invalid timecode format: '%s' (hh:mm:ss:ff or "+
            "[+-]hh:mm:ss[:;.]ff@rr[.rr]])" % value)
    super(TypedProperty, self).__set__(obj, value)


  def getTimecode(self, value):
    """

    @return str, The timecode component of @param value, or an empty string if
    no valid timecode is found in the input.

    """

    if value is None:
      return ''

    match = self.timecodeRegex.match(value)
    if not match:
      return ''

    sign = match.group('sign')
    sign = sign if sign else ''
    hh = int(match.group('hours'))
    mm = int(match.group('minutes'))
    ss = int(match.group('seconds'))
    ff = int(match.group('frames'))
    df = match.group('dropFrame')

    tc = "%s%02d:%02d:%02d%s%02d" % (sign, hh, mm, ss, df, ff)
    return tc


  def getFrameRate(self, value):
    """

    @return float, The frame rate of @param value else 0 if no valid framerate
    is encoded in the value.

    """

    rate = 0.0

    if value is None:
      return rate

    match = self.timecodeRegex.match(value)
    if not match:
      return rate

    rr = match.group('frameRate')
    if rr:
      rate = float(rr)

    return rate




