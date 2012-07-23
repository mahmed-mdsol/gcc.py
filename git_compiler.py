from git_manager import GitManager
from tasks.task import CompilationTask, LinkingTask
import os

class GitCompiler:
  '''The main honcho - the compiler that travels through time and compiles your commits.'''

  def __init__(self, repo='.', build_directory='./build', **env):
    '''Initialize'''
    self.git_manager = GitManager(repo)
    self.commit_targets = []
    self.compilation_options = dict(build_directory = build_directory)
    self.linking_options = {}
    self.build_directory = os.path.abspath(build_directory)
    os.environ.update(env)

  def add_commit_targets(self, **kwargs):
    '''Add commit targets to compile.''' #TODO think about how to specify commits
    self.commit_targets.extend(self.git_manager.get_commits(**kwargs))

  # TODO remove_commit_targets

  def set_compilation_task(self, task, **kwargs):
    '''Set the compilation task (the thing that'll compile each commit)'''
    self.compilation_task = task
    self.compilation_options = kwargs or self.compilation_options

  def set_linking_task(self, task, **kwargs):
    '''Set the linking task (the thing that'll link the outputs of the compilation task)'''
    self.linking_task = task
    self.linking_options = kwargs or self.linking_options

  def compile(self, link=True):
    '''Compile (and link unless specified otherwise)! 
       (Works inside the root of the repo)
       TODO: Thread this out with an observer to output progress.
    '''
    current_directory = os.getcwd()
    os.chdir(self.git_manager.repo.working_dir)
    self.compilation_output = self.compilation_task(self.commit_targets, self.compilation_options)
    if link: 
      self.link(self.compilation_output)
    os.chdir(current_directory)

  def link(self, compilation_output):
    '''Link compilation output!'''
    self.linking_task.perform(compilation_output, self.linking_options)

