class Error(Exception):
	   def __init__(self, msg):
		   self.msg = msg

	   def __str__(self):
		   return self.msg

class ParseError(Error): pass
class ExecutionError(Error): pass
class ExpressionError(Error): pass

class Pri:
	# evaluation happens in the following order:
	# skip: expressions, functions, variables
	# 1. exponents, factorials
	# 2. multiplication, division
	# 3. addition, subtraction
	# 4. logic operators
	# 5. boolean operators
	# 6. variable setting

	# these won't be parsed into expressions at all
	INVALID = -2
	# NONE means store but don't execute directly
	# used for variables, lazy loading functions and expressions
	NONE = -1

	PROB = 0
	EXPONENT = 1
	MULTDIV = 2
	ADDSUB = 3

	LOGIC = 4
	BOOL = 5
	SET = 6

def test_number(num):
	return str(num).lstrip('-').replace('.', '', 1).isdigit()