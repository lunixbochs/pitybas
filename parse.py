# -*- coding: utf-8 -*-
import tokens
import interpret

LOOKUP = {}
LOOKUP.update(tokens.Token.tokens)
LOOKUP.update(tokens.Variable.tokens)
LOOKUP.update(tokens.Function.tokens)

SYMBOLS = []
TOKENS = tokens.Token.tokens.keys()
VARIABLES = tokens.Variable.tokens.keys()
FUNCTIONS = tokens.Function.tokens.keys()

FUNCTIONS = [func+'(' for func in FUNCTIONS]
TOKENS += VARIABLES + FUNCTIONS

TOKENS.sort()
TOKENS.reverse()

for t in TOKENS:
	if not t[0] in SYMBOLS and not t.isalpha():
		SYMBOLS.append(t[0])

class ParseError(Exception):
       def __init__(self, msg):
           self.msg = msg

       def __str__(self):
           return self.msg

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
	
	def cleanup(self):
		for line in self.lines:
			if line:
				new = []
				expr = None
				for token in line:
					if token.priority > tokens.Pri.INVALID:
						expr = expr or interpret.Expression()
						expr.append(token)
					else:
						if expr:
							new.append(expr)

						expr = None
						new.append(token)
				
				if expr:
					new.append(expr)
				
				yield new
	
	def parse(self):
		while self.more():
			char = self.source[self.pos]
			if char in ('\n', ':'):
				self.inc()
				self.line += 1
				continue
			elif char in ' \t':
				self.inc()
				continue
			elif char in SYMBOLS:
				result = self.symbol()
			elif '0' <= char <= '9':
				result = tokens.Value(self.number())
			elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
				result = self.token()
			elif char == '"':
				result = tokens.Value(self.string())
			else:
				self.error('could not tokenize: %s' % repr(char))
			
			# TODO: handle parens, use the stack for them
			# functions push the stack into argument mode
			# open paren outside a function pushes the stack into expression mode
			# TODO: check for comma here, turn it into a tuple if we find one (used for Disp and functions)

			self.add(result)
		
		return [line for line in self.cleanup()]
	
	def add(self, token):
		while self.line >= len(self.lines):
			self.lines.append([])
		
		self.lines[self.line].append(token)
	
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

	
	def token(self, sub=False):
		remaining = self.source[self.pos:]
		for token in TOKENS:
			if remaining.startswith(token):
				self.inc(len(token))
				return LOOKUP[token]()
		else:
			if not sub:
				near = remaining[:8].split('\n',1)[0]
				self.error('no token found at pos %i near "%s"' % (self.pos, near))
	
	def number(self, dot=True):
		num = ''
		while self.more():
			char = self.source[self.pos]
			if not char.isdigit():
				break

			num += char
			self.inc()
		
		if char == '.' and dot:
			num += '.'
			self.inc()

			num += self.number(False)
			
			if num[-1] == '.' or num[0] == '.':
				pass # TODO: verify behavior of 1. and .1 on device

		return float(num)
	
	def string(self):
		ret = ''
		self.inc()

		while self.more():
			char = self.source[self.pos]
			if char == '"':
				self.inc()
				break

			elif char in ('\n', ':'):
				break
			
			ret += char
			self.inc()

		return ret