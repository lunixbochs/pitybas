import tokens
from common import ExecutionError, ExpressionError, Pri, test_number

class Base:
	priority = Pri.NONE

	can_run = False
	can_set = False
	can_get = True
	absorbs = ()

	def __init__(self):
		self.tokens = []
		self.finished = False
	
	def append(self, token):
		if self.tokens:
			# implied multiplication
			if self.tokens[-1].priority == token.priority == tokens.Pri.NONE:

				# negative numbers actually have implied addition
				if isinstance(token, tokens.Value)\
					and test_number(token.value) and int(token.value) < 0:
						self.tokens.append(tokens.Plus())
				else:
					self.tokens.append(tokens.Mult())

		self.tokens.append(token)
	
	def extend(self, array):
		for x in array:
			self.append(x)
	
	def flatten(self):
		if len(self.tokens) == 1:
			first = self.tokens[0]
			if isinstance(first, Expression):
				return first.flatten()
			elif first.can_get:
				return first
		
		return self

	def fill(self):
		# TODO: instead of this system, perhaps tokens should be able to specify whether they need/want left/right params
		if not self.tokens: return

		# if we don't have a proper variable:token:variable pairing in the token list,
		# this method will allow tokens to fill in an implied variable to their left or right
		new = []
		for i in xrange(len(self.tokens)):
			t = self.tokens[i]
			if (i % 2 == 0 and not t.can_get):
				left = None
				right = None

				if i > 0:
					left = self.tokens[i-1]
					if not left.can_fill_right:
						left = None

				right = self.tokens[i]
				if not right.can_fill_left:
					right = None

				if left is not None and right is not None:
					if left < right:
						left = None
					else:
						right = None

				if left is not None:
					new.append(left.fill_right())
				elif right is not None:
					new.append(right.fill_left())

			new.append(t)

		last = new[-1]
		if not last.can_get:
			if last.can_fill_right:
				new.append(last.fill_right())

		self.tokens = new

	def validate(self):
		if not self.tokens: return

		# figure out how to handle in-place tokens like the symbol for ^3
		# perhaps replace it with a ^3 so we can enforce (value, token, value)
		# or we can pad "in-place" tokens with a null to be passed as right

		# make sure expression is ordered (value, token, value, token, value)
		for i in xrange(len(self.tokens)):
			t = self.tokens[i]
			
			if (i % 2 == 0 and not t.can_get) or ( i % 2 == 1 and not t.can_run):
				raise ExpressionError('bad token order: %s' % self)

		# determine whether we have any tokens after a ->
		found_stor = False
		for i in xrange(len(self.tokens)):
			t = self.tokens[i]
			odd = i % 2

			if isinstance(t, tokens.Store):
				found_stor = True
				stor_odd = odd
			elif found_stor and (odd == stor_odd):
				raise ExpressionError('Store cannot be followed by non-Store tokens in expression: %s' % self)
	
	def order(self):
		# this step returns a list of ordered indicies
		# to help reduce tokens to a single value
		# see common.Pri for an ordering explanation

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
		self.fill()
		self.validate()

		sub = []
		expr = self.tokens[:]
		for i in self.order():
			n = 0
			for s in sub:
				if s < i:
					n += 1

			sub += [i, i+1]
			i -= n

			right = expr.pop(i+1)
			left = expr.pop(i-1)
			
			token = expr[i-1]
			expr[i-1] = tokens.Value(token.run(vm, left, right))

		return vm.get(expr[0])
	
	def finish(self):
		self.finished = True
	
	def __len__(self):
		return len(self.tokens)

	def __repr__(self):
		return 'E(%s)' % (' '.join(repr(token) for token in self.tokens))

bracket_map = {'(':')', '{':'}', '[':']'}

class Expression(Base): pass

class Bracketed(Base):
	def __init__(self, end):
		self.end = bracket_map[end]
		Base.__init__(self)

class Tuple(Base):
	priority = Pri.INVALID

	def __init__(self):
		self.contents = []
		Base.__init__(self)
	
	def append(self, expr):
		if isinstance(expr, Expression):
			expr = expr.flatten()
		self.contents.append(expr)
	
	def get(self, vm):
		return [vm.get(arg) for arg in self.contents]
	
	def __len__(self):
		return len(self.contents)
	
	def __repr__(self):
		return 'T(%s)' % (', '.join(repr(expr) for expr in self.contents))

class Arguments(Tuple, Bracketed):
	def __init__(self, end):
		self.contents = []
		Bracketed.__init__(self, end)
	
	def __repr__(self):
		return 'A(%s)' % (', '.join(repr(expr) for expr in self.contents))
