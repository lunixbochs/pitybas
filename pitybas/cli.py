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
    print 'Welcome to pitybas. Press Ctrl-D to exit.'
    print
    vm = Repl(history=20, io=io)

if options.verbose:
    vm.print_tokens()
    print
    print '-===[ Running %s ]===-' % args[0]

if options.ast:
    print_ast(vm)
    sys.exit(0)

try:
    vm.execute()
    if options.stacktrace:
        vm.print_stacktrace(options.vardump)
except KeyboardInterrupt:
    print
    vm.print_stacktrace(options.vardump)
except Exception, e:
    print
    print
    vm.print_stacktrace(options.vardump)

    print '%s on line %i:' % (e.__class__.__name__, vm.line),

    if isinstance(e, Error):
        print e.msg
    else:
        print
        print '-===[ Python traceback ]===-'
        print traceback.format_exc()
