1->X
1->Y
While 1

Output(Y, X, "O")
getKey->K

If K>=24 and K<=26 or K=34
Output(Y, X, " ")

If K=24
max(1,X-1)->X

If K=25
max(1,Y-1)->Y

If K=26
min(16,X+1)->X

If K=34
min(8,Y+1)->Y

End