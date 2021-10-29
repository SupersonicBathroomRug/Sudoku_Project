from itertools import product

from tracker import MustBe, local_to_global

def only_one_value(sudoku):
    # RULE: only 1 value can be written to this cell, as all others are present in this row+column+section
    made_deduction = False
    for i, j in product(range(9), range(9)):
        if sudoku.board[i][j]!=0: # left here to enable contradiction check
            continue
        tmp = sudoku.allowed[i][j] # which numbers are not present in this row+column+section?
        if len(tmp)==0: # if nothing is allowed in this empty cell: CONTRADICTION!
            print(f"cannot fill cell {i},{j}")
            return
        if len(tmp)==1: # if only a single value is allowed: FILL!
            ass =tmp.last_one()
            made_deduction |= sudoku.make_deduction(MustBe((i,j),ass),
                'allowed',tmp.notNones())
    return made_deduction

def only_this_cell(sudoku):
    # RULE: v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
    # ignoring already filled cells is done be make_deduction
    made_deduction = False
    for i, j in product(range(9), range(9)):
        if len(sudoku.rowpos[i][j]) == 1:
            made_deduction |= sudoku.make_deduction(MustBe((i,sudoku.rowpos[i][j].last_one()),j+1,'rowpos'),
                'rowpos',sudoku.rowpos[i][j].notNones())
        if len(sudoku.colpos[i][j])==1:
            made_deduction |= sudoku.make_deduction(MustBe((i,sudoku.colpos[i][j].last_one()),j+1,'colpos'),
                'colpos',sudoku.colpos[i][j].notNones())
        if len(sudoku.secpos[i][j])==1:
            p = local_to_global(i,*sudoku.secpos[i][j].last_one())
            made_deduction |= sudoku.make_deduction(MustBe((i,sudoku.secpos[i][j].last_one()),j+1,'secpos'),
                'secpos',sudoku.secpos[i][j].notNones())
    return made_deduction
