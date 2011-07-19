# -*- coding: utf-8 -*-
import tokens
from errors import ParseError
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
	
	def more(self):
		return self.pos < self.length
	
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
							if isinstance(token, Value) and str(value).replace('-', '', 1).replace('.', '', 1).isdigit() and int(value) < 0:
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
					last = new[0]
					pops = []
					for i in xrange(1, len(new)):
						token = new[i]
						for typ in last.absorbs:
							if isinstance(token, typ):
								last.absorb(token)
								pops.append(i)
						
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
					stack = self.stack[-1]

					if stack.end == char:
						result = self.stack.pop()
						result.finish()
						self.inc()
					else:
						self.error('tried to end \'%s\' with: "%s" (expecting "%s")' % (stack, char, stack.end))
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
				
				self.inc()
				continue
			elif '0' <= char <= '9' or isinstance(self.token(inc=False), tokens.Minus):
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
	
	def number(self, dot=True):
		num = ''
		first = True
		while self.more():
			char = self.source[self.pos]
			if char == '-' and first: pass
			elif not char.isdigit():
				break

			first = False
			num += char
			self.inc()

		if char == '.' and dot:
			num += '.'
			self.inc()

			num += self.number(False)
			
			if num[-1] == '.' or num[0] == '.':
				pass # TODO: verify behavior of 1. and .1 on device

		f, i = float(num), int(num)
		if f != i:
			return f
		else:
			return i
	
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
