import sys
from optparse import OptionParser

parser = OptionParser(usage='Usage: pb.py [options] filename')
parser.add_option('-v', '--verbose', dest="verbose", action="store_true", help="verbose output")

(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

from interpret import Interpreter
vm = Interpreter.from_file(args[0])

if options.verbose:
	print 'Token stream:'
	for line in vm.code:
		print (', '.join(repr(n) for n in line)).replace("u'", "'")
	print
	print '-==[ Running %s ]==-' % args[0]

vm.execute()
