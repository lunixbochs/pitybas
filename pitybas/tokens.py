# -*- coding: utf-8 -*-
import datetime
import decimal
import fractions
import math
import random
import string

from common import Pri, ExecutionError, StopError, ReturnError
from expression import Tuple, Expression, Arguments, ListExpr, MatrixExpr

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
        return self.call(vm, vm.get(self.arg))

    def call(self, vm, args):
        raise NotImplementedError

    def __repr__(self):
        if self.arg:
            return '%s%s' % (repr(self.token), repr(self.arg).replace('A', '', 1))
        else:
            return '%s()' % repr(self.token)

class StubFunction(Function, Stub):
    def call(self, vm, args): pass

# variables

class EOF(Token, Stub):
    def run(self, vm):
        raise StopError

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

class Value(Const, Stub):
    def __init__(self, value):
        self.value = value
        Variable.__init__(self)

    def get(self, vm): return self.value

    def __repr__(self):
        return repr(self.value)

# list/matrix

class List(Variable, Stub):
    absorbs = (Arguments,)

    def __init__(self, name=None):
        self.name = name
        super(List, self).__init__()

    def dim(self, vm, value=None):
        if value is not None:
            assert isinstance(value, (int, long))

            try:
                l = vm.get_list(self.name)
            except KeyError:
                l = []

            l = l[:value] + ([0] * (value - len(l)))
            vm.set_list(self.name, l)
        else:
            return len(vm.get(self))

    def get(self, vm):
        if self.arg:
            arg = vm.get(self.arg)[0]
            assert isinstance(arg, (int, long))
            return vm.get_list(self.name)[arg-1]

        return vm.get_list(self.name)

    def set(self, vm, value):
        if self.arg:
            arg = vm.get(self.arg)[0]
            assert isinstance(arg, (int, long))
            assert isinstance(value, (int, long, float, complex))

            l = vm.get_list(self.name)
            i = arg - 1

            if i == len(l):
                l.append(value)
            else:
                l[i] = value
            vm.set_list(self.name, l)
        else:
            assert isinstance(value, list)
            vm.set_list(self.name, value[:])

        return value

    def __repr__(self):
        if self.arg:
            return 'l%s(%s)' % (self.name, self.arg)

        return 'l%s' % self.name

class ListToken(List):
    token = u'∟'

class Matrix(Variable, Stub):
    absorbs = (Arguments,)

    def __init__(self, name=None):
        self.name = name

    def dim(self, vm, value=None):
        if value is not None:
            assert isinstance(value, list) and len(value) == 2

            a, b = value
            try:
                m = vm.get_matrix(self.name)
            except KeyError:
                m = [[]]

            m = m[:a]
            for i in xrange(len(m), a):
                n = ([0] * b)
                m.append(n)

            m = [l[:b] + ([0] * (b - len(l))) for l in m]
            vm.set_matrix(self.name, m)
        else:
            val = vm.get_matrix(self.name)
            return [len(val), len(val[0])]

    def get(self, vm):
        if self.arg:
            arg = vm.get(self.arg)
            assert isinstance(arg, list) and len(arg) == 2
            return vm.get_matrix(self.name)[arg[0]-1][arg[1]-1]

        return vm.get_matrix(self.name)

    def set(self, vm, value):
        if self.arg:
            arg = vm.get(self.arg)
            assert isinstance(arg, list) and len(arg) == 2
            assert isinstance(value, (int, long, float, complex))

            m = vm.get_matrix(self.name)
            m[arg[0]-1][arg[1]-1] = value
        else:
            assert isinstance(value, list)
            vm.set_matrix(self.name, value)

        return value

    def __repr__(self):
        return '[%s]' % self.name

class dim(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) == 1

        arg = self.arg.contents[0].flatten()
        assert isinstance(arg, (List, Matrix))
        return arg.dim(vm)

    def set(self, vm, value):
        assert self.arg and len(self.arg) == 1

        arg = self.arg.contents[0].flatten()
        assert isinstance(arg, (List, Matrix))
        name = arg.name

        arg.dim(vm, value)
        return value

class augment(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) == 2
        a = self.arg.contents[0].flatten()
        b = self.arg.contents[1].flatten()
        if isinstance(a, (List, ListExpr)) and isinstance(b, (List, ListExpr)):
            return vm.get(a) + vm.get(b)
        elif isinstance(a, (Matrix, MatrixExpr)) and isinstance(b, (Matrix, MatrixExpr)):
            a = vm.get(a)
            b = vm.get(b)
            assert len(a) == len(b)
            return [left + b[i] for i, left in enumerate(a)]
        else:
            raise ExecutionError('augment() requires List, List or Matrix, Matrix')

