import sys, traceback
from optparse import OptionParser
from interpret import Interpreter
from common import Error

parser = OptionParser(usage='Usage: pb.py [options] filename')
parser.add_option('-v', '--verbose', dest="verbose", action="store_true", help="verbose output")
parser.add_option('-s', '--stacktrace', dest="stacktrace", action="store_true", help="always stacktrace")

(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

vm = Interpreter.from_file(args[0])
vm.hist_len = 20

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
		print ('[%i, %i]:' % (row, col)).ljust(9), repr(cur).replace("u'", '').replace("'", '').replace('E(', '(')

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

	print 'Error on line %i:' % (vm.line),

	if isinstance(e, Error):
		print e.msg
	else:
		print
		print '-===[ Python traceback ]===-'
		print traceback.format_exc()

