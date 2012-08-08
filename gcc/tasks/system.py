from gcc.tasks.task import CompilationTask, LinkingTask
import os
import shlex
import subprocess
import sys
from gcc.util import find_files

class SystemTask(object):
  
  def __init__(self, command_maker, shell=False, work_in_git_dir=False, stop_on_exception = False, log_stdout=None, log_stderr=None): # TODO support STDIN
    '''Initialize the SystemTask.
    command_maker should either be a callable object that takes the task input and options and generates a string command to execute
                  or a static string representing the command to execute
    (
      Note that unless shell = True, this command will not have access to special shell semantics (like pipes or & or >, etc).
      This is because arbitrary shell access is [usually] BAD and inherently dangerous.
    )
    stop_on_exception should be True if compilation should stop if an exception occurs (command returns nonzero status code)
    log_stdout/log_stderr should be set to an object to which stdout/stderr should be sent (instead of the console)
    '''
    self.command_maker = isinstance(command_maker, str) and (lambda *args: command_maker) or command_maker
    self.popen_options = {'shell': shell}
    if log_stdout:
      self.popen_options['stdout'] = log_stdout
    if log_stderr:
      self.popen_options['stderr'] = log_stderr
    self
    self.work_in_git_dir = work_in_git_dir
    self.stop_on_exception = stop_on_exception
    self.execute = subprocess.check_call

  def get_command(self, task_input, options):
    '''Generate the command to pass to subprocess given the task input and options'''
    cmd = self.command_maker(task_input, options)
    return self.popen_options['shell'] and cmd or shlex.split(self.command_maker(task_input, options))

class SystemCompilationTask(CompilationTask, SystemTask):

  # TODO this is horrible. You call yourself a programmer? 
  # Implement event observers for tasks instead.
  def __init__(self, precompilation_commands = [], precompile_commands = [], postcompile_commands = [], postcompilation_commands = [], *args, **kwargs):
    CompilationTask.__init__(self)
    SystemTask.__init__(self, *args, **kwargs)
    self.precompilation_commands = precompilation_commands
    self.precompile_commands = precompile_commands
    self.postcompile_commands = postcompile_commands
    self.postcompilation_commands = postcompilation_commands

  def mark_incomplete_on_fail(f):
    '''Decorator to mark a commit compilation task incomplete if an exception was raised.'''
    def wrapped(self, commit, *args, **kwargs):
      try:
        f(self, commit, *args, **kwargs) # Call the wrapped function
      except Exception as e:
        self.mark_incomplete(commit, e)
        if self.stop_on_exception:
          raise
        else:
          self.log("Exception ignored: {0}\n".format(repr(e)))
    return wrapped

  def precompilation(self):
    if self.work_in_git_dir:
      self.popen_options.update(cwd = self.git_manager.repo.working_dir)
    if 'in_order' in self.options:
      self.targets.sort(key=lambda c: c.committed_date) # sort by committed date if commits should be compiled in_order
    self.execute_all(self.precompilation_commands)

  def execute_all(self, commands):
    for command in commands:
      self.execute(command, **self.popen_options)

  def should_compile(self, commit):
    '''Compile if there is no output directory for the commit or if the compilation is incomplete.'''
    return not os.path.isdir(self.output_directory_for(commit)) or self.has_incomplete_output_for(commit)

  @mark_incomplete_on_fail
  def precompile(self, commit):
    CompilationTask.precompile(self, commit)
    self.options.update(output_directory = self.output_directory_for(commit))
    self.execute_all(self.precompile_commands)

  @mark_incomplete_on_fail
  def compile(self, commit):
    self.execute(self.get_command(commit, self.options), **self.popen_options)
    return find_files(self.output_directory_for(commit), '*')

  def __call__(self, targets, options, git_manager, *args, **kwargs):
    ''':[ This is terrible. You're an awful programmer.'''
    self.targets, self.options, self.git_manager = targets, options, git_manager
    CompilationTask.__call__(self, targets, options, git_manager, *args, **kwargs)

  @mark_incomplete_on_fail
  def postcompile(self, commit):
    self.execute_all(self.postcompile_commands)

  def postcompilation(self):
    self.execute_all(self.postcompilation_commands)



