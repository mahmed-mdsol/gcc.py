from git_manager import GitManager
from tasks.task import CompilationTask, LinkingTask
import os

class GitCompiler:
  '''The main honcho - the compiler that travels through time and compiles your commits.'''

  def __init__(self, repo='.', build_directory='./build', **env):
    '''Initialize'''
    self.git_manager = GitManager(repo)
    self.commit_targets = []
    self.build_directory = os.path.abspath(build_directory)
    self.compilation_options = dict(build_directory = self.build_directory)
    self.linking_options = {}
    os.environ.update(env)

  def add_commit_targets(self, **kwargs):
    '''Add commit targets to compile.'''
    self.commit_targets.extend(self.git_manager.get_commits(**kwargs))

  def remove_commit_targets(filter_function):
    '''Remove commit targets that cause the given function to return a truthy value.'''
    self.commit_targets[:] = [commit for commit in self.commit_targets if not filter_function(commit)]


  def set_compilation_task(self, task, **kwargs):
    '''Set the compilation task (the thing that'll compile each commit)'''
    self.compilation_task = task
    if kwargs:
      self.compilation_options.update(kwargs)

  def set_linking_task(self, task, **kwargs):
    '''Set the linking task (the thing that'll link the outputs of the compilation task)'''
    self.linking_task = task
    if kwargs:
      self.linking_options.update(kwargs)

  def compile(self, link=True, **additional_compilation_args):
    '''Compile (and link unless specified otherwise)!
       TODO: Thread this out with an observer to output progress.
    '''
    options = self.compilation_options.copy()
    if additional_compilation_args:
      options.update(additional_compilation_args)
    self.compilation_output = self.compilation_task(self.commit_targets, options, self.git_manager)
    if link: 
      self.link(self.compilation_output)

  def link(self, compilation_output):
    '''Link compilation output!'''
    self.linking_task(self.commit_targets, compilation_output, self.linking_options, self.git_manager)

