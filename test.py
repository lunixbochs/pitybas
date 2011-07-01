import sys
if len(sys.argv) < 2:
	print 'Usage: python test.py [file]'
	sys.exit(1)

f = open(sys.argv[1], 'r')
source = f.read().decode('utf8')
f.close()

from parse import Parser
parser = Parser(source)
parser.parse()
