from task import CompilationTask
import os
import datetime

class CommitSummary(CompilationTask):
	# TODO support customization

	def compile(self, commit):
		filename = os.path.join(self.output_directory_for(commit),'commit_summary.txt')
		self.log("Writing commit summary to " + filename)
		f = open(filename, 'w')
		print >> f, "Commit:", commit
		print >> f, "Author:", commit.author, "<", commit.author.email, ">"
		print >> f, "Date:", str(datetime.datetime.fromtimestamp(commit.committed_date))
		print >> f, "Impact:", str(commit.stats.total)
		print >> f, "Files:", str(commit.stats.files)
		f.close()
		self.log("Finished writing commit summary.")
