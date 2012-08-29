from gcc.git_compiler import *
from gcc.tasks.task import CompilationTask, LinkingTask
from gcc.util import find_files
from png_movie_linker import PngMovieLinker
import subprocess
import os
import colorama
import sys
colorama.init()

#######################################################################################################################
## CONFIGS ##
#######################################################################################################################
REPO = len(sys.argv) and sys.argv[1] or '../balance_gcc'
ENV = dict(RAILS_ENV='test')
COLUMBO = 'rb/columbo.rb'

#Scenario Samples:
SCENARIOS = [
  "@PB1448-014", #Wizard
  "@PB080-003", # Rand Design Page
  "@PB1406-006b", # Switch to Block
  "@PB058-026", # Treatment Page
  "@PB1417-026", # Treatment Schedule
  #"@PB117-104", # Simulation
  "@PB057-051", # Sites/Subjects
  "@PB063-066", # Items Page
  "@PB074-111a", # Item Manage
  "@PB6675-002", # Field Mapper 
  "@PB6675-010b", # Field Mapping
  "@PB10322-001", # Block upload
  "@PB10406-008", # Rand Block List Page
  "@PB039-903" # Audit
]

COMMIT_TARGETS = dict(from_ref='balance-pre-release-2011.4.0', to_ref='develop')

# Whether or not to only look at PR merge commits
FILTER_BY_PR = True

# Look at every N commits
SKIP_AMOUNT = 20

# Whether or not the movie should show progression per scenario vs total progression over time
PER_SCENARIO_PROGRESSION = True

FRAME_RATE = 3
MOVIE_FILE = 'movieMod20.mp4'
AUDIO_FILE = 'audio/new_soul.mp3'


#######################################################################################################################
## COMPILER PREP ##
#######################################################################################################################
compiler = GitCompiler(REPO, **ENV)
columbo = os.path.abspath(COLUMBO)
scenarios = ",".join(sorted(SCENARIOS, key=lambda pb: int(pb[3:pb.find('-')]))) #Sorted by PB major number


print "Scenarios to execute:", scenarios

def cucumber(task_input, options):
  return "bundle exec cucumber --expand -r {0} --format=pretty --format=Shamus::Columbo --out {1} -r features/support/default_selenium.rb -t {2}".format(columbo, options['output_directory'], scenarios)

# tags = ['balance-release-2011.1.0']#sorted(map(lambda t: str(t), compiler.git_manager.repo.tags))[-6:] #map(lambda t: t.commit, compiler.git_manager.repo.tags)
# print "Tags (", len(tags), "):", tags

# compiler.add_commit_targets(refs=tags)

i = -1
def filter_function(commit):
  global i
  if FILTER_BY_PR:
    consider_it = compiler.git_manager.PULL_REQUEST_FILTER(commit)
  else:
    consider_it = True

  if consider_it:
    i = (i + 1) % SKIP_AMOUNT
    return i == 0
  else:
    return False

COMMIT_TARGETS.update(filter_function=filter_function)
compiler.add_commit_targets(**COMMIT_TARGETS)


#######################################################################################################################
## Custom Task Classes ##
#######################################################################################################################

