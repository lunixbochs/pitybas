from parse import Parser
from tokens import EOF, Value
from common import ExecutionError

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
		self.running = []

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

	def push_block(self, block=None):
		if not block and self.running:
			block = self.running[-1]

		if block:
			self.blocks.append(block)
		else:
			raise ExecutionError('tried to push an invalid block to the stack')

	def pop_block(self):
		if self.blocks:
			return self.blocks.pop()
		else:
			raise ExecutionError('tried to pop an empty block stack')
	
	def find(self, *types, **kwargs):
		if 'wrap' in kwargs:
			wrap = kwargs['wrap']
		else:
			wrap = False
		
		def y(i):
			line = self.code[i]
			if line:
				for t in types:
					cur = line[0]
					if isinstance(cur, t):
						return i, 0, cur

		for i in xrange(self.line, len(self.code)):
			ret = y(i)
			if ret: yield ret
		
		if wrap:
			for i in xrange(0, self.line):
				ret = y(i)
				if ret: yield ret
	
	def goto(self, row, col):
		if row >= 0 and row < len(self.code)\
			and col >= 0 and col < len(self.code[row]):
				self.line = row
				self.col = col
		else:
			raise ExecutionError('cannot goto (%i, %i)' % (row, col))

	def run(self, cur):
		if cur.can_run:
			self.running.append((self.line, self.col, cur))
			self.inc()
			cur.run(self)
			self.running.pop()
		elif cur.can_get:
			self.inc()
			self.set_var('Ans', cur.get(self))
		else:
			raise ExecutionError('cannot seem to run token: %s' % cur)


	def execute(self):
		while not isinstance(self.cur(), EOF):
			cur = self.cur()
			self.run(cur)
