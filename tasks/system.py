from tasks import Task
import subprocess
import shlex
import os

class SystemTask(Task):
  
  def __init__(self, command_maker, shell=False, work_in_git_dir=False, stop_on_exception = False, log_stdout=None, log_stderr=None, **task_args): # TODO support STDIN
    '''Initialize the SystemTask.
    command_maker should be a callable object that takes the task input and options and generates a string command to execute
    (
      Note that unless shell = True, this command will not have access to special shell semantics (like pipes or & or >, etc).
      This is because arbitrary shell access is [usually] BAD and inherently dangerous.
    )
    stop_on_exception should be True if compilation should stop if an exception occurs (command returns nonzero status code)
    log_stdout/log_stderr should be set to an object to which stdout/stderr should be sent (instead of the console)
    '''
    Task.__init__(self, **task_args)
    self.command_maker = command_maker
    self.popen_options = {'shell': shell}
    if log_stdout:
      self.popen_options['stdout'] = log_stdout
    if log_stderr:
      self.popen_options['stderr'] = log_stderr
    self.work_in_git_dir = work_in_git_dir
    self.execute = stop_on_exception and subprocess.check_call or subprocess.call

  def get_command(self, task_input, options):
    '''Generate the command to pass to subprocess given the task input and options'''
    return shlex.split(self.command_maker(task_input, options))

  def perform(self, task_input, options={}):
    # TODO SystemCompileTask, SystemLinkTask
    input_is_a_hash = isinstance(task_input, dict) #Linking 
    os.environ.update(options) # add the options to the environment for use by the commands.

    for unit in task_input:
      if input_is_a_hash:
        self.execute(self.get_command(task_input[unit], options)) # linking
      else:
        self.execute(self.get_command(unit, options))

