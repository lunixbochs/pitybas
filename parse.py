SYMBOLS = '+-/*:^(){}[]<>.!'
TOKENS = [
	'If', 'Then', 'End', 'Goto', 'While', 'Repeat', 'Lbl',
	'Disp', 'Output', 'ClrHome',
	'and', 'or', 'xor', 'not'
	'>=', '<=', '->',
]

TOKENS.sort()
TOKENS.reverse()

class ParseError(Exception):
       def __init__(self, msg):
           self.msg = msg

       def __str__(self):
           return self.msg

class Parser:
	def __init__(self, source):
		self.source = source.replace('\r\n', '\n').replace('\r', '\n')
		self.length = len(source)
		self.pos = 0
		self.ast = []
	
	def error(self, msg):
		raise ParseError(msg)
	
	def inc(self, n=1):
		self.pos += n
	
	def more(self):
		return self.pos < self.length
	
	def parse(self):
		while self.more():
			char = self.source[self.pos]
			if char in ('\n', ':'):
				# new line
				# this needs to reset anything line-specific
				# like parens and quotes
				# maybe this will just turn into a RESET code
				self.inc()
				pass
			elif char in SYMBOLS:
				print 'parsed a symbol: %s' % self.symbol()
			elif '0' <= char <= '9':
				print 'parsed a number: %s' % self.number()
			elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
				print 'parsed a token: %s' % self.token()
			elif char == '"':
				print 'parsed a string: %s' % self.string()
			elif char in ' \t':
				self.inc()
			else:
				self.error('no tokenize path for: "%s"' % char)
	
	def symbol(self):
		token = self.token(True)
		if token:
			return token
		else:
			char = self.source[self.pos]
			self.inc()
			return char
	
	def token(self, sub=False):
		remaining = self.source[self.pos:]
		for token in TOKENS:
			if remaining.startswith(token):
				self.inc(len(token))
				return token
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
			
			if num[-1] == '.':
				pass # TODO: verify behavior of 1. and .1 on device

		return num
	
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