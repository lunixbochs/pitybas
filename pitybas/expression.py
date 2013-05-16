import tokens
from common import ExpressionError, Pri, is_number

class Base:
    priority = Pri.NONE

    can_run = False
    can_set = False
    can_get = True
    can_fill_left = False
    can_fill_right = False
    absorbs = ()

    end = None

    def __init__(self):
        self.contents = []
        self.finished = False

    def append(self, token):
        if self.contents:
            prev = self.contents[-1]

            # the minus sign implies a * -1 when used by itself
            if isinstance(prev, tokens.Minus):
                # TODO: fix this the rest of the way
                if len(self.contents) == 1:
                    self.contents.pop()
                    self.contents += [tokens.Value(-1), tokens.Mult()]

            # absorb: tokens can absorb the next token from the expression if it matches a list of types
            elif isinstance(token, prev.absorbs):
                if isinstance(token, Base):
                    token = token.flatten()

                prev.absorb(token)
                return

            # implied multiplication
            elif prev.priority == token.priority == tokens.Pri.NONE:

                # negative numbers actually have implied addition
                if isinstance(token, tokens.Value)\
                    and is_number(token.value) and int(token.value) < 0:
                        self.contents.append(tokens.Plus())
                else:
                    self.contents.append(tokens.Mult())

        self.contents.append(token)

    def extend(self, array):
        for x in array:
            self.append(x)

    def flatten(self):
        if len(self.contents) == 1:
            first = self.contents[0]
            if isinstance(first, Base):
                return first.flatten()
            elif first.can_get:
                return first

        return self

    def fill(self):
        # TODO: instead of this system, perhaps tokens should be able to specify whether they need/want left/right params
        if not self.contents: return

        # if we don't have a proper variable:token:variable pairing in the token list,
        # this method will allow tokens to fill in an implied variable to their left or right
        new = []
        for i in xrange(len(self.contents)):
            t = self.contents[i]
            if (i % 2 == 0 and not t.can_get):
                left = None
                right = None

                if i > 0:
                    left = self.contents[i-1]
                    if not left.can_fill_right:
                        left = None

                right = self.contents[i]
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

        self.contents = new

    def validate(self):
        if not self.contents: return

        # figure out how to handle in-place tokens like the symbol for ^3
        # perhaps replace it with a ^3 so we can enforce (value, token, value)
        # or we can pad "in-place" tokens with a null to be passed as right

        # make sure expression is ordered (value, token, value, token, value)
        for i in xrange(len(self.contents)):
            t = self.contents[i]

            if (i % 2 == 0 and not t.can_get) or ( i % 2 == 1 and not t.can_run):
                raise ExpressionError('bad token order: %s' % self)

        # determine whether we have any tokens after a ->
        found_stor = False
        for i in xrange(len(self.contents)):
            t = self.contents[i]
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

        for i in xrange(len(self.contents)):
            token = self.contents[i]
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
        expr = self.contents[:]
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

    def close(self, char):
        for stack in reversed(self.contents):
            if isinstance(stack, Base):
                if stack.close(char):
                    return False

        if char == self.end and not self.finished:
            self.finish()
            return True

    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return 'E(%s)' % (' '.join(repr(token) for token in self.contents))

bracket_map = {'(':')', '{':'}', '[':']'}

class Expression(Base): pass

class Bracketed(Base):
    def __init__(self, end):
        self.end = bracket_map[end]
        Base.__init__(self)

    def __repr__(self):
        return 'B(%s)' % (' '.join(repr(token) for token in self.contents))

class ParenExpr(Bracketed):
    end = ')'

class Tuple(Base):
    priority = Pri.INVALID

    def __init__(self):
        Base.__init__(self)

    def append(self, expr):
        if isinstance(expr, Base):
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
        Bracketed.__init__(self, end)

    def __repr__(self):
        return 'A(%s)' % (', '.join(repr(expr) for expr in self.contents))

class FunctionArgs(Arguments):
    end = ')'

class ListExpr(Arguments):
    priority = Pri.NONE
    end = '}'

    def __repr__(self):
        return 'L{%s}' % (', '.join(repr(expr) for expr in self.contents))

class MatrixExpr(Arguments):
    priority = Pri.NONE
    end = ']'

    def __repr__(self):
        return 'M[%s]' % (', '.join(repr(expr) for expr in self.contents))

