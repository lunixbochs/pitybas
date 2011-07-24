# -*- coding: utf-8 -*-
import math, random

from common import Pri, ExecutionError
from expression import Tuple, Expression, Arguments

# helpers

def add_class(name, *args, **kwargs):
	globals()[name] = type(name, args, kwargs)

# decorators

def get(f):
	def run(self, vm, left, right):
		return f(self, vm, vm.get(left), vm.get(right))
	
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
			'can_fill_left': False,
			'can_fill_right': False
		})

		cls = type.__new__(self, name, bases, attrs)

		if 'run' in dir(cls):
			cls.can_run = True
		
		if 'get' in dir(cls):
			cls.can_get = True
		
		if 'set' in dir(cls):
			cls.can_set = True

		if 'fill_left' in dir(cls):
			cls.can_fill_left = True
		
		if 'fill_right' in dir(cls):
			cls.can_fill_right = True
		
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

	def __cmp__(self, token):
		try:
			if self.priority < token.priority:
				return -1
			elif self.priority == token.priority:
				return 0
			elif self.priority > token.priority:
				return 1
			else:
				raise AttributeError
		except AttributeError:
			return NotImplemented

	def __repr__(self):
		return repr(self.token)

class Stub:
	@classmethod
	def add(cls, sub, name, attrs): pass

class Token(Parent):
	tokens = {}

	def run(self, vm):
		raise NotImplementedError
	
	def __repr__(self):
		if self.arg:
			return '%s %s' % (repr(self.token), repr(self.arg))
		else:
			return repr(self.token)

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
		if self.can_run:
			self.priority = Pri.INVALID

		Parent.__init__(self)

	def get(self, vm):
		raise NotImplementedError
	
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

class Theta(SimpleVar):
	token = u'\u03b8'

for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
	add_class(c, SimpleVar)

class Str(SimpleVar, Stub):
	pass

for i in xrange(10):
	add_class('Str%i' % i, SimpleVar)

# operators

class Stor(Token):
	token = u'→'
	priority = Pri.SET

	def run(self, vm, left, right):
		right.set(vm, vm.get(left))
		return vm.get(left)

class Store(Stor): token = '->'

class Operator(Token, Stub):
	@get
	def run(self, vm, left, right):
		return self.op(left, right)

class AddSub(Operator, Stub): priority = Pri.ADDSUB
class MultDiv(Operator, Stub): priority = Pri.MULTDIV
class Exponent(Operator, Stub): priority = Pri.EXPONENT
class RightExponent(Exponent, Stub):
        def fill_right(self):
                return Value(None)

class Bool(Operator, Stub):
	priority = Pri.BOOL

	@get
	def run(self, vm, left, right):
		return int(bool(self.bool(left, right)))

class MathFunction(Function, Stub):
	def get(self, vm):
		args = vm.get(self.arg)
		return self.call(vm, args)
	
	def call(self, vm, arg): raise NotImplementedError

# a MathFunction expecting a single Expression as the argument
class MathExprFunction(MathFunction, Stub):
	def get(self, vm):
		assert len(self.arg) == 1
		args = vm.get(self.arg)

		return self.call(vm, args[0])

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

# TODO: -¹, ², ³, √(, ³√(, ×√
class Square(RightExponent):
	token = u'²'

	def op(self, left, right):
		return left ** 2

class Cube(RightExponent):
	token = u'³'

	def op(self, left, right):
		return left ** 3

class Sqrt(Function):
	token = u'√'

	def get(self, vm):
		return math.sqrt(vm.get(self.arg)[0])

class sqrt(Sqrt): pass

class CubeRoot(MathExprFunction):
	token = u'³√'
	
	def call(self, vm, arg):
		# TODO: proper accuracy. maybe write a numpy addon, to increase accuracy if numpy is installed?

		# round to within our accuracy bounds
		# this allows us to reverse a cube properly, as long as we don't pass 14 significant digits
		i = arg ** (1.0/3)
		places = 14 - len(str(int(math.floor(i))))
		if places > 0:
			return round(i, places)
		else:
			# oh well
			return i

class SciNot(Operator):
	priority = Pri.EXPONENT
	token = u'ᴇ'

	def fill_left(self):
		return Value(1)

	def op(self, left, right):
		return left * (10 ** right)

class Abs(MathExprFunction):
	token = 'abs'

	def call(self, vm, arg):
		return abs(arg)

class gcd(MathFunction):
	def call(self, vm, args):
		assert len(args) == 2
		return gcd.gcd(*args)

	# TODO: list support
	@staticmethod
	def gcd(a, b):
		while b:
			a, b = b, (a % b)
		return a

class lcm(MathFunction):
	def call(self, vm, args):
		assert len(args) == 2

		a, b = args
		return a * b / gcd.gcd(a, b)

class Min(MathFunction):
	token = 'min'

	def call(self, vm, args):
		assert len(args) == 2
		return min(*args)

class Max(MathFunction):
	token = 'max'

	def call(self, vm, args):
		assert len(args) == 2
		return max(*args)

class Round(MathFunction):
	token = 'round'

	def call(self, vm, args):
		assert len(args) in (1, 2)

		if len(args) == 2:
			places = args[1]
		else:
			places = 9

		return round(args[0], places)

