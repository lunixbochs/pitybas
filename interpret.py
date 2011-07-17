from parse import Parser
from tokens import EOF, Value, Pri

class Expression:
	priority = Pri.NONE

	can_run = False
	can_set = False
	can_get = True
	can_call = False

	def __init__(self):
		self.tokens = []
	
	def append(self, token):
		self.tokens.append(token)
	
	def extend(self, array):
		for x in array:
			self.append(x)
	
	def flatten(self):
		if len(self.tokens) == 1:
			first = self.tokens[0]
			if isinstance(first, Expression):
				return first.flatten()
		
		return self
	
	def fill(self):
		pass
		# TODO: fill implied multiplication symbols
		# TODO: test on a calc to see how functions
		# respond to implied mult
	
	def order(self):
		# this step returns a list of ordered indicies
		# to help reduce tokens to a single value
		# see tokens.Pri for an ordering explanation
		self.fill()

		order = {}

		for i in xrange(len(self.tokens)):
			token = self.tokens[i]
			p = token.priority
			if p >= 0:
				# anything below zero is to be ignored
				if p in order:
					order[p].append(i)
				else:
					order[p] = [i]
		
		ret = []
		for p in order:
			ret += order[p]
		
		return ret
	
	def get(self, vm):
		sub = []
		
		expr = self.tokens[:]
		for i in self.order():
			n = 0
			for s in sub:
				if s < i:
					n += 1

			sub += [i, i+1]
			i -= n

			right = expr.pop(i+1).get(vm)
			left = expr.pop(i-1).get(vm)
			
			token = expr[i-1]
			expr[i-1] = Value(token.run(left, right))
		# TODO: set Ans here if appropriate

		return expr[0].get(vm)

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
		self.vars[var] = value
		return value

	def run(self):
		while not isinstance(self.cur(), EOF):
			cur = self.cur()
			if cur.can_run:
				self.inc()
				cur.run(self)
			elif cur.can_get:
				self.set_var('Ans', cur.get(self))
			else:
				print cur.run