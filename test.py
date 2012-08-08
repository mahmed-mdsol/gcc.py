from gcc.git_compiler import *
from gcc.tasks.task import CompilationTask
from gcc.util import find_files
from png_movie_linker import PngMovieLinker
import subprocess
import os
import colorama
colorama.init()

compiler = GitCompiler('../balance', RAILS_ENV='test')

columbo = os.path.abspath('rb/columbo.rb')

#Scenario Samples:
scenarios = ",".join([
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
])

print "Scenarios to execute:", scenarios

def cucumber(task_input, options):
  return "bundle exec cucumber -r {0} --format=pretty --format=Shamus::Columbo --out {1} -r features/support/default_selenium.rb -t {2}".format(columbo, options['output_directory'], scenarios)



# tags = ['balance-release-2011.1.0']#sorted(map(lambda t: str(t), compiler.git_manager.repo.tags))[-6:] #map(lambda t: t.commit, compiler.git_manager.repo.tags)
# print "Tags (", len(tags), "):", tags

# compiler.add_commit_targets(refs=tags)

i = -1
def filter_function(commit):
  global i
  i = (i + 1) % 20
  return compiler.git_manager.PULL_REQUEST_FILTER(commit) and i == 0


compiler.add_commit_targets(from_ref='balance-pre-release-2011.4.0', to_ref='develop', filter_function=filter_function)

class CucumberScreenshots(CompilationTask):

  def precompilation(self):
    self.failed_commits = []
    subprocess.call("""     
        bundle install
        RAILS_ENV=test bundle exec rake db:drop db:create --trace
      """, shell=True, cwd='../balance')
    CompilationTask.precompilation(self)

  def perform(self, commit_targets, *args, **kwargs):
    commit_targets.sort(key=lambda c: c.committed_date)
    return CompilationTask.perform(self, commit_targets, *args, **kwargs)

  def compile(self, commit):
    if len(os.listdir(self.output_directory_for(commit))) == 0:
      self.log("Prepping working directory")
      log_file = os.path.join(self.output_directory_for(commit), "compilation.log")
      output_log = open(log_file, 'w')
      self.log("Output in {0}".format(log_file))
      popen_options = dict(shell=True, stdout=output_log, stderr=subprocess.STDOUT, cwd = self.git_manager.repo.working_dir)
      subprocess.call("""
        # source ~/.bash_profile
        # rvm use 1.8.7-p174
        cd ..
        cd -
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
      except Exception as e:
        self.log(colorama.Fore.RED + 'Cuke fail. :( [{0}]'.format(repr(e)) + colorama.Fore.RESET)
        self.failed_commits.append(commit)
      subprocess.call("""
        git clean -f -d
        for f in *; do git checkout $f; done
        """, **popen_options)
    else:
      self.log("Not recompiling commit; there's already stuff here!")

    return list(find_files(self.output_directory_for(commit), "*.png"))

compiler.set_compilation_task(CucumberScreenshots())
compiler.set_linking_task(PngMovieLinker('movieMod20.mp4', audio="audio/new_soul.mp3", framerate=3), date_order=True)

compiler.compile(link = True, in_order = True)

