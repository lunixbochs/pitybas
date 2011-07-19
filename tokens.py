# -*- coding: utf-8 -*-
import string, math
import expression
from common import Pri

# helpers

def add_class(name, *args, **kwargs):
	globals()[name] = type(name, args, kwargs)

# decorators

def get(f):
	def run(self, vm, left, right):
		return f(self, vm, left.get(vm), right.get(vm))
	
	return run

# magic classes

class Tracker(type):
	def __new__(self, name, bases, attrs):
		if not 'token' in attrs:
			attrs['token'] = name
		
		attrs.update({
			'can_run': False,
			'can_get': False,
			'can_set': False,
		})

		cls = type.__new__(self, name, bases, attrs)

		if 'run' in dir(cls):
			cls.can_run = True
		
		if 'get' in dir(cls):
			cls.can_get = True
		
		if 'set' in dir(cls):
			cls.can_set = True
		
		return cls

	def __init__(cls, name, bases, attrs):
		if bases:
			bases[-1].add(cls, name, attrs)

class InvalidOperation(Exception):
	pass

class Parent:
	__metaclass__ = Tracker

	@classmethod
	def add(cls, sub, name, attrs):
		if 'token' in attrs:
			name = attrs['token']
		
		if name and not cls == Parent:
			cls.tokens[name] = sub
	
	can_run = False
	can_get = False
	can_set = False
	absorbs = ()
	arg = None

	# used for evaluation order inside expressions
	priority = Pri.INVALID

	def absorb(self, token):
		self.arg = token
		self.absorbs = ()

	def __repr__(self):
		return self.token

class Stub:
	@classmethod
	def add(cls, sub, name, attrs): pass

class Token(Parent):
	tokens = {}

	def run(self, vm):
		raise NotImplementedError
	
	def __repr__(self):
		if self.arg:
			return '%s %s' % (self.token, self.arg)
		else:
			return self.token

class StubToken(Token, Stub):
	def run(self, vm): pass

class Variable(Parent):
	priority = Pri.NONE
	tokens = {}

	def get(self, vm):
		raise NotImplementedError

class Function(Parent):
	priority = Pri.NONE
	tokens = {}

	absorbs = (expression.Arguments,)

	@classmethod
	def add(cls, sub, name, attrs):
		if 'token' in attrs:
			name = attrs['token']
		
		if name:
			name += '('
			cls.tokens[name] = sub

	def __init__(self):
		self.args = ()
		if self.run:
			self.priority = Pri.INVALID

		Parent.__init__(self)

	def get(self, vm):
		raise NotImplementedError
	
	def set_args(self, args):
		self.args = args
	
	def __repr__(self):
		if self.arg:
			return '%s%s' % (self.token, repr(self.arg).replace('A', '', 1))
		else:
			return '%s()' % self.token

class StubFunction(Function, Stub):
	def call(self, vm): pass

# token definitions

class EOF(Token, Stub):
	def run(self, vm):
		vm.done()

class Const(Variable, Stub):
	def __init__(self, value):
		super(Const, self).__init__()
		self.value = value

	def get(self, vm):
		return self.value

class If(Token):
	def run(self, vm):
		@vm.block
		def run(b):
			if b.true():
				b.run()
			else:
				b.skip()

class While(Token):
	def run(self, vm):
		@vm.block
		def run(b):
			if b.true():
				while b.true():
					b.run()
			else:
				b.skip()

'''
class block:
	def __call__(block, self, vm):
		def wrapper(self, vm):
			# get expression
			# get block

			func(self, block)
		
		return wrapper

class While(Token):
	@block
	def run(self, block):
		if block.true():
			while block.true():
				block.run()
		else:
			block.skip()
'''

# from vm import block, expr?

class Repeat(Token):
	def run(self, vm):
		@vm.block
		def run(b):
			if b.false():
				while b.false():
					b.run()
			else:
				b.skip()

class Stor(Token):
	token = u'→'
	priority = Pri.SET

	def run(self, vm, left, right):
		right.set(vm, left)
		return left.get(vm)

class Store(Stor): token = '->'

class Disp(Token):
	absorbs = (expression.Expression, Variable)

	def run(self, vm):
		cur = self.arg
		if not cur:
			print
			return

		if isinstance(cur, expression.Tuple):
			print ', '.join(str(x) for x in cur.get(vm))
		else:
			print cur.get(vm)

class Disp(Function):
	def run(self, vm):
		print ', '.join(str(x) for x in self.arg.get(vm))

class Goto(Function):
	def run(self, vm):
		vm.goto(*self.arg.get(vm))

class Then(StubToken): pass
class Else(StubToken): pass

class End(Token):
	def run(self, vm):
		vm.end_block()

# operators

class Operator(Token, Stub):
	@get
	def run(self, vm, left, right):
		return self.op(left, right)

class AddSub(Operator): priority = Pri.ADDSUB
class MultDiv(Operator): priority = Pri.MULTDIV
class Bool(Operator):
	priority = Pri.BOOL

	@get
	def run(self, vm, left, right):
		if self.bool(left, right): return 1
		return 0

class Logic(Bool): priority = Pri.LOGIC

# math

class Plus(AddSub):
	token = '+'

	def op(self, left, right):
		return left + right

class Minus(AddSub):
	token = '-'

	def op(self, left, right):
		return left - right

class Mult(MultDiv):
	token = '*'

	def op(self, left, right):
		return left * right

class Div(MultDiv):
	token = '/'

	def op(self, left, right):
		return left / right

# boolean

class And(Bool):
	token = 'and'

	def bool(self, left, right):
		return left and right

class Or(Bool):
	token = 'or'

	def bool(self, left, right):
		return left or right

class xor(Bool):
	def bool(self, left, right):
		return left ^ right

# logic

class LessThan(Logic):
	token = '<'
	
	def bool(self, left, right):
		return left < right

class GreaterThan(Logic):
	token = '>'

	def bool(self, left, right):
		return left > right

class LessOrEquals(Logic):
	token = '<='

	def run(self, left, right):
		return left <= right

class LessOrEqualsToken(LessOrEquals):
	token = u'≤'

class GreaterOrEquals(Logic):
	token = '>='

	def bool(self, left, right):
		return left >= right

class GreaterOrEqualsToken(GreaterOrEquals):
	token = u'≥'

# variables

class Const(Variable, Stub):
	value = None

	def set(self, vm, value): raise InvalidOperation
	def get(self, vm): return self.value

class Value(Const):
	def __init__(self, value):
		self.value = value
		Variable.__init__(self)

	def get(self, vm): return self.value

	def __repr__(self):
		return repr(self.value)

class Ans(Const):
	def get(self, vm): return vm.get_var('Ans')

class Pi(Const):
	token = u'π'
	value = math.pi

class e(Const):
	token = 'e'
	value = math.e

class SimpleVar(Variable, Stub):
	def set(self, vm, value): return vm.set_var(self.token, value)
	def get(self, vm): return vm.get_var(self.token)

for c in string.uppercase:
	add_class(c, SimpleVar)