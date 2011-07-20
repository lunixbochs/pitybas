# -*- coding: utf-8 -*-
import tokens
from common import ParseError
from expression import Expression, Bracketed, Arguments, Tuple

LOOKUP = {}
LOOKUP.update(tokens.Token.tokens)
LOOKUP.update(tokens.Variable.tokens)
LOOKUP.update(tokens.Function.tokens)

SYMBOLS = []
TOKENS = tokens.Token.tokens.keys()
VARIABLES = tokens.Variable.tokens.keys()
FUNCTIONS = tokens.Function.tokens.keys()
TOKENS += VARIABLES + FUNCTIONS

TOKENS.sort()
TOKENS.reverse()

for t in TOKENS:
	if not t[0] in SYMBOLS and not t.isalpha():
		SYMBOLS.append(t[0])

def test_number(num):
	return str(num).lstrip('-').replace('.', '', 1).isdigit()

class Parser:
	def __init__(self, source):
		self.source = unicode(source)
		self.length = len(source)
		self.pos = 0
		self.line = 0
		self.lines = []

		self.stack = []
	
	def clean(self):
		self.source = self.source.replace('\r\n', '\n').replace('\r', '\n')
	
	def error(self, msg):
		raise ParseError(msg)
	
	def inc(self, n=1):
		self.pos += n
	
	def more(self, pos=None):
		if pos is None: pos = self.pos
		return pos < self.length
	
	def post(self):
		for line in self.lines:
			if line:
				new = []
				expr = None
				last_none = False
				for token in line:
					none = (token.priority == tokens.Pri.NONE)

					if token.priority > tokens.Pri.INVALID:
						expr = expr or Expression()
						if none and last_none:
							# fill in implied multiplication
							# negative numbers actually have implied addition
							if isinstance(token, tokens.Value)\
								and test_number(token.value) and int(token.value) < 0:
									expr.append(tokens.Plus())
							else:
								expr.append(tokens.Mult())

						expr.append(token)
					else:
						if expr:
							new.append(expr)

						expr = None
						new.append(token)
					
					last_none = none
				
				if expr:
					new.append(expr)
				
				if new:
					# implied expressions need to be added to tuples in their entirety, instead of just their last element
					pops = []
					for i in xrange(0, len(new)-1):
						e, t = new[i], new[i+1]
						if isinstance(e, Expression) and isinstance(t, Tuple):
							pops.append(i)
							e.append(t.contents[0])
							t.contents[0] = e

					for p in reversed(sorted(pops)):
						new.pop(p)

					# tokens with the absorb mechanic can steal the next token from the line if it matches a list of types
					last = new[0]
					pops = []
					for i in xrange(1, len(new)):
						token = new[i]
						for typ in last.absorbs:
							if isinstance(token, typ):
								last.absorb(token)
								pops.append(i)
								break
						
						last = token
					
					for p in reversed(sorted(pops)):
						new.pop(p)

				yield new

	def parse(self):
		while self.more():
			char = self.source[self.pos]

			if char in ('\n', ':'):
				self.close_brackets()

				self.inc()
				self.line += 1
				continue
			elif char in ' \t':
				self.inc()
				continue
			elif char in '([{':
				self.stack.append(Bracketed(char))
				self.inc()
				continue
			elif char in ')]}':
				if self.stack:
					stacks = []
					l = len(self.stack)
					for i in xrange(l):
						stack = self.stack.pop(l-i-1)
						if isinstance(stack, Bracketed):
							if stack.end == char:
								for s in stacks:
									stack.append(s)
									
								result = stack
								stack.finish()
								self.inc()
							else:
								self.error('tried to end \'%s\' with: "%s" (expecting "%s")' % (stack, char, stack.end))
						else:
							stacks.append(stack)
				else:
					self.error('encountered "%s" but we have no expression on the stack to terminate' % char)
			elif char == ',':
				line = self.lines[-1]
				if len(self.stack) > 1 and isinstance(self.stack[-2], Tuple):
					expr = self.stack.pop()
					self.stack[-1].append(expr)
				elif self.stack and isinstance(self.stack[-1], Tuple):
					pass
				else:
					if self.lines[-1]:
						token = self.lines[-1].pop()
					else:
						self.error('Encountered comma, but cannot find anything to put in the tuple')

					tup = Tuple()
					tup.append(token)
					self.stack.append(tup)
				
				if isinstance(self.stack[-1], Arguments):
					self.stack.append(Expression())

				self.inc()
				continue
			elif '0' <= char <= '9'	or isinstance(self.token(sub=True, inc=False), tokens.Minus) and self.number(test=True):
				result = tokens.Value(self.number())
			elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
				result = self.token()
			elif char in SYMBOLS:
				result = self.symbol()
			elif char == '"':
				result = tokens.Value(self.string())
			else:
				self.error('could not tokenize: %s' % repr(char))

			if isinstance(result, tokens.Store):
				self.close_brackets()

			self.add(result)

			# functions push the stack into argument mode
			if isinstance(result, tokens.Function):
				args = Arguments('(')
				self.stack.append(args)
				self.stack.append(Expression())
				result.absorb(args)

		self.close_brackets()
		return [line for line in self.post()]
	
	def add(self, token):
		# TODO: cannot add Pri.INVALID unless there's no expr on the stack
		if self.stack:
			stack = self.stack[-1]
			stack.append(token)
		elif not isinstance(token, Arguments):
			while self.line >= len(self.lines):
				self.lines.append([])

			self.lines[self.line].append(token)
	
	def close_brackets(self):
		while self.stack:
			self.add(self.stack.pop())

	def symbol(self):
		token = self.token(True)
		if token:
			return token
		else:
			char = self.source[self.pos]
			if char in LOOKUP:
				self.inc()
				return LOOKUP[char]()
			else:
				# a second time to throw the error
				self.token()

	
	def token(self, sub=False, inc=True):
		remaining = self.source[self.pos:]
		for token in TOKENS:
			if remaining.startswith(token):
				if inc:
					self.inc(len(token))
				return LOOKUP[token]()
		else:
			if not sub:
				near = remaining[:8].split('\n',1)[0]
				self.error('no token found at pos %i near "%s"' % (self.pos, near))
	
	def number(self, dot=True, test=False, inc=True):
		num = ''
		first = True
		pos = self.pos
		while self.more(pos):
			char = self.source[pos]
			if char == '-' and first: pass
			elif not char.isdigit():
				break

			first = False
			num += char
			pos += 1

		if char == '.' and dot:
			num += '.'
			pos += 1

			self.pos, tmp = pos, self.pos
			num += str(self.number(dot=False))
			self.pos = tmp

		if inc and not test: self.pos = pos

		if test_number(num):
			if test: return True
			f, i = float(num), int(num)
			if f != i:
				return f
			else:
				return i
		else:
			if test: return False
			raise ParseError('invalid number ending at pos %i: %s' % (self.pos, num))
	
	def string(self):
		ret = ''
		self.inc()

		while self.more():
			char = self.source[self.pos]
			if char == '"':
				self.inc()
				break

			elif char == '\n':
				break
			
			ret += char
			self.inc()

		return ret
