import colorama
colorama.init()

class Logger(object):

	@staticmethod
	def log(src, message, tag="INFO", term_color="", term_bg=""):
		print term_bg + term_color + ""

