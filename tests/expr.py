import path; path.go()

from interpret import Expression
from tokens import Value, Mult, Plus

e = Expression()
e.extend([Value(2), Mult(), Value(3), Plus(), Value(4), Mult(), Value(-1)])
print e.order()
print e.run(None)