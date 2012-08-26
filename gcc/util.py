import fnmatch
import os
import copy

def find_files(directory, pattern):
  for root, dirs, files in os.walk(directory):
    for basename in files:
      if fnmatch.fnmatch(basename, pattern):
        filename = os.path.join(root, basename)
        yield filename

def dynamically_extend(instance, with_class):
  '''Return a shallow copy of the given instance that extends the other class. [Only works with instances of new-style classes]'''
  # Make a shallow copy so we don't alter the original instance
  extended = copy.copy(instance)
  # Create a dynamic class that has the same classname as the original instance, but now extends with_class and its original class.
  extended.__class__ = type(instance.__class__.__name__, (instance.__class__, with_class), {})
  return extended
