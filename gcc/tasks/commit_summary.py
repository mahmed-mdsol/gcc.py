from task import CompilationTask, LinkingTask
import os
import datetime

class CommitSummary(object):
  # TODO support customization

  def __init__(self, output_to_files=False):
    '''If output_to_files is True, a commit_summary.txt file will be created in the output_directory_for each commit.'''
    self.output_to_files = output_to_files

  def should_checkout(self, commit):
    return False

  def should_create_output_directory(self):
    # Create directories only if we want to output to files.
    return self.output_to_files

  def get_output_stream_for(self, commit):
    if self.output_to_files:
      filename = os.path.join(self.output_directory_for(commit),'commit_summary.txt')
      self.log("Writing commit summary to " + filename)
      f = open(filename, 'w')
    else:
      from StringIO import StringIO
      f = StringIO()
    return f

  def write_commit_details(self, commit, f):
    print >> f, "Commit:", commit
    print >> f, "Author:", commit.author, "<", commit.author.email, ">"
    print >> f, "Date:", str(datetime.datetime.fromtimestamp(commit.committed_date))
    print >> f, "Impact:", str(commit.stats.total)
    print >> f, "Files:", str(commit.stats.files)

  def output_value(self, f):
    if self.output_to_files:
      return f.name #File handle
    else:
      return f.getvalue() #StringIO

  def compile(self, commit):
    f = self.get_output_stream_for(commit)
    output_val = None
    try:
      self.write_commit_details(commit, f)
      output_val = self.output_value(f)
    finally:
      f.close()
    self.log("Finished writing commit summary for {0}".format(commit))
    return output_val

  def link(self, compilation_output, linking_options):
    '''Combine all the commit summaries into a single commit summary report.'''
    commits = compilation_output.keys()
    commits.sort(key=lambda c: c.committed_date) # TODO abstract this since this is something that would be commonly done.
    with open('commit_summary_report.txt', 'w') as report:
      for commit in commits:
        output = compilation_output[commit]
        if self.output_to_files:
          with open(output, 'r') as output_file:
            output = output_file.read()
        print >> report, "-------------------"
        print >> report, output
        print >> report, "-------------------"


if __name__ == '__main__':
  from gcc.git_compiler import GitCompiler
  compiler = GitCompiler('.')
  compiler.add_commit_targets(rev='master')
  commit_summary = CommitSummary()
  compiler.set_compilation_task(CompilationTask(commit_summary))
  compiler.set_linking_task(LinkingTask(commit_summary))
  compiler.compile(link=True)
