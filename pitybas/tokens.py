# -*- coding: utf-8 -*-
import string, math
from common import Pri, ExecutionError
from expression import Tuple, Expression, Arguments

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
		if isinstance(token, Expression):
			flat = token.flatten()
			for typ in self.absorbs:
				if isinstance(flat, typ):
					token = flat

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

	absorbs = (Arguments,)

	@classmethod
	def add(cls, sub, name, attrs):
		if 'token' in attrs:
			name = attrs['token']
		
		if name:
			name += '('
			cls.tokens[name] = sub

	def __init__(self):
		self.args = ()
		if self.can_run:
			self.priority = Pri.INVALID

		Parent.__init__(self)

	def get(self, vm):
		raise NotImplementedError
	
	def set_args(self, args):
		self.args = args
	
	def __repr__(self):
		if self.arg:
			return '%s%s' % (repr(self.token), repr(self.arg).replace('A', '', 1))
		else:
			return '%s()' % repr(self.token)

class StubFunction(Function, Stub):
	def call(self, vm): pass

# variables

class EOF(Token, Stub):
	def run(self, vm):
		vm.done()

class Const(Variable, Stub):
	def __init__(self, value):
		super(Const, self).__init__()
		self.value = value

	def get(self, vm):
		return self.value

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

for i in xrange(10):
	add_class('Str%i' % i, SimpleVar)

# operators

class Stor(Token):
	token = u'→'
	priority = Pri.SET

	def run(self, vm, left, right):
		right.set(vm, left.get(vm))
		return left.get(vm)

class Store(Stor): token = '->'

class Operator(Token, Stub):
	@get
	def run(self, vm, left, right):
		return self.op(left, right)

class AddSub(Operator): priority = Pri.ADDSUB
class MultDiv(Operator): priority = Pri.MULTDIV
class Exponent(Operator): priority = Pri.EXPONENT
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

class Pow(Exponent):
	token = '^'

	def op(self, left, right):
		return left ** right

class Sqrt(Function):
	token = u'√'

	def get(self, vm):
		expr = Expression()
		for arg in self.arg.contents:
			expr.append(arg)

		return math.sqrt(expr.get(vm))

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

# control flow

class Block(StubToken):
	absorbs = (Expression, Value)

class If(Block):
	def run(self, vm):
		if self.arg == None:
			raise ExecutionError('If statement without condition')

		true = bool(self.arg.get(vm))
		tokens = vm.find(Else, End, wrap=False)

		els, end = None, None
		for row, col, token in tokens:
			if not els and isinstance(token, Else):
				els = row, col, token
			elif isinstance(token, End):
				end = row, col, token
				break

		cur = vm.cur()
		if isinstance(cur, Then):
			if true:
				vm.push_block()
				vm.inc()
			elif els:
				vm.push_block()
				row, col, _ = els
				vm.goto(row, col)
				vm.inc()
			elif end:
				row, col, _ = end
				vm.goto(row, col)
				vm.inc()
			else:
				raise ExecutionError('If/Then could not find End on negative expression')
		elif true:
			vm.run(cur)
		else:
			vm.inc_row()

	def resume(self, vm, row, col): pass

class Then(Token):
	def run(self, vm):
		raise ExecutionError('cannot execute a standalone Then statement')

class Else(Token):
	def run(self, vm):
		row, col, block = vm.pop_block()
		ends = vm.find(End, wrap=False)
		for e in ends:
			row, col, end = e
			break
		else:
			raise ExecutionError('Else could not find End')

		vm.goto(row, col)
		vm.inc()

class Loop(Block, Stub):
	def run(self, vm):
		if self.arg == None:
			raise ExecutionError('%s statement without condition' % self.token)

		row, col, _ = vm.running[-1]
		self.resume(vm, row, col)

	def loop(self, vm):
		return True

	def resume(self, vm, row, col):
		vm.goto(row, col)
		if self.loop(vm):
			vm.push_block((row, col, self))
			vm.inc()
		else:
			tokens = vm.find(End, wrap=False)
			for row, col, token in tokens:
				if isinstance(token, End):
					break
			else:
				raise ExecutionError('%s could not find End' % self.token)

			vm.goto(row, col)
			vm.inc()

class While(Loop):
	def loop(self, vm):
		return bool(self.arg.get(vm))

class Repeat(Loop):
	def loop(self, vm):
		return not bool(self.arg.get(vm))

class For(Loop, Function):
	pos = None

	def loop(self, vm):
		if len(self.arg) in (3, 4):
			var = self.arg.contents[0]
			args = [arg.get(vm) for arg in self.arg.contents[1:]]

			forward = True
			if len(args) == 3:
				inc = args[2]
				args = args[:2]
				forward = False
			else:
				inc = 1
			
			start, end = args
			
			if self.pos is None:
				self.pos = start
			else:
				self.pos += inc

			var.set(vm, self.pos)
			if forward and self.pos > end or not forward and self.pos < end:
				return False
			else:
				return True
		else:
			raise ExecutionError('incorrect arguments to For loop')

class End(Token):
	def run(self, vm):
		row, col, block = vm.pop_block()
		block.resume(vm, row, col)

class Lbl(StubToken):
	absorbs = (Expression, Value)

	@staticmethod
	def guess_label(arg, vm):
		label = None
		if isinstance(arg, Expression):
			arg = arg.flatten()

		if isinstance(arg, Value):
			label = arg.get(vm)
		elif isinstance(arg, Variable):
			label = arg.token
		elif isinstance(arg, Expression):
			label = arg.get(vm)
		
		return label
	
	def get_label(self, vm):
		return Lbl.guess_label(self.arg, vm)

class Goto(Token):
	absorbs = (Expression, Value)
	def run(self, vm):
		label = Lbl.guess_label(self.arg, vm)
		
		if label:
			for row, col, token in vm.find(Lbl):
				if token.get_label(vm) == label:
					vm.goto(row, col)
		else:
			raise ExecutionError('could not find a label to Goto: %s' % self.arg)

class Goto(Function):
	def run(self, vm):
		vm.goto(*self.arg.get(vm))

# input/output

class Disp(Token):
	absorbs = (Expression, Variable)

	def run(self, vm):
		cur = self.arg
		if not cur:
			print
			return

		if isinstance(cur, Tuple):
			print ', '.join(str(x) for x in cur.get(vm))
		else:
			print cur.get(vm)

class Disp(Function):
	def run(self, vm):
		print ', '.join(str(x) for x in self.arg.get(vm))


class Prompt(Token):
	absorbs = (Expression, Variable, Tuple)
	
	def run(self, vm):
		if not self.arg:
			raise ExecutionError('Prompt used without arguments')

		if isinstance(self.arg, Tuple):
			for var in self.arg.contents:
				self.prompt(vm, var)
		else:
			self.prompt(vm, self.arg)

	def prompt(self, vm, var):
		var.set(vm, input('%s? ' % var.token))

	def __repr__(self):
		return 'Prompt(%s)' % repr(self.arg)

class Input(Token):
	absorbs = (Expression, Variable, Tuple)

	def run(self, vm):
		arg = self.arg
		if not arg:
			raise ExecutionError('Input used without arguments')

		if isinstance(arg, Tuple) and len(arg) == 1 or isinstance(arg, Variable):
			self.prompt(vm, arg)
		elif isinstance(arg, Tuple) and len(arg) == 2:
			self.prompt(vm, arg.contents[1], arg.contents[0].get(vm))
		else:
			raise ExecutionError('Input used with wrong number of arguments')

	def prompt(self, vm, var, msg=''):
		var.set(vm, input('%s? ' % msg))