class CucumberScreenshots(CompilationTask):

  def precompilation(self):
    self.failed_commits = []
    '''
    subprocess.call("""
        bundle install
        RAILS_ENV=test bundle exec rake db:drop db:create --trace
      """, shell=True, cwd='../balance')
    '''
    CompilationTask.precompilation(self)

  def perform(self, commit_targets, *args, **kwargs):
    commit_targets.sort(key=lambda c: c.committed_date)
    return CompilationTask.perform(self, commit_targets, *args, **kwargs)

  def all_pb_directories_exist(self, output_directory):
    '''Return True only if a PB directory exists for all PBs in SCENARIOS and the directory isn't empty'''
    for pb in SCENARIOS:
      scenario_dir = os.path.join(output_directory, pb[1:])
      if not os.path.isdir(scenario_dir) or len(os.listdir(scenario_dir)) == 0:
        return False
    return True

  def should_compile(self, commit):
    '''We should compile this commit only if we haven't compiled it before or we don't have all the scenario output'''
    output_directory = self.output_directory_for(commit)
    return not os.path.isdir(output_directory) or len(os.listdir(output_directory)) == 0 or self.has_incomplete_output_for(commit) #or not self.all_pb_directories_exist(output_directory)

  def should_checkout(self, commit):
    '''Returns True since we need commits to be checked out to run cucumber on them!'''
    return True

  def should_do_forceful_checkouts(self):
    '''Returns True to start off with a "fresh" working state.'''
    return True

  def should_create_output_directory(self):
    '''Returns True since we need an output directory to store screenshots!'''
    return True

  def existing_output_for(self, commit):
    return list(find_files(self.output_directory_for(commit), "*.png"))

  def print_failed_commits(self):
    self.log("Failed Commits:\n" + "\n".join([str(commit) for commit in self.failed_commits]))

  handle_interrupt = print_failed_commits
  postcompilation  = print_failed_commits

  def compile(self, commit):
    '''
    self.log("Prepping working directory")
    log_file = os.path.join(self.output_directory_for(commit), "compilation.log")
    output_log = open(log_file, 'w')
    self.log("Output in {0}".format(log_file))
    popen_options = dict(shell=True, stdout=output_log, stderr=subprocess.STDOUT, cwd = self.git_manager.repo.working_dir)
    subprocess.call("""
      cd ..
      cd - # Trigger rvmrc if there is one.
      export RAILS_ENV=test

      cp config/database.yml.sample config/database.yml

      git checkout Gemfile
      git checkout Gemfile.lock
      rm -rf vendor/plugins
      rm -rf public
      git checkout vendor
      git checkout public
      git submodule update --init
      git clean -f -d

      #cp config/database.yml.sample config/database.yml
      bundle install

      # RAILS_ENV=test bundle exec rake db:drop db:create --trace

      RAILS_ENV=test bundle exec rake db:migrate --trace
      RAILS_ENV=test bundle exec rake db:seed --trace
    """, **popen_options)
    self.log("Done prepping")
    self.log("Cuking!")
    try:
      subprocess.check_call(cucumber(None, dict(output_directory = self.output_directory_for(commit))), **popen_options)
      self.log(colorama.Fore.GREEN + 'Successfully cuked!' + colorama.Fore.RESET)
      try:
        os.remove(self.incomplete_compilation_file(commit))
      except:
        pass
    except Exception as e:
      self.log(colorama.Fore.RED + 'Cuke fail. :( [{0}]'.format(repr(e)) + colorama.Fore.RESET)
      self.mark_incomplete(commit, e)
      self.failed_commits.append(commit)
  '''
    return self.existing_output_for(commit)

class PerScenarioMovieLinker(LinkingTask):

  def link(self, compilation_output, linking_options):
    commits = compilation_output.keys()
    commits.sort(key=lambda c: c.committed_date)

    def make_video(scenario):
      c = {}
      for commit in commits:
        c[commit] = [f for f in (compilation_output[commit] or []) if f.find(scenario[1:]) >= 0]

      p = PngMovieLinker('{0}.mp4'.format(scenario[1:]), framerate=FRAME_RATE)
      p.link(c, dict(date_order=True, frames_directory=scenario[1:]))


    # Thread out the making of each video
    import threading
    threads = []
    for scenario in SCENARIOS:
      threads.append(threading.Thread(target=make_video, args=(scenario,)))

    for thread in threads:
      thread.start()

    # Wait for the threads to finish.
    self.log("Started {0} threads".format(len(threads)))
    self.log("Waiting to join")

    for thread in threads:
      thread.join()

    self.log("Joined! :D")

    # Now join the intermediate videos together.
    output_frames_directory = 'ps_images'
    if not os.path.isdir(output_frames_directory):
      os.makedirs(output_frames_directory)

    i = 0
    image_format = os.path.join(output_frames_directory, "image%08d.png")

    for scenario in scenarios.split(','):
      for f in os.listdir(scenario[1:]):
        subprocess.check_call('cp {0} {1}'.format(os.path.join(scenario[1:], f), image_format % i), shell=True)
        i += 1

    cmd = "ffmpeg -qscale 5 -i {0} {1} -vf scale=\"854:trunc(ow/a/2)*2\" -r {2} {3}".format(image_format, AUDIO_FILE and ("-i " + AUDIO_FILE) or "", FRAME_RATE, MOVIE_FILE)
    
    self.log("Linking videos with {0}".format(cmd))
    subprocess.check_call(cmd, shell=True)

#######################################################################################################################
## THE MOMENT OF TRUTH ##
#######################################################################################################################

compilation_task = CucumberScreenshots()
linking_task = PER_SCENARIO_PROGRESSION and PerScenarioMovieLinker() or PngMovieLinker(MOVIE_FILE, audio=AUDIO_FILE, framerate=FRAME_RATE)

compiler.set_compilation_task(compilation_task, in_order = True)
compiler.set_linking_task(linking_task, date_order=True)

compiler.compile(link = True)

