Disp "string constant:"
Disp "spam"

Disp "string concatenation:"
Disp "eggs" + " foo"

Disp "expression with parens"
Disp ((1 + 2) + 3) * 4

Disp "unterminated brackets"
Disp ((1 + 2

Disp "logic operators"
Disp 1 < 3 and 4 > 3

Disp "variable set, implied multiplication"
2->A
1->B
Disp AB

Disp "-> should close all brackets (this should Disp 6)"
3+(1+2->C
Disp C

Disp "->D->E"
1->D->E
Disp D + E

Disp "comma Disp test"
Disp 1, 2, 3, "four!"

Disp "function test"
Disp(1, 2

Disp "goto test
Goto(27, 0
Disp "will be skipped"
Disp "this should disp"