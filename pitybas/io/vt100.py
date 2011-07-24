from pitybas.parse import Parser
from pitybas.common import ParseError

import sys, tty, termios

class VT:
	def __init__(self, width=16, height=8):
		self.width = width
		self.height = height
		self.clear()

		self.row, self.col = 1, 1
		self.pos_stack = []
	
	def push(self):
		self.pos_stack.append((self.row, self.col))
	
	def pop(self):
		self.row, self.col = self.pos_stack.pop()

	def e(self, *seqs):
		for seq in seqs:
			sys.stdout.write('\033'+seq)

	def clear(self, reset=True):
		self.e('[2J', '[H')
		self.row, self.col = 1, 1
		if reset:
			self.lines = []
			for i in xrange(self.height):
				self.lines.append([' ']*self.width)
	
	def scroll(self):
		self.lines.pop(0)
		self.lines.append([' ']*self.width)
		self.row = max(1, self.row - 1)
	
	def flush(self):
		self.clear(reset=False)
		sys.stdout.write('\n'.join(''.join(line) for line in self.lines))
	
	def move(self, row, col):
		self.row, self.col = row, col
		self.e('[%i;%iH' % (row, col))
	
	def wrap(self, msg):
		first = self.width - self.col + 1
		first, msg = msg[:first], msg[first:]
		lines = [first]
		while msg:
			lines.append(msg[:self.width])
			msg = msg[self.width:]
		
		return lines
	
	def write(self, msg, scroll=True):
		row, col = self.row, self.col
		self.e('[%i;%iH' % (row, col))

		for line in self.wrap(msg):
			if row > self.height:
				row -= 1

				if scroll:
					self.scroll()
					row, col = self.row, self.col
					self.flush()
					self.move(row, 1)
				else:
					break

			for char in line:
				self.lines[row-1][col-1] = char
				sys.stdout.write(char)
				col += 1
			
			col = 1
			row += 1
			sys.stdout.write('\n')
		
		self.row, self.col = row, col
	
	def output(self, row, col, msg):
		self.e('7')
		old = self.row, self.col
		self.move(row, col)
		self.write(msg)

		self.row, self.col = old
		self.e('8')

	def getch(self):
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		tty.setraw(sys.stdin.fileno())

		ch = sys.stdin.read(1)

		fd = sys.stdin.fileno()
		termios.tcsetattr(fd, termios.TCSANOW, old)
		return ch

class IO:
	def __init__(self, vm):
		self.vm = vm
		self.vt = VT()

	def clear(self):
		self.vt.clear()

	def input(self, msg, is_str=False):
		# TODO: implement this in VT terms
		while True:
			try:
				self.vt.push()
				self.vt.move(9, 1)

				if msg:
					print msg,

				line = raw_input()

				self.vt.flush()
				self.vt.pop()
				if not is_str:
					val = Parser.parse_line(self.vm, line)
				else:
					val = line

				return val
			except ParseError:
				print 'ERR:DATA'
				print

	def output(self, row, col, msg):
		self.vt.output(row, col, msg)

	def disp(self, msg=''):
		if isinstance(msg, (complex, int, float)):
			msg = str(msg).rjust(16)

		self.vt.write(msg)
	
	def pause(self, msg=''):
		if msg: self.disp(msg)
		self.input('[press enter]', True)
	
	def menu(self, menu):
		# menu is a tuple of (title, (desc, label)),
		# TODO: implement this in VT terms

		lookup = []
		while True:
			self.vt.clear(reset=False)
			i = 1

			for title, entries in menu:
				print '-[ %s ]-' % self.vm.get(title)
				for name, label in entries:
					print '%i: %s' % (i, self.vm.get(name))
					lookup.append(label)
					i += 1
				
			choice = raw_input('choice? ')
			print
			if choice.isdigit() and 0 < int(choice) <= len(lookup):
				label = lookup[int(choice)-1]
				self.vt.flush()
				return label
			else:
				print 'invalid choice'