class Fill(Function):
    def run(self, vm):
        assert self.arg and len(self.arg) == 2
        num, var = self.arg.contents
        var = var.flatten()
        num = vm.get(num)

        assert isinstance(num, (int, long, float, complex))
        assert isinstance(var, (List, Matrix))

        if isinstance(var, List):
            l = [num for i in xrange(len(vm.get(var)))]
            var.set(vm, l)
        elif isinstance(var, Matrix):
            m = []
            o = vm.get(var)
            for a in o:
                c = []
                for b in a:
                    c.append(num)

                m.append(c)

            var.set(vm, m)

class seq(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) in (4, 5)
        arg = self.arg.contents
        expr = arg[0]
        var = arg[1].flatten()
        assert isinstance(var, Variable)
        assert isinstance(expr, Expression)
        step = 1
        if len(arg) == 5:
            step = vm.get(arg[4])
        out = []
        start, end = vm.get(arg[2]), vm.get(arg[3])
        for i in xrange(start, end + 1, step):
            vm.set_var(var.token, i)
            out.append(vm.get(expr))
        return out

class Sum(Function):
    token = 'sum'

    def get(self, vm):
        assert self.arg and len(self.arg) == 1
        arg = self.arg.flatten()
        return sum(vm.get(arg))

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

class NumVar(SimpleVar, Stub):
    def get(self, vm):
        return vm.get_var(self.token, 0)

class StrVar(SimpleVar, Stub):
    def get(self, vm):
        return vm.get_var(self.token, '')

class Theta(NumVar):
    token = u'\u03b8'

class THETA(NumVar):
    def set(self, vm, value):
        return vm.set_var(Theta.token, value)

    def get(self, vm):
        return vm.get_var(Theta.token)

for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    add_class(c, NumVar)

class Str(SimpleVar, Stub):
    pass

for i in xrange(10):
    add_class('Str%i' % i, StrVar)

# operators

class Stor(Token):
    token = u'→'
    priority = Pri.SET

    def run(self, vm, left, right):
        ans = vm.get(left)
        right.set(vm, ans)
        return ans

class Store(Stor): token = '->'

class Operator(Token, Stub):
    @get
    def run(self, vm, left, right):
        return self.op(left, right)

class FloatOperator(Operator, Stub):
    @get
    def run(self, vm, left, right):
        # TODO: be smarter about when to coerce to float
        if isinstance(left, (int, long)) or isinstance(right, (int, long)):
            decimal.getcontext().prec = max(len(str(left)), len(str(right)))
            left = decimal.Decimal(left)
            right = decimal.Decimal(right)

        ans = self.op(left, right)
        # 14 digits of precision?
        if abs(ans - int(ans)) < 0.00000000000001:
            ans = int(ans)

        return ans

class AddSub(Operator, Stub): priority = Pri.ADDSUB
class MultDiv(FloatOperator, Stub): priority = Pri.MULTDIV
class Exponent(Operator, Stub): priority = Pri.EXPONENT
class RightExponent(Exponent, Stub):
    def fill_right(self):
        return Value(None)

class Bool(Operator, Stub):
    priority = Pri.BOOL

    @get
    def run(self, vm, left, right):
        return int(bool(self.bool(left, right)))

# a Function expecting a single Expression as the argument
class MathExprFunction(Function, Stub):
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

class transpose(RightExponent):
    token = '_T'

    def op(self, left, right):
        vm = {'tmp': left}
        rows, cols = Matrix('tmp').dim(vm)
        out = [[0] * rows for i in xrange(cols)]
        for y in xrange(rows):
            for x in xrange(cols):
                out[x][y] = left[y][x]
        return out

# TODO: -¹, ², ³, √(, ³√(, ×√
class Square(RightExponent):
    token = u'²'

    def op(self, left, right):
        return left ** 2

class Cube(RightExponent):
    token = u'³'

    def op(self, left, right):
        return left ** 3

class Sqrt(MathExprFunction):
    token = u'√'

    def call(self, vm, arg):
        return math.sqrt(arg)

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

class gcd(Function):
    def call(self, vm, args):
        assert len(args) == 1 and isinstance(args[0], list) or len(args) == 2
        if len(args) == 1:
            return reduce(lambda a, b: fractions.gcd(a, b), args[0])
        else:
            return fractions.gcd(*args)

    # TODO: list support
    @staticmethod
    def gcd(a, b):
        while b:
            a, b = b, (a % b)
        return a

