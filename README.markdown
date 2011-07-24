pitybas
=======
A working TI-BASIC interpreter, written in Python.

Currently, all `.bas` files in tests/ run except circle.bas (due to lack of graph screen functions)

	Usage: pb.py [options] filename

	Options:
		-h, --help        show this help message and exit
		-d, --dump        dump variables in stacktrace
		-s, --stacktrace  always stacktrace
		-v, --verbose     verbose output
		-i IO, --io=IO    select an IO system: simple (default), vt100