class Int(MathExprFunction):
	token = 'int'

	def call(self, vm, arg):
		return math.floor(arg)

class iPart(MathFunction):
	def call(self, vm, arg):
		return int(arg)

class fPart(MathFunction):
	def call(self, vm, arg):
		return math.modf(arg)[1]

# trig

class sin(MathExprFunction):
	def call(self, vm, arg): return math.sin(arg)

class cos(MathExprFunction):
	def call(self, vm, arg): return math.cos(arg)

class tan(MathExprFunction):
	def call(self, vm, arg): return math.tan(arg)

# TODO: subclass these inverse functions with the unicode -1 token, and probably add support for that in the parser for ints too
class asin(MathExprFunction):
	token = 'sin-1'

	def call(self, vm, arg): return math.asin(arg)

class acos(MathExprFunction):
	token = 'cos-1'

	def call(self, vm, arg): return math.acos(arg)

class atan(MathExprFunction):
	token = 'tan-1'

	def call(self, vm, arg): return math.atan(arg)

class sinh(MathExprFunction):
	def call(self, vm, arg): return math.sinh(arg)

class cosh(MathExprFunction):
	def call(self, vm, arg): return math.cosh(arg)

class tanh(MathExprFunction):
	def call(self, vm, arg): return math.tanh(arg)

class asinh(MathExprFunction):
	token = 'sin-1'

	def call(self, vm, arg): return math.asinh(arg)

class acosh(MathExprFunction):
	token = 'cos-1'

	def call(self, vm, arg): return math.acosh(arg)

class atanh(MathExprFunction):
	token = 'tan-1'

	def call(self, vm, arg): return math.atanh(arg)

# probability

class nPr(Operator):
	# TODO: nPr and nCr should support lists
	priority = Pri.PROB

	def op(self, left, right):
		return math.factorial(left) / math.factorial((left - right))

class nCr(Operator):
	priority = Pri.PROB

	def op(self, left, right):
		return math.fact(left) / (math.fact(right) * math.fact((left - right)))

class Factorial(Exponent):
	token = '!'

	def op(self, left, right):
		return math.factorial(left)

	def fill_right(self):
		return Value(None)

# random numbers

class rand(Variable):
	def get(self, vm):
		return random.random()
	
	def set(self, vm, value):
		random.seed(value)

class rand(MathFunction):
	def call(self, vm, args):
		assert len(args) == 1
		return [random.random() for i in xrange(args[0])]

class randInt(MathFunction):
	def call(self, vm, args):
		assert len(args) in (2, 3)

		if len(args) == 2:
			args.append(1)
		
		return random.randint(*args)

class randNorm(MathFunction):
	def call(self, vm, args):
		assert len(args) in (2, 3)

		if len(args) == 3:
			args, n = args[:2], args[2]
		else:
			n = 1
		
		return [random.normalvariate(*args) for i in xrange(n)]

class randBin(MathFunction):
	def call(self, vm, args):
		raise NotImplementedError # numpy.random has a binomial distribution, or I could write my own...

class randM(MathFunction):
	def call(self, vm, args):
		raise NotImplementedError # I don't know how I'm going to do lists and matricies yet

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

class Not(Function):
	token = 'not'

	def get(self, vm):
		args = vm.get(self.arg)
		assert len(args) == 1

		return int(bool(not args[0]))

# logic

class Equals(Logic):
	token = '='

	def bool(self, left, right):
		return left == right

class NotEquals(Logic):
	token = '~='

	def bool(self, left, right):
		return left != right

class NotEqualsToken(NotEquals):
	token = u'≠'

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

	def find_end(self, vm, or_else=False, cur=False):
		tokens = vm.find(Block, Then, Else, End, wrap=False)
		blocks = []
		thens = 0
		for row, col, token in tokens:
			if not cur and token is self:
				continue

			if isinstance(token, If):
				continue

			if isinstance(token, Then):
				thens += 1
				blocks.append(token)
			elif isinstance(token, Block):
				blocks.append(token)
			elif isinstance(token, End):
				if (thens == 0 or not or_else) and not blocks:
					return row, col, token
				else:
					b = blocks.pop(0)
					if isinstance(b, Then):
						thens -= 1
			elif or_else and isinstance(token, Else):
				if thens == 0:
					return row, col, token

class If(Block):
	def run(self, vm):
		if self.arg == None:
			raise ExecutionError('If statement without condition')

		true = bool(vm.get(self.arg))

		cur = vm.cur()
		if isinstance(cur, Then):
			vm.push_block()
			vm.inc()
				
			if not true:
				end = self.find_end(vm, or_else=True)
				if end:
					row, col, end = end
					if isinstance(end, End):
						vm.pop_block()

					vm.goto(row, col)
					vm.inc()
				else:
					raise ExecutionError('If/Then could not find End on negative expression')
		elif true:
			vm.run(cur)
		else:
			vm.inc_row()

	def resume(self, vm, row, col): pass
	def stop(self, vm, row, col): pass

class Then(Token):
	def run(self, vm):
		raise ExecutionError('cannot execute a standalone Then statement')