class lcm(Function):
    def call(self, vm, args):
        assert len(args) == 2
        a, b = args
        if isinstance(a, list):
            a = self.lcm_list(*a)
        if isinstance(b, list):
            a = self.lcm_list(*b)
        return self.lcm(a, b)

    @staticmethod
    def lcm(a, b):
        return a * b / gcd.gcd(a, b)

    @classmethod
    def lcm_list(cls, *args):
        args = list(args)
        a = args.pop(0)
        while args:
            b = args.pop(0)
            a = cls.lcm(a, b)
        return a

class Min(Function):
    token = 'min'

    def call(self, vm, args):
        assert len(args) == 2
        return min(*args)

class Max(Function):
    token = 'max'

    def call(self, vm, args):
        assert len(args) in (1, 2)
        if len(args) == 1:
            assert isinstance(args[0], list)
            return max(args[0])
        else:
            a1, a2 = args
            if not isinstance(a1, list):
                a1 = [a1]
            if not isinstance(a2, list):
                a2 = [a2]
            return max(a1 + a2)

class Round(Function):
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

class iPart(MathExprFunction):
    def call(self, vm, arg):
        return int(arg)

class fPart(MathExprFunction):
    def call(self, vm, arg):
        return math.modf(arg)[1]

class floor(MathExprFunction):
    def call(self, vm, arg):
        return math.floor(arg)

class ceiling(MathExprFunction):
    def call(self, vm, arg):
        return math.ceil(arg)

class mod(Function):
    def call(self, vm, args):
        assert len(args) == 2
        return args[0] % args[1]

class expr(MathExprFunction):
    def call(self, vm, arg):
        from parse import Parser, ParseError
        return Parser.parse_line(vm, arg)

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

class rand(Function):
    def call(self, vm, args):
        assert len(args) == 1
        return [random.random() for i in xrange(args[0])]

class randInt(Function):
    def call(self, vm, args):
        assert len(args) in (2, 3)

        if args[0] > args[1]:
            args[0], args[1] = args[1], args[0]

        if len(args) == 2:
            return random.randint(*args)

        return [random.randint(*args[:2]) for i in xrange(args[2])]

class randNorm(Function):
    def call(self, vm, args):
        assert len(args) in (2, 3)

        if len(args) == 3:
            args, n = args[:2], args[2]
        else:
            n = 1

        return [random.normalvariate(*args) for i in xrange(n)]

class randBin(Function):
    def call(self, vm, args):
        raise NotImplementedError # numpy.random has a binomial distribution, or I could write my own...

class randM(Function):
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

    def bool(self, left, right):
        return left <= right

class LessOrEqualsToken(LessOrEquals):
    token = u'≤'

class GreaterOrEquals(Logic):
    token = '>='

    def bool(self, left, right):
        return left >= right

class GreaterOrEqualsToken(GreaterOrEquals):
    token = u'≥'

# string manipulation

class inString(Function):
    def call(self, vm, args):
        assert len(args) == 2 or len(args) == 3 and isinstance(args[2], (int, long))
        assert isinstance(args[0], basestring) and isinstance(args[1], basestring)
        haystack = args[0]
        needle = args[1]
        skip = 0
        if len(args) == 3:
            skip = args[2]
        return haystack.find(needle, skip)

class sub(Function):
    def call(self, vm, args):
        assert len(args) == 3
        s = args[0]
        a, b = args[1], args[2]
        assert a > 0 and b < len(s)
        return s[a - 1:a - 1 + b]

class length(Function):
    def call(self, vm, args):
        assert len(args) == 1
        return len(args[0])

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
                    raise StopError('If/Then could not find End on negative expression')
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
        assert isinstance(block, If)
        end = block.find_end(vm)
        if end:
            row, col, end = end
        else:
            raise StopError('Else could not find End')

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
            self.stop(vm, row, col)

    def stop(self, vm, row, col):
        vm.goto(row, col)
        end = self.find_end(vm)
        if end:
            row, col, end = end
        else:
            raise StopError('%s could not find End' % self.token)

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
            args = self.arg.contents[1:]

            if len(args) == 3:
                inc = vm.get(args[2])
                args = args[:2]
            else:
                inc = 1
            forward = inc > 0
            start, end = args

            if self.pos is None:
                self.pos = vm.get(start)
            else:
                self.pos += inc

            var.set(vm, self.pos)
            if forward and self.pos > vm.get(end) or not forward and self.pos < vm.get(end):
                return False
            else:
                return True
        else:
            raise ExecutionError('incorrect arguments to For loop')

    def stop(self, vm, row, col):
        self.pos = None
        Loop.stop(self, vm, row, col)

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
        for i, (row, col, block) in enumerate(reversed(vm.blocks)):
            if not isinstance(block, If):
                block.stop(vm, row, col)
                vm.blocks = vm.blocks[:-i - 1]
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
            label = unicode(arg.flatten())

        return unicode(label)

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

