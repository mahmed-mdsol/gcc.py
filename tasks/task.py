
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

  def __call__(self, *args, **kwargs):
    '''Tasks should be executed by calling them rather than calling perform directly.'''
    self.pre_task()
    self.result = self.perform(*args, **kwargs)
    self.post_task()

class CompilationTask(Task):

  def __init__(self):
    '''Initializes the task with precompilation and postcompilation as pre and post task callbacks'''
    Task.__init__(self, self.precompilation, self.postcompilation)

  def precompilation(self):
    '''Executed before compilation of commits begin.'''
    pass

  def precompile(self, commit):
    '''Executed before the given commit is compiled.'''
    pass

  def compile(self, commit):
    '''Performs the actual compilation of the commit. (This is the one you definitely have to implement)'''
    return None

  def postcompile(self, commit):
    '''Executed after the commit has been compiled.'''
    pass

  def postcompilation(self):
    '''Performed after all compilation has occurred'''
    pass

  def should_compile(self, commit):
    '''Return whether or not the given commit should be compiled. Useful to prevent recompiling commits.'''
    return True

  def perform(self, commit_targets, compilation_options, git_manager):
    self.targets = commit_targets
    self.options = compilation_options
    self.git_manager = git_manager
    results = {}

    for commit in commit_targets:
      if self.should_compile(commit):
        self.precompile(commit)
        results[commit] = self.compile(commit)
        self.postcompile(commit)

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

  def perform(self, compilation_output, linking_options, git_manager):
    self.compilation_output = compilation_output
    self.linking_options = linking_options
    self.git_manager = git_manager

    self.prelinkage()
    result = self.link(compilation_output, linking_options)
    self.postlinkage()

    return result


def CompositeTask(Task):
  def __init__(self, pre_task = None, post_task = None, *tasks):
    self.tasks = tasks
    Task.__init__(self, pre_task, post_task)

  def perform(self, *args, **kwargs):
    output = []
    for task in self.tasks:
      output.append(task.perform(*args, **kwargs))
    return output

