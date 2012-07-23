
class Task(object):

	def __init__(self, pre_task = None, post_task = None):
		if pre_task: self.pre_task = pre_task
		if post_task: self.post_task = post_task

	def pre_task(self, *args):
		pass

	def perform(*args):
		pass

	def post_task(self, *args):
		pass

	def __call__(self, *args):
		self.pre_task(*args)
		self.result = self.perform(*args)
		self.post_task(*args)

class CompilationTask(Task):

	def __init__(self):
		Task.__init__(self, self.precompilation, self.postcompilation)

	def precompilation(self):
		pass

	def precompile(commit):
		pass

	def compile(self, commit):
		return None

	def postcompile(self, commit):
		pass

	def postcompilation(self):
		pass

	def perform(self, commit_targets, compilation_options):
		self.targets = commit_targets
		self.options = compilation_options
		results = {}

		for commit in commit_targets:
			self.precompile(commit)
			results[commit] = self.compile(commit)
			self.postcompile(commit)

		return results

class LinkingTask(Task):

	def __init__(self):
		Task.__init__(self, self.prelinkage, self.postlinkage)

	def prelinkage(self):
		pass

	def link(self, compilation_output, linking_options):
		return None

	def postlinkage(self):
		pass

	def perform(self, compilation_output, linking_options):
		self.compilation_output = compilation_output
		self.linking_options = linking_options

		self.prelinkage()
		result = self.link(compilation_output, linking_options)
		self.postlinkage()

		return result


def CompositeTask(Task):
	def __init__(self, pre_task = None, post_task = None, *tasks):
		self.tasks = tasks
		Task.__init__(self, pre_task, post_task)

	def perform(self, *args):
		output = []
		for task in self.tasks:
			output.append(task.perform(*args))
		return output

