# -*- coding: utf-8 -*-
import string

SYMBOLS = [
	'+', '-', '*', '/', u'‾', '^', u'√',
	'=', u'≠', '>', u'≥', '<', u'≤',
	u'→', '!', u'π', '%', 'r', u'°',
	',', '(', ')', '[', ']', '{', '}',
]

TOKENS = [
	'>=', '<=', '->', u'¹', u'²', u'³',
	'and', 'Archive', 'AxesOff', 'AxesOn', 'a+bi',
	'Boxplot',
	'Clear Entries', 'ClockOff', 'ClockOn',
	'ClrAllLists', 'ClrDraw', 'ClrHome', 'ClrList', 'ClrTable',
	'Connected', 'CoordOff', 'CoordOn', 'CubicReg',
	u'►Dec', 'Degree', 'DelVar', 'DependAsk', 'DependAuto',
	'DiagnosticOff', 'DiagnosticOn', 'Disp', 'DispGraph',
	'DispTable', u'►DMS', 'Dot', 'DrawF', 'DrawInv',
	'e', 'E', 'Else', 'End', 'Eng', 'ExecLib', 'ExpReg',
	'ExprOff', 'ExprOn',
	'GarbageCollect', 'getDate', 'getDtFmt', 'getKey', 'getTime',
	'getTmFmt', 'Goto', 'GridOff', 'GridOn', 'G-T',
	'Histogram', 'Horiz', 'Horizontal',
	'i', 'If', 'IndpntAsk', 'IndpntAuto', 'Input', 'IsClockOn',
	u'∟', 'LabelOff', 'LabelOn', 'Lbl', 'LinReg(a+bx)', 'LinReg(ax+b)',
	'LinRegTInt', 'LinRegTTest', 'LnReg', 'Logistic',
	'Manual-Fit', 'Med-Med', 'ModBoxplot',
	'n', 'nCr', 'n/d', 'Normal', 'NormProbPlot', 'nPr',
	'or',
	'Param', 'Pause', 'PlotsOff', 'PlotsOn', 'Pmt_Bgn', 'Pmt_End',
	u'►Polar', 'Polar', 'PolarGC', 'prgm', 'Prompt', 'PwrReg',
	'QuadReg', 'QuartReg',
	'Radian', 'rand', u're^θi', 'Real', 'RecallGDB', 'RecallPic',
	u'►Rect', 'RectGC', 'Repeat', 'Return',
	'Scatter', 'Sci', 'Seq', 'Sequential', 'SetUpEditor', 'Simul',
	'SinReg', 'startTmr', 'Stop', 'StoreGDB', 'StorePic',
	'Then', 'Time', 'TInterval', 'Trace', 'T-Test', 'tvm_FV', 'tvm_I%',
	'tvm_N', 'tvm_Pmt', 'tvm_PV',
	'UnArchive', 'uvAxes', 'uwAxes',
	'Vertical', 'vwAxes',
	'Web', 'While',
	'xor', 'xyLine',
	'ZBox', 'ZDecimal', 'ZInteger', 'ZInterval', 'Zoom In', 'Zoom Out',
	'ZoomFit', 'ZoomRcl', 'ZoomStat', 'ZoomSto', 'ZPrevious', 'ZSquare',
	'ZStandard', 'ZTrig'
]

VARIABLES = [
	'Ans',
	'Xmin', 'Xmax', 'Ymin', 'Ymax', u'π'
]+list(string.uppercase)

FUNCTIONS = [
	u'√', u'³√',
	'augment', 'angle', 'ANOVA',
	'bal', 'binomcdf', 'binompdf',
	'checkTmr', u'χ²cdf', u'χ²pdf', u'χ²-Test', u'χ²GOF-Test',
	'Circle', 'conj', 'cos', u'cosֿ¹', 'cosh', u'coshֿ¹', 'cumSum',
	'dayOfWk', 'dbd', 'det', 'dim', 'DS<',
	'e^', u'►Eff', u'Equ►String', 'expr',
	'Fcdf', 'Fill', 'fMax', 'fMin', 'fnInt', 'For', 'fPart', 'Fpdf',
	'Fix', 'Float', 'FnOff', 'FnOn', u'►Frac', 'Full', 'Func',
	'gcd', 'geometcdf', 'geometpdf', 'Get', 'GetCalc', 'getDtStr',
	'getTmStr', 'GraphStyle',
	'identity', 'imag', 'inString', 'int', u'ΣInt', 'invNorm',
	'invT', 'iPart', 'irr', 'IS>',
	'lcm', 'length', 'Line', u'ΔList', u'List►matr', 'ln','log',
	'logBASE',
	u'Matr►list', 'max', 'mean', 'median', 'Menu', 'min',
	'nDeriv', u'►Nom', 'normalcdf', 'normalpdf', 'not', 'npv',
	'OpenLib', 'Output',
	'Plot1', 'Plot2', 'Plot3', 'poissoncdf', 'poissonpdf',
	u'ΣPrn', 'prod', 'Pt-Change', 'Pt-Off', 'Pt-On', 'Pxl-Change',
	'Pxl-Off', 'Pxl-On', 'pxl-Test', u'P►Rx', u'P►Ry',
	'randBin', 'randInt', 'randIntNoRep', 'randM', 'randNorm', 'real',
	'ref', 'remainder', 'round', '*row', 'row+', '*row+', 'rowSwap',
	'rref', u'R►Pr', u'R►Pθ',
	'Select', 'Send', 'seq', 'setDate', 'setDtFmt', 'setTime',
	'setTmFmt', 'Shade', u'Shadeχ²', 'ShadeF', 'ShadeNorm',
	'Shade_t', 'sin', u'sinֿ¹', 'sinh', u'sinhֿ¹', 'solve', 'SortA',
	'SortD', 'stdDev', u'String►Equ', 'sub', 'sum',
	'tan', u'tanֿ¹', 'Tangent', 'tanh', u'tanhֿ¹', 'tcdf', 'Text',
	'timeCnv', 'tpdf',
	'variance',
	'Z-Test',

	'Pt-On', 'For',
	'abs', 'min', 'max', 'sqrt'
]

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
		self.ast = []
	
	def clean(self):
		self.source = self.source.replace('\r\n', '\n').replace('\r', '\n')
	
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
				self.inc()
				self.line += 1
				continue
			elif char in ' \t':
				self.inc()
				continue
			elif char in SYMBOLS:
				result = self.symbol()
			elif '0' <= char <= '9':
				result = self.number()
			elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
				result = self.token()
			elif char == '"':
				result = self.string()
			else:
				self.error('could not tokenize: %s' % repr(char))
			
			self.add(result)
		
		for line in self.lines:
			print '"' + ('", "'.join(line)) + '"'
	
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
			
			if num[-1] == '.' or num[0] == '.':
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