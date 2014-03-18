import inspect
import copy


__all__ = ['Auditor']


class Auditor(object):
  """

  This class provides a quick-and-dirty accounting mechanism for Class,
  method and object usage. The idea is to look at the extents of usage, rather
  than any kind of realtime reporting.

  Raw coverage data is accessible, or can be sprinted to a string.

  """

  kKey_Count = '__count__'
  kKey_Args = '__args__'

  def __init__(self):
    super(Auditor, self).__init__()

    self.__enabled = True
    self.reset()


  def getEnabled(self):
    return self.__enabled

  def setEnabled(self, enabled):
    self.__enabled = enabled


  def reset(self):
    self.__coverage = {}
    self.__groups = {}


  def addClass(self, obj, group=None):
    """

    Adds usage of the supplied Class.

    @param obj instance or class, The Class to record will ultimately be
    determined by inspection of __class__ or type() on this object or its base.

    @param group str [None], If supplied, the Class's usage will also be counted in
    the supplied group.

    @return dict, The coverage data dict for the Class

    """
    if not self.__enabled:
      return

    cls = self.__classFromObj(obj)

    # Classes are simply stored as top-level keys in the __coverage dict
    clsDict = self.__getObjDict(self.__coverage, cls)
    clsDict[self.kKey_Count] += 1

    # If we have a group, we store Classes as top-level keys there too
    if group:
      groupDict = self.__groups.setdefault(group, {})
      groupClsDict = self.__getObjDict(groupDict, cls)
      groupClsDict[self.kKey_Count] += 1

    # We return the dictionary for the Class to make chained usage easier later
    # on - so we don't have to go hunting for it twice
    return clsDict


  def addMethod(self, instanceMethod, obj=None, group=None, arg=None):
    """

    Adds usage of a method.

    @param instanceMethod object, The function or bound method that you will to
    count.

    @param obj object [None], If supplied the parent Class for the method will
    be determined from this object, rather than from introspection of the
    instanceMethod arg.

    @prarm group str, If supplied, a count will also be registered for the
    method under this group (note: for groups, the parent Class usage isn't
    recorded).

    @param arg dict [{}] Can contain the args passed to the method at the time
    of invocation, these will be stored as an array under the kKey_Args key in
    the functions coverage dict.

    @return dict, The coverage data dict for the method

    """

    if not self.__enabled:
      return

    # Count a usage of the methods Class, which will conveniently give us back
    # the right dictionary for any child methods, etc....
    cls = self.__classFromObj(obj if obj else instanceMethod)
    clsDict = self.addClass(cls)

    # Unpack the function object if its a bound method
    func = instanceMethod
    if hasattr(instanceMethod, 'im_func'):
      func = instanceMethod.im_func

    # Now count the function as a key under it's parent Class's dict
    methodDict = self.__getObjDict(clsDict, func)
    methodDict[self.kKey_Count] += 1

    # If we have been supplied args, then append them to the kKey_Args key in
    # the method's dict.
    if arg:
      argsList = methodDict.setdefault(self.kKey_Args, [])
      try:
        argsList.append(copy.deepcopy(arg))
      except:
        pass

    # If we have a group, count the method there too. We don't keep args here,
    # only in the main __coverage dict.
    if group:
      groupDict = self.__groups.setdefault(group, {})
      groupObjDict = self.__getObjDict(groupDict, func)
      groupObjDict[self.kKey_Count] += 1

    # Return this in case its useful
    return methodDict


  def addObj(self, obj, group=None):
    """

    Simply count the usage of 'something'. Doesn't really matter what, as long
    as its hashable so can be used as a key in a dict.

    @param group str [None], If supplied, a count will also be recorded under
    the named group.

    @return dict, The coverage dict for the object.

    """

    if not self.__enabled:
      return

    objDict = self.__getObjDict(self.__coverage, obj)
    objDict[self.kKey_Count] += 1

    if group:
      groupDict = self.__groups.setdefault(group, {})
      groupObjDict = self.__getObjDict(groupDict, obj)
      groupObjDict[self.kKey_Count] += 1

    return objDict


  def coverage(self):
    """

    @return dict, The main coverage data dict with all data since the last
    reset. It is a hierarchical dictionary where at any level two keys
    represent the coverage data: kKey_Count (int) and kKey_Args (list). Other
    keys in the dict represent child counts. For example top-level keys are
    Classes or arbitrary objects. Other keys under a Class dict are the methods
    of that Class.

    """
    return self.__coverage


  def groups(self):
    """

    @return dict, As per coverage, except the Grouping dict is returned. If no
    grouped counts have been made, this will be empty. Otherwise, the top-level
    keys will be group names, and values will be a dictionary of coverage dicts
    for arbitrary objects.

    """
    return self.__groups


  def sprintCoverage(self, groupsOnly=False):
    """

    @return str, A multi-line formatted string containing recorded coverage.

    """

    s = ""

    if not groupsOnly and self.__coverage:
      s  += "Coverage:\n\n"
      for c in sorted(self.__coverage.keys()):
        # c will be a Class or arbitrary object
        itemDict = self.__coverage[c]
        n = c.__name__ if hasattr(c, '__name__') else c
        s += "  %s (%d)\n" % (n, itemDict.get(self.kKey_Count, 0))
        for m, d in itemDict.items():
          # m will be a method or function (or the count key for the class)
          # d will be the data for that method
          if m == self.kKey_Count: continue
          n = m.__name__ if hasattr(m, '__name__') else m
          s += "    %s (%s)\n" % (n, d.get(self.kKey_Count, 0))
          # Print the args list for each invocation if we have the data
          args = d.get(self.kKey_Args, [])
          if args:
            for a in args:
              # Some hosts will raise here based on binding issues, etc...
              try: s += "        %r\n" % (a,)
              except: pass
            s += "\n"

    if self.__groups:
      s += "\n"
      s += "Groups:\n\n"
      for g in sorted(self.__groups.keys()):
        # Groups are just arbitrary string keys
        s += "  %s:\n" % g
        gDict = self.__groups[g]
        for c in sorted(gDict.keys()):
          # c could be a class, or anything really
          n = c.__name__ if hasattr(c, '__name__') else c
          s += "    %s (%d)\n" % (n, gDict[c].get(self.kKey_Count, 0))
        s += "\n"

    return s


  def __getObjDict(self, dict, obj):
    # Presently, we simply create a child dict for the obj if there isn't one,
    # and ensure it has the count key, and its initialized to 0
    return dict.setdefault(obj, { self.kKey_Count : 0 })


  def __classFromObj(self, obj):

    # If its an instance method then get self, which will be an instance, or a
    # class in the case of @classmethods
    if hasattr(obj, 'im_self'):
      obj = obj.im_self

    # If its a class, were good
    if inspect.isclass(obj):
      return obj

    # Else, see if we can get the class
    if hasattr(obj, '__class__'):
      return obj.__class__

    # Fall back on Type
    return type(obj)