class Stop(Token):
    def run(self, vm):
        raise StopError

class Return(Token):
    def run(self, vm):
        raise ReturnError

# input/output

class ClrHome(Token):
    def run(self, vm):
        vm.io.clear()

class Float(Token):
    def run(self, vm):
        vm.fixed = -1

class Fix(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        assert self.arg is not None
        arg = vm.get(self.arg)
        assert arg >= 0

        vm.fixed = arg

class Disp(Token):
    absorbs = (Expression, Variable, Tuple)

    @staticmethod
    def format_matrix(data):
        if isinstance(data, int):
            return data
        out = '[' + str(data[0])
        for row in data[1:]:
            out += '\n ' + str(row)
        out += ']'
        return out

    def run(self, vm):
        cur = self.arg
        if not cur:
            self.disp(vm)
            return

        data = None
        if isinstance(cur, ListExpr):
            data = str(vm.get(cur))
        elif isinstance(cur, (MatrixExpr, Matrix)):
            data = self.format_matrix(vm.get(cur))
        elif isinstance(cur, Tuple):
            items = []
            for arg in cur.contents:
                data = vm.get(arg)
                if isinstance(arg, ListExpr):
                    items.append(str(data))
                elif isinstance(arg, (MatrixExpr, Matrix)):
                    items.append(self.format_matrix(data))
                else:
                    items.append(data)
            self.disp(vm, *items)
            return
        else:
            data = vm.get(cur)
        self.disp(vm, data)

    def disp(self, vm, *msgs):
        if not msgs:
            vm.io.disp()
            return
        for msg in msgs:
            vm.io.disp(vm.disp_round(msg))

class Print(Disp):
    absorbs = (Expression, Variable, Tuple)

    def disp(self, vm, *msgs):
        if isinstance(msgs, (tuple, list)):
            vm.io.disp(', '.join(str(vm.disp_round(x)) for x in msgs))
        else:
            vm.io.disp(vm.disp_round(msgs))

class Output(Function):
    def run(self, vm):
        assert len(self.arg) == 3
        row, col, msg = vm.get(self.arg)
        vm.io.output(row, col, vm.disp_round(msg))

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
        if isinstance(var, Expression):
            var = var.flatten()
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

    def prompt(self, vm, var, msg='?'):
        if isinstance(var, Str):
            is_str = True
        else:
            is_str = False

        val = vm.io.input(msg, is_str)
        var.set(vm, val)

class getKey(Variable):
    def get(self, vm):
        return vm.io.getkey()

class pgrm(Token):
    done = False

    def dynamic(self, char):
        if not self.done and char in string.uppercase:
            self.name += char
            return True
        self.done = True
        return False

    def __init__(self):
        self.name = ''

    def run(self, vm):
        vm.run_pgrm(self.name)

    def __repr__(self):
        return 'pgrm' + self.name

class REPL(Token):
    def run(self, vm):
        from parse import Parser, ParseError

        if vm.repl_serial != vm.serial:
            vm.repl_serial = vm.serial
            ans = vm.vars.get('Ans')
            if ans is not None:
                d = Disp()
                d.arg = Ans()
                d.run(vm)

        code = None
        while not code:
            repl_line = None
            while not repl_line:
                try:
                    repl_line = raw_input('>>> ')
                except KeyboardInterrupt:
                    print
                except EOFError:
                    code = [[EOF()]]
                    break

            if not code:
                try:
                    code = Parser(repl_line + '\n').parse()
                except ParseError, e:
                    print e

        for line in reversed(code):
            vm.code.insert(self.line, line)

        vm.line, vm.col = self.line, self.col

# date commands

class dayOfWk(Function):
    def call(self, vm, args):
        assert len(args) == 3
        date = datetime.datetime(year=args[0], month=args[1], day=args[2])
        return date.isoweekday() % 7 + 1

# file IO (not in original TI-Basic)

class ReadFile(Function):
    def call(self, vm, args):
        assert len(args) == 1
        return open(args[0], 'r').read()
