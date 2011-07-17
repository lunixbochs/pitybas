import sys, os
if len(sys.argv) < 2:
	print 'Usage: python parser.py [file]'
	sys.exit(1)

import path; path.go()
if not os.path.exists(sys.argv[1]):
	test = os.path.join('tests', sys.argv[1])
	if os.path.exists(test):
		sys.argv[1] = test

from interpret import Interpreter
vm = Interpreter.from_file(sys.argv[1])

print 'Token stream:'
for line in vm.code:
	print (', '.join(repr(n) for n in line)).replace("u'", "'")
print
print 'Running...'
print

vm.run()