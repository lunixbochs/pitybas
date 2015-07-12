Disp "basic list"
{1,2,3}->lTEST
Disp lTEST
5->lTEST(1)
Disp lTEST

Disp "list copy"
{1}->l1
l1->l2
2->l2(1)
Disp l1
Disp l2

Disp "basic matrix"
[[1,2,3,4]]->[A]
Disp [A]
2->[A](1,1)
Disp [A]

Disp "dim get"
Disp dim(lTEST), dim([A])

Disp "dim set"
3->dim(l1)
Disp dim(l1), l1

{1,1}->dim([A])
Disp dim([A]), [A]
