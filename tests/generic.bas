Disp "string constant:"
Disp "spam"
Disp

Disp "string concatenation:"
Disp "eggs" + " foo"
Disp

Disp "expression with parens"
Disp ((1 + 2) + 3) * 4
Disp

Disp "unterminated brackets"
Disp ((1 + 2
Disp

Disp "logic operators"
Disp 1 < 3 and 4 > 3
Disp

Disp "variable set, implied multiplication"
2->A
1->B
Disp AB
Disp

Disp "-> should close all brackets (this should Disp 6)"
3+(1+2->C
Disp C
Disp

Disp "->D->E"
1->D->E
Disp D + E
Disp

Disp "comma Disp test"
Disp 1, 2, 3, "four!"
Disp

Disp "goto test
Goto A
Disp "this should not display"
Lbl A
Disp "this should display"
Disp

Disp "If without Then test"
If 1
Disp "phase one succeeded"
If 0
Disp "phase two failed"
Disp