from parse import Parser
from tokens import EOF, Value

class Interpreter:
	@classmethod
	def from_string(cls, string):
		code = Parser(string).parse()
		return Interpreter(code)
	
	@classmethod
	def from_file(cls, filename):
		string = open(filename, 'r').read().decode('utf8')
		return Interpreter.from_string(string)

	def __init__(self, code):
		self.code = code
		self.code.append([EOF()])
		self.line = 0
		self.col = 0
		self.expression = None
		self.blocks = []

		self.vars = {}
	
	def cur(self):
		return self.code[self.line][self.col]

	def inc(self):
		self.col += 1
		if self.col >= len(self.code[self.line]):
			self.col = 0
			return self.inc_row()

		return self.cur()

	def inc_row(self):
		self.line = min(self.line+1, len(self.code)-1)
		self.expression = None
		return self.cur()
	
	def get_var(self, var):
		return self.vars[var]
	
	def set_var(self, var, value):
		if isinstance(value, Value):
			value = value.get(self)

		self.vars[var] = value
		return value

	def run(self):
		while not isinstance(self.cur(), EOF):
			cur = self.cur()
			if cur.can_run:
				self.inc()
				cur.run(self)
			elif cur.can_get:
				self.inc()
				self.set_var('Ans', cur.get(self))
			else:
				print cur.run