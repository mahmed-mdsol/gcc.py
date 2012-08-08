from gcc.tasks import LinkingTask

import subprocess
import os
import shlex
import shutil
import watermark

import Image, ImageFont
from datetime import datetime

class PngMovieLinker(LinkingTask):

	def __init__(self, output_file='movie.mp4', audio=None, framerate=1, ffmpeg_dash_args=""):
		self.ffmpeg_args = ffmpeg_dash_args + " -vf scale=\"854:trunc(ow/a/2)*2\" "
		self.audio = audio
		self.output_file = output_file
		self.framerate = framerate
		self.options = ""
		self.execute = subprocess.check_call

	@staticmethod
	def generate_ffmpeg_command_with(options, file='movie.mp4'):
		'''Turns ({'qscale': 5, 'r': 30, ...}, file) into "ffmpeg -qscale 5 -r 30 file"'''
		#return 'ffmpeg ' + " ".join(map(lambda opt: "-{0} {1}".format(*opt), options.items())) + " {0}".format(file)
		return 'ffmpeg ' + " ".join(options) + " " + file

	def link(self, compilation_output, linking_options):
		self.log("Linking {0} commits, {1} images total.".format(len(compilation_output.keys()), reduce(lambda x, y: x + y, map(lambda a: len(list(a)), compilation_output.values()), 0)))
		commits = compilation_output.keys()
		output_frames_directory = ('frames_directory' in linking_options) and linking_options['frames_directory'] or 'images'
		
		if not os.path.isdir(output_frames_directory):
			os.makedirs(output_frames_directory)

		self.log("Frames located in {0}".format(output_frames_directory))

		if 'date_order' in linking_options and linking_options['date_order']:
			commits.sort(key=lambda c: c.committed_date)

		self.log("Prepping images")
		format = self.prep_images(commits, compilation_output, output_frames_directory)
		self.log("Done prepping")

		options = ["-i {0}".format(format)]
		if self.audio: options.append("-i {0}".format(self.audio))
		options.append(self.ffmpeg_args)
		options.append("-r {0}".format(self.framerate))

		command = self.generate_ffmpeg_command_with(options, self.output_file) #shlex.split(self.generate_ffmpeg_command_with(self.options))

		self.log("Command: {0}".format(command))

		self.execute(command, shell=True)

		self.log("Completed command.")


	def prep_images(self, commits, compilation_output, frames_directory):
		padsize = 8 # TODO
		import re
		p = re.compile("Merge pull request #(\d+)", re.IGNORECASE)
		image_format = os.path.join(frames_directory, "image%0{0}d.png".format(padsize))
		i = 0
		images = []
		font = ImageFont.truetype("HannaHandwriting.ttf", 14)
		
		for commit in commits:
			text = "PR #{0} - {1}".format(p.match(commit.summary) and p.match(commit.summary).group(1) or "N/A", datetime.fromtimestamp(commit.committed_date).strftime("%A, %B %d, %Y"))
			files = compilation_output[commit] or []
			for f in files:
				if f[-3:] == "png":
					image = Image.open(f)
					mark = watermark.write_centered_text(watermark.round_rectangle((275, 50), 10, "grey"), text, color='white', font=font)
					watermark.watermark(image, mark, (image.size[0] - mark.size[0], image.size[1] - mark.size[1]), 0.5).save(image_format % i)
					# shutil.copyfile(f, image_format % i)
					i += 1
		return image_format #os.path.join(frames_directory, '*.png')


scenarios = [
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


def find_files(directory, pattern):
  return subprocess.check_output('find {0} -name "{1}"'.format(directory, pattern), shell=True).split()	# TODO not shell 

def make_scenario_videos(commits=None):
  def make_video(scenario):
    import git
    repo = git.repo.Repo('../balance')
    c = {}
    ds = commits and commits or os.listdir('build')
    for d in ds:
      c[repo.commit(d)] = filter(lambda f: f.find(scenario[1:]) >= 0, list(find_files(os.path.join('build', str(d)), "*.png")))

    # c = {repo.commit(): find_files('oldimages', '*.png')}
    p = PngMovieLinker('{0}.mp4'.format(scenario[1:]), framerate='1')
    p.link(c, dict(date_order=True, frames_directory=scenario[1:]))

  import threading
  threads = []
  for scenario in scenarios:
    threads.append(threading.Thread(target=make_video, args=(scenario,)))

  for thread in threads:
  	thread.start()

  print "Started {0} threads".format(len(threads))
  print "Waiting to join"

  for thread in threads:
  	thread.join()

  print "Joined and done! :D"


if __name__ == '__main__':	
  make_scenario_videos()
#	c = {}
#	for d in os.listdir('build'):
#		c[repo.commit(d)] = filter(lambda f: f.find('PB6675-010b') >= 0, list(find_files(os.path.join('build', d), "*.png")))
#
#	# c = {repo.commit(): find_files('oldimages', '*.png')}
#	p = PngMovieLinker('test2.mp4', 'audio/new_soul.mp3', '1')
#	p.link(c, dict(date_order=True))