class Else(Token):
	def run(self, vm):
		row, col, block = vm.pop_block()
		end = self.find_end(vm)
		if end:
			row, col, end = end
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
			self.stop(vm)

	def stop(self, vm):
		end = self.find_end(vm)
		if end:
			row, col, end = end
		else:
			raise ExecutionError('%s could not find End' % self.token)

		vm.goto(row, col)
		vm.inc()

class While(Loop):
	def loop(self, vm):
		return bool(vm.get(self.arg))

class Repeat(Loop):
	def loop(self, vm):
		return not bool(vm.get(self.arg))

class For(Loop, Function):
	pos = None

	def loop(self, vm):
		if len(self.arg) in (3, 4):
			var = self.arg.contents[0]
			args = [vm.get(arg) for arg in self.arg.contents[1:]]

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
		try:
			row, col, block = vm.pop_block()
			block.resume(vm, row, col)
		except ExecutionError:
			pass

class Continue(Token):
	def run(self, vm):
		for row, col, block in reversed(vm.blocks):
			if not isinstance(block, If):
				block.resume(vm, row, col)
				break
		else:
			raise ExecutionError('Continue could not find a block to continue')

class Break(Token):
	def run(self, vm):
		for row, col, block in reversed(vm.blocks):
			if not isinstance(block, If):
				block.stop(vm, row, col)
				break
		else:
			raise ExecutionError('Break could not find a block to end')

class Lbl(StubToken):
	absorbs = (Expression, Value)

	@staticmethod
	def guess_label(vm, arg):
		label = None
		if isinstance(arg, Expression):
			arg = arg.flatten()

		if isinstance(arg, Value):
			label = vm.get(arg)
		elif isinstance(arg, Variable):
			label = arg.token
		elif isinstance(arg, Expression):
			label = vm.get(arg)
		
		return label
	
	def get_label(self, vm):
		return Lbl.guess_label(vm, self.arg)

class Goto(Token):
	absorbs = (Expression, Value)
	def run(self, vm):
		Goto.goto(vm, self.arg)
	
	@staticmethod
	def goto(vm, token):
		label = Lbl.guess_label(vm, token)
		if label:
			for row, col, token in vm.find(Lbl, wrap=True):
				if token.get_label(vm) == label:
					vm.goto(row, col)
					return
					
		raise ExecutionError('could not find a label to Goto: %s' % token)

class Menu(Function):
	def run(self, vm):
		args = self.arg.contents[:]
		l = len(args)
		if l >= 3 and (l - 3) % 2 == 0:
			title = args.pop(0)

			menu = (title, zip(args[::2], args[1::2])),

			label = vm.io.menu(menu)
			Goto.goto(vm, label)
		else:
			raise ExecutionError('Invalid arguments to Menu(): %s' % args)

class Pause(Token):
	absorbs = (Expression, Variable)

	def run(self, vm):
		cur = self.arg
		if cur:
			vm.io.pause(vm.get(cur))
		else:
			vm.io.pause()

# input/output

class ClrHome(Token):
	def run(self, vm):
		vm.io.clear()

class Disp(Token):
	absorbs = (Expression, Variable, Tuple)

	def run(self, vm):
		cur = self.arg
		if not cur:
			self.disp(vm)
			return

		self.disp(vm, vm.get(cur))
	
	def disp(self, vm, msgs=None):
		if isinstance(msgs, (tuple, list)):
			for msg in msgs:
				vm.io.disp(msg)
		else:
			vm.io.disp(msgs)

class Print(Disp):
	absorbs = (Expression, Variable, Tuple)

	def disp(self, vm, msgs=None):
		if isinstance(msgs, (tuple, list)):
			vm.io.disp(', '.join(str(x) for x in msgs))
		else:
			vm.io.disp(msgs)

class Prompt(Token):
	absorbs = (Expression, Variable, Tuple)
	
	def run(self, vm):
		if not self.arg:
			raise ExecutionError('%s used without arguments')

		if isinstance(self.arg, Tuple):
			for var in self.arg.contents:
				self.prompt(vm, var)
		else:
			self.prompt(vm, self.arg)

	def prompt(self, vm, var):
		val = vm.io.input(var.token + '?')
		var.set(vm, val)

	def __repr__(self):
		return 'Prompt(%s)' % repr(self.arg)

class Input(Token):
	# TODO: how is string input handled on calc? been too long
	absorbs = (Expression, Variable, Tuple)

	def run(self, vm):
		arg = self.arg
		if not arg:
			raise ExecutionError('Input used without arguments')

		if isinstance(arg, Tuple) and len(arg) == 1 or isinstance(arg, Variable):
			self.prompt(vm, arg)
		elif isinstance(arg, Tuple) and len(arg) == 2:
			self.prompt(vm, arg.contents[1], vm.get(arg.contents[0]))
		else:
			raise ExecutionError('Input used with wrong number of arguments')

	def prompt(self, vm, var, msg=''):
		if isinstance(var, Str):
			is_str = True
		else:
			is_str = False
		
		val = vm.io.input(msg + '?', is_str)
		var.set(vm, val)
