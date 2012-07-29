from tasks.task import LinkingTask

import subprocess
import os
import shlex
import shutil

class PngMovieLinker(LinkingTask):

	def __init__(self, output_file='movie.mp4', framerate=1, **ffmpeg_dash_args):
		options = dict(r=framerate, vf='scale=\"854:trunc(ow/a/2)*2\"') #dict(qscale=qscale, r=framerate, b=bitrate)
		options.update(ffmpeg_dash_args)
		self.options = options
		self.execute = subprocess.check_call

	@staticmethod
	def generate_ffmpeg_command_with(options, file='movie.mp4'):
		'''Turns ({'qscale': 5, 'r': 30, ...}, file) into "ffmpeg -qscale 5 -r 30 file"'''
		return 'ffmpeg ' + " ".join(map(lambda opt: "-{0} {1}".format(*opt), options.items())) + " {0}".format(file)

	def link(self, compilation_output, linking_options):
		commits = compilation_output.keys()
		output_frames_directory = ('frames_directory' in linking_options) and linking_options['frames_directory'] or 'images'
		
		if not os.path.isdir(output_frames_directory):
			os.makedirs(output_frames_directory)

		self.log("Frames located in {0}".format(output_frames_directory))

		if 'date_order' in linking_options and linking_options['date_order']:
			commits.sort(key=lambda c: c.committed_date)

		format = self.prep_images(commits, compilation_output, output_frames_directory)
		self.options['i'] = format

		command = self.generate_ffmpeg_command_with(self.options) #shlex.split(self.generate_ffmpeg_command_with(self.options))

		self.log("Command: {0}".format(command))

		self.execute(command, shell=True)

		self.log("Completed command.")


	def prep_images(self, commits, compilation_output, frames_directory):
		padsize = 8 # TODO
		image_format = os.path.join(frames_directory, "image%0{0}d.png".format(padsize))
		i = 0
		images = []
		for commit in commits:
			files = compilation_output[commit] or []
			for f in files:
				if f[-3:] == "png":
					shutil.copyfile(f, image_format % i)
					i += 1
		return image_format #os.path.join(frames_directory, '*.png')


if __name__ == '__main__':	
	def find_files(directory, pattern):
	  return subprocess.check_output('find {0} -name "{1}"'.format(directory, pattern), shell=True).split()	# TODO not shell 
	import git
	repo = git.repo.Repo('../balance')
	c = {repo.commit(): find_files('build/ae79f9c4ad312689f2326580e2df0d2a9b16e134/', '*.png')}
	p = PngMovieLinker()
	p.link(c, {})




