import sys, traceback
from optparse import OptionParser
from interpret import Interpreter, Repl
from common import Error
from pitybas.io.vt100 import IO as vt100

parser = OptionParser(usage='Usage: pb.py [options] filename')
parser.add_option('-a', '--ast', dest="ast", action="store_true", help="parse, print ast, and quit")
parser.add_option('-d', '--dump', dest="vardump", action="store_true", help="dump variables in stacktrace")
parser.add_option('-s', '--stacktrace', dest="stacktrace", action="store_true", help="always stacktrace")
parser.add_option('-v', '--verbose', dest="verbose", action="store_true", help="verbose output")
parser.add_option('-i', '--io', dest="io", help="select an IO system: simple (default), vt100")

(options, args) = parser.parse_args()

if len(args) > 1:
    parser.print_help()
    sys.exit(1)

io = None
if options.io == 'vt100':
    io = vt100

if args:
    vm = Interpreter.from_file(args[0], history=20, io=io)
else:
    print 'Welcome to pitybas.'
    print
    vm = Repl(history=20, io=io)

if options.verbose:
    print 'Token stream:'
    for line in vm.code:
        print (', '.join(repr(n) for n in line)).replace("u'", "'")
    print
    print '-===[ Running %s ]===-' % args[0]

def print_ast(vm, start=0, end=None):
    if end is None:
        end = len(vm.code)

    for i in xrange(max(start, 0), min(end, len(vm.code))):
        line = vm.code[i]
        print '{}: {}'.format(i, line)

def stacktrace(vm, num=None):
    if not num:
        num = vm.hist_len

    if vm.history:
        print
        print '-===[ Stacktrace ]===-'

    for row, col, cur in vm.history[-num:]:
        print ('[%i, %i]:' % (row, col)).ljust(9), repr(cur).replace("u'", '').replace("'", '')

    if vm.history:
        print

    print '-===[ Code (row {}, col {}) ]===-'.format(vm.line, vm.col)
    h = num / 2
    print_ast(vm, vm.line - h, vm.line + h)
    print

    if options.vardump and vm.vars:
        print
        print '-===[ Variable Dump ]===-'
        import pprint
        pprint.pprint(vm.vars)
        print

if options.ast:
    print_ast(vm)
    sys.exit(0)

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

