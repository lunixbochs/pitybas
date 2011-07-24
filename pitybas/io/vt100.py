from pitybas.parse import Parser
from pitybas.common import ParseError

class IO:
	def __init__(self, vm):
		self.vm = vm

	def clear(self):
		raise NotImplementedError

	def input(self, msg, is_str=False):
		while True:
			try:
				line = self.complicated_input_routine()

				if not is_str:
					val = Parser.parse_line(self.vm, line)
				else:
					val = line

				return val
			except ParseError:
				print 'ERR:DATA'
				print

	def output(self, x, y, msg):
		raise NotImplementedError

	def disp(self, msg=''):
		raise NotImplementedError
	
	def pause(self, msg=''):
		raise NotImplementedError
	
	def menu(self, menu):
		raise NotImplementedError
