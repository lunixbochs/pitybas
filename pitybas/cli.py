import sys, traceback
from optparse import OptionParser
from interpret import Interpreter
from common import Error
from pitybas.io.vt100 import IO as vt100

parser = OptionParser(usage='Usage: pb.py [options] filename')
parser.add_option('-d', '--dump', dest="vardump", action="store_true", help="dump variables in stacktrace")
parser.add_option('-s', '--stacktrace', dest="stacktrace", action="store_true", help="always stacktrace")
parser.add_option('-v', '--verbose', dest="verbose", action="store_true", help="verbose output")
parser.add_option('-i', '--io', dest="io", help="select an IO system: simple (default), vt100")

(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

io = None
if options.io == 'vt100':
	io = vt100

vm = Interpreter.from_file(args[0], history=20, io=io)

if options.verbose:
	print 'Token stream:'
	for line in vm.code:
		print (', '.join(repr(n) for n in line)).replace("u'", "'")
	print
	print '-===[ Running %s ]===-' % args[0]

def stacktrace(vm, num=None):
	if not num: num = vm.hist_len

	print
	print '-===[ Stacktrace ]===-'
	for row, col, cur in vm.history[-num:]:
		print ('[%i, %i]:' % (row, col)).ljust(9), repr(cur).replace("u'", '').replace("'", '')

	if options.vardump:
		print
		print '-===[ Variable Dump ]===-'
		import pprint
		pprint.pprint(vm.vars)

try:
	vm.execute()
	if options.stacktrace:
		print
		stacktrace(vm)
except KeyboardInterrupt:
	print
	stacktrace(vm, 6)
except Exception, e:
	print
	print
	stacktrace(vm, 6)

	print '%s on line %i:' % (e.__class__.__name__, vm.line),

	if isinstance(e, Error):
		print e.msg
	else:
		print
		print '-===[ Python traceback ]===-'
		print traceback.format_exc()

