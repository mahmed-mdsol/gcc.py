import os, errno
import datetime
import sys
import codecs

# TODO Make this observable with fired events instead of having silly hooks.
class Task(object):

  def __init__(self, pre_task = None, post_task = None):
    if pre_task: self.pre_task = pre_task
    if post_task: self.post_task = post_task

  def pre_task(self, *args):
    pass

  def perform(*args):
    pass

  def post_task(self, *args):
    pass

  @staticmethod
  def log(msg):
    sys.stderr.write("{0} ==>\t{1}\n".format(datetime.datetime.now(), msg))


  def __call__(self, *args, **kwargs):
    '''Tasks should be executed by calling them rather than calling perform directly.'''
    self.pre_task()
    self.result = self.perform(*args, **kwargs)
    self.post_task()
    return self.result

class CompilationTask(Task):

  def __init__(self):
    '''Initializes the task with precompilation and postcompilation as pre and post task callbacks'''
    Task.__init__(self, self.precompilation, self.postcompilation)

  def precompilation(self):
    '''Executed before compilation of commits begin.'''
    pass

  def precompile(self, commit):
    '''Executed before the given commit is compiled.'''
    try:
      os.makedirs(self.output_directory_for(commit))
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  def should_compile(self, commit):
    '''Return whether or not the given commit should be compiled. Useful to prevent recompiling commits.'''
    return True

  def should_checkout(self, commit):
    '''Return whether or not this commit should be checked out.'''
    return True

  def compile(self, commit):
    '''Performs the actual compilation of the commit. (This is the one you definitely have to implement)'''
    return None

  def postcompile(self, commit):
    '''Executed after the commit has been compiled.'''
    pass

  def postcompilation(self):
    '''Performed after all compilation has occurred'''
    pass

  def should_ignore_exception(self, e):
    '''Return whether or not this exception occurring during compilation should be ignored.'''
    return False

  def output_directory_for(self, commit):
    return os.path.join(self.options['build_directory'], str(commit), self.__class__.__name__) #./build/abcdef90293901.../

  def incomplete_compilation_file(self, commit):
    return os.path.join(self.output_directory_for(commit), 'incomplete')

  def has_incomplete_output_for(self, commit):
    return os.path.isfile(self.incomplete_compilation_file(commit))

  def mark_incomplete(self, commit, exception=None):
    '''Write out an incomplete file marking the commit compilation as incomplete.'''
    f = open(self.incomplete_compilation_file(commit), 'a')
    print >> f, str(commit)
    print >> f, "By:", str(commit.author), "on", str(datetime.datetime.fromtimestamp(commit.committed_date))
    print >> f, commit.message
    if exception:
      print >> f, "Exception:", repr(exception)
    f.close()

  def log(self, msg):
    try:
      Task.log("[COMPILATION][{0}]: {1}".format(self.__class__.__name__, msg))
    except Exception as e:
      print "Error logging: {0}".format(e)

  def perform(self, commit_targets, compilation_options, git_manager):
    self.targets = commit_targets
    self.options = compilation_options
    self.git_manager = git_manager
    results = {}
    self.log("Beginning compilation of {0} commit targets.".format(len(list(commit_targets))))
    for commit in commit_targets:
      try:
        if self.should_compile(commit):
          self.log("Compiling " + str(commit))
          self.log(commit.message)
          self.log("Committed at {0}".format(datetime.datetime.fromtimestamp(commit.committed_date)))
          if self.should_checkout(commit):
            self.git_manager.switch_to(commit)
          self.precompile(commit)
          results[commit] = self.compile(commit)
          self.postcompile(commit)
          self.log("|====|\n")
      except Exception as e:
        if self.should_ignore_exception(e):
          self.log("Ignoring exception: {0}".format(e))
          pass
        else:
          exc_info = sys.exc_info()
          raise exc_info[0], exc_info[1], exc_info[2]
    return results

class LinkingTask(Task):

  def __init__(self):
    Task.__init__(self, self.prelinkage, self.postlinkage)

  def prelinkage(self):
    pass

  def link(self, compilation_output, linking_options):
    return None

  def postlinkage(self):
    pass

  def log(self, msg):
    Task.log("[LINKING][{0}]: {1}".format(self.__class__.__name__, str(msg)))

  def perform(self, commit_targets, compilation_output, linking_options, git_manager):
    '''Link the given compilation output.'''
    self.commit_targets = commit_targets
    self.compilation_output = compilation_output
    self.linking_options = linking_options
    self.git_manager = git_manager

    self.prelinkage()
    result = self.link(compilation_output, linking_options)
    self.postlinkage()

    return result


class CompositeTask(Task):
  def __init__(self, pre_task = None, post_task = None, *tasks):
    self.tasks = tasks
    Task.__init__(self, pre_task, post_task)

  def perform(self, *args, **kwargs):
    output = []
    for task in self.tasks:
      output.append(task(*args, **kwargs))
    return output

