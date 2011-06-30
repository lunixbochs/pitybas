source = '''
If A < 3
Then
Disp "spam"
End
'''

from parse import Parser
parser = Parser(source)
parser.parse()