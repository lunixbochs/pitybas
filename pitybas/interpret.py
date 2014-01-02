from collections import defaultdict
import time
import traceback

from parse import Parser, ParseError
from tokens import EOF, Value, REPL
from common import ExecutionError, StopError, ReturnError

from pitybas.io.simple import IO
from expression import Base

class Interpreter(object):
    @classmethod
    def from_string(cls, string, *args, **kwargs):
        code = Parser(string).parse()
        return Interpreter(code, *args, **kwargs)

    @classmethod
    def from_file(cls, filename, *args, **kwargs):
        string = open(filename, 'r').read().decode('utf8')
        return Interpreter.from_string(string, *args, **kwargs)

    def __init__(self, code, history=10, io=None):
        if not io: io = IO
        self.io = io(self)

        self.code = code
        self.code.append([EOF()])
        self.line = 0
        self.col = 0
        self.expression = None
        self.blocks = []
        self.running = []
        self.history = []
        self.hist_len = history

        self.vars = {}
        self.lists = defaultdict(list)
        self.matrix = {}
        self.fixed = -1

        self.serial = 0
        self.repl_serial = 0

    def cur(self):
        return self.code[self.line][self.col]

    def inc(self):
        self.col += 1
        if self.col >= len(self.code[self.line]):
            self.col = 0
            return self.inc_row()

        return self.cur()

    def inc_row(self):
        self.line = min(self.line+1, len(self.code)-1)
        self.expression = None
        return self.cur()

    def get_var(self, var):
        return self.vars[var]

    def set_var(self, var, value):
        if isinstance(value, (Value, Base)):
            value = value.get(self)

        self.vars[var] = value
        return value

    def get_matrix(self, name):
        return self.matrix[name]

    def set_matrix(self, name, value):
        self.matrix[name] = value

    def get_list(self, name):
        return self.lists[name]

    def set_list(self, name, value):
        self.lists[name] = value

    def push_block(self, block=None):
        if not block and self.running:
            block = self.running[-1]

        if block:
            self.blocks.append(block)
        else:
            raise ExecutionError('tried to push an invalid block to the stack')

    def pop_block(self):
        if self.blocks:
            return self.blocks.pop()
        else:
            raise ExecutionError('tried to pop an empty block stack')

    def find(self, *types, **kwargs):
        if 'wrap' in kwargs:
            wrap = kwargs['wrap']
        else:
            wrap = False

        if 'pos' in kwargs:
            pos = kwargs['pos']
        else:
            pos = self.line

        def y(i):
            line = self.code[i]
            if line:
                cur = line[0]
                if isinstance(cur, types):
                    return i, 0, cur

        for i in xrange(pos, len(self.code)):
            ret = y(i)
            if ret: yield ret

        if wrap:
            for i in xrange(0, pos):
                ret = y(i)
                if ret: yield ret

    def goto(self, row, col):
        if row >= 0 and row < len(self.code)\
            and col >= 0 and col < len(self.code[row]):
                self.line = row
                self.col = col
        else:
            raise ExecutionError('cannot goto (%i, %i)' % (row, col))

    def get(self, *var):
        ret = []
        for v in var:
            val = v.get(self)
            if isinstance(val, complex):
                if not val.imag:
                    val = val.real

            if isinstance(val, (float)):
                # TODO: perhaps limit precision here
                i = int(val)
                if val == i:
                    val = i

            ret.append(val)

        if len(ret) == 1:
            return ret[0]

        return ret

    def disp_round(self, num):
        if not isinstance(num, (int, float, complex)):
            return num

        if self.fixed < 0:
            return num
        else:
            return round(num, self.fixed)

    def run(self, cur):
        self.history.append((self.line, self.col, cur))
        self.history = self.history[-self.hist_len:]

        cur.line, cur.col = self.line, self.col

        if cur.can_run:
            self.running.append((self.line, self.col, cur))
            self.inc()
            cur.run(self)
            self.running.pop()
        elif cur.can_get:
            self.inc()
            self.set_var('Ans', cur.get(self))
            self.serial = time.time()
        else:
            raise ExecutionError('cannot seem to run token: %s' % cur)

    def execute(self):
        with self.io:
            try:
                while not isinstance(self.cur(), EOF):
                    cur = self.cur()
                    self.run(cur)
            except StopError, e:
                if e.message:
                    print
                    print 'Stopped:', e.message
            except ReturnError, e:
                if e.message:
                    print
                    print 'Returned:', e.message

        print

class Repl(Interpreter):
    def __init__(self, code=[], **kwargs):
        super(Repl, self).__init__(code, **kwargs)
        self.code.insert(-2, [REPL()])

    def execute(self):
        while not isinstance(self.cur(), EOF):
            try:
                super(Repl, self).execute()
            except ParseError, e:
                print e
            except:
                print traceback.format_exc()
