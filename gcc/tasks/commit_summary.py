from task import CompilationTask
import os
import datetime

class CommitSummary(CompilationTask):
	# TODO support customization
	def should_checkout(self, commit):
		return False

	def get_output_stream_for(self, commit):
		filename = os.path.join(self.output_directory_for(commit),'commit_summary.txt')
		self.log("Writing commit summary to " + filename)
		return open(filename, 'w')

	def write_commit_details(self, commit, f):
		print >> f, "Commit:", commit
		print >> f, "Author:", commit.author, "<", commit.author.email, ">"
		print >> f, "Date:", str(datetime.datetime.fromtimestamp(commit.committed_date))
		print >> f, "Impact:", str(commit.stats.total)
		print >> f, "Files:", str(commit.stats.files)

	def output_value(self, f):
		return f.name

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


if __name__ == '__main__':
	from gcc.git_compiler import GitCompiler
	compiler = GitCompiler('.')
	compiler.add_commit_targets(rev='master')
	compiler.set_compilation_task(CommitSummary())
	compiler.compile(link=False)
