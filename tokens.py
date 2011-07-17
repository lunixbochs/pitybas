# -*- coding: utf-8 -*-
import string, math

def add_class(name, *args, **kwargs):
	globals()[name] = type(name, args, kwargs)

class Tracker(type):
	def __init__(cls, name, bases, attrs):
		if bases:
			bases[-1].add(cls, name, attrs)

class InvalidOperation(Exception):
	pass

class Pri:
	# evaluation happens in the following order:
	# skip: expressions, functions, variables
	# 1. exponents, factorials
	# 2. multiplication, division
	# 3. addition, subtraction
	# 4. logic operators
	# 5. boolean operators
	# 6. variable setting

	# these won't be parsed into expressions at all
	INVALID = -2
	# NONE means store but don't execute directly
	# used for variables, lazy loading functions and expressions
	NONE = -1

	EXPONENT = 0
	MULTDIV = 1
	ADDSUB = 2

	LOGIC = 3
	BOOL = 4
	SET = 5

class Parent:
	__metaclass__ = Tracker

	@classmethod
	def add(cls, sub, name, attrs):
		if 'token' in attrs:
			name = attrs['token']
		else:
			attrs['token'] = name
		
		if name and not cls == Parent:
			cls.tokens[name] = sub
	
	can_run = False
	can_get = False
	can_set = False
	can_call = False

	# used for evaluation order inside expressions
	priority = Pri.INVALID

	def __init__(self):
		if self.run != Parent.run:
			self.can_run = True

		if self.get != Parent.get:
			self.can_get = True
		
		if self.set != Parent.set:
			self.can_set = True
		
		if self.call != Parent.call:
			self.can_call = True
	
	def run(self, vm): raise InvalidOperation
	def get(self, vm): raise InvalidOperation
	def set(self, vm, value): raise InvalidOperation
	def call(self, vm): raise InvalidOperation

class Stub:
	@classmethod
	def add(cls, sub, name, attrs): pass

class Token(Parent):
	tokens = {}

	def run(self, vm):
		raise NotImplementedError

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

	def get(self, vm):
		return self.call(vm)

	def call(self, vm):
		raise NotImplementedError

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

	def run(self, vm):
		@vm.expr
		def run(e):
			return e.right.set(e.left.get())

class Store(Stor): token = '->'

class Disp(Token):
	def run(self, vm):
		cur = vm.cur()
		if isinstance(cur, tuple):
			print '\n'.join(str(x.get(vm)) for x in cur)
		else:
			print cur.get(vm)
		
		vm.inc()


class Then(StubToken): pass
class Else(StubToken): pass

class End(Token):
	def run(self, vm):
		vm.end_block()

# operators

class Operator(Token, Stub): pass
class AddSub(Operator): priority = Pri.ADDSUB
class MultDiv(Operator): priority = Pri.MULTDIV
class Bool(Operator):
	priority = Pri.BOOL

	def run(self, left, right):
		if self.bool(left, right): return 1
		return 0

class Logic(Bool): priority = Pri.LOGIC

# math

class Plus(AddSub):
	token = '+'

	def run(self, left, right):
		return left + right

class Minus(AddSub):
	token = '-'

	def run(self, left, right):
		return left - right

class Mult(MultDiv):
	token = '*'

	def run(self, left, right):
		return left * right

class Div(MultDiv):
	token = '/'

	def run(self, left, right):
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


['+', '-', '*', '/', u'‾', '^', u'√',
'=', u'≠', '>', u'≥', '<', u'≤',
u'→', '!', u'π', '%', 'r', u'°',
',', '(', ')', '[', ']', '{', '}',]

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