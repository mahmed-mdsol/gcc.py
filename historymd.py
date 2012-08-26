import re
from gcc.tasks.task import CompilationTask, LinkingTask
from collections import defaultdict

class PRCollect(CompilationTask):
  def __init__(self):
    self.pr_title = re.compile('Merge pull request (#\d+) from .+\n\n(.+)', re.DOTALL)
    self.tag = re.compile('([\d\.]+)')
    CompilationTask.__init__(self)

  def describe(self, commit):
    try:
      return self.git_manager.git.describe(commit, contains=True)
    except:
      return None

  def should_checkout(self, commit):
    # We don't need to checkout the commit to gather info about it, so always return False.
    return False

  def should_ignore_exception(self, e):
    # Sure, why not, I don't really care. :P
    return True

  def should_create_output_directory(self):
    # We don't need to write out output for this task
    return False

  def compile(self, commit):
    pr_match = self.pr_title.match(commit.message)
    tag_match = self.tag.findall(self.describe(commit) or "")
    title = None
    tag = tag_match and tag_match[0] or None
    if pr_match:
      title = "{0} - {1}".format(pr_match.group(1).encode('utf-8'), pr_match.group(2).encode('utf-8'))
    self.log("Tag matched: {0}".format(tag))
    return (tag, title)

class HistoryMDLinker(LinkingTask):
  def __init__(self):
    LinkingTask.__init__(self)

  def link(self, compilation_output, linking_options):
    history_file = open('History.md', 'w')
    self.log("Writing History.md")
    try:
      commits = compilation_output.keys()
      commits.sort(key=lambda c: -c.committed_date) # newest first
      release_history = defaultdict(list)
      for commit in commits:
        tag, title = compilation_output[commit]
        if tag and title:
          release_history[tag].append(title)
        else:
          self.log("Not writing tag: {0} title: {1}".format(tag, title))
      tags = sorted(release_history.keys())
      tags.reverse()
      for tag in tags:
        print >> history_file, "\n{0}\n========".format(tag)
        for title in release_history[tag]:
          print >> history_file, "* {0}".format(title)
          self.log("Wrote {0} for {1}".format(title, tag))
    finally:
      history_file.close()

if __name__ == '__main__':
  from gcc.git_compiler import GitCompiler
  import sys
  compiler = GitCompiler(len(sys.argv) > 1 and sys.argv[1] or ".") # Take the first argument as the repo path or assume the current directory is the repo if no args are provided.
  git = compiler.git_manager
  compiler.add_commit_targets(from_ref=git.first_commit, to_ref=git.last_commit, filter_function=git.PULL_REQUEST_FILTER)
  compiler.set_compilation_task(PRCollect())
  compiler.set_linking_task(HistoryMDLinker())
  compiler.compile()


