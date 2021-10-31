from itertools import product

from tracker import MustBe, local_to_global

def only_one_value(sudoku):
    """RULE: only 1 value can be written to this cell, as all others are present in this row+column+section"""
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
    """RULE: v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
    ignoring already filled cells is done be make_deduction"""
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

def _apply_for_nines(func):
    for row in range(9):
        cells_to_check = [(row,col) for col in range(9)]
        func(cells_to_check)

    for col in range(9):
        cells_to_check = [(row,col) for row in range(9)]
        func(cells_to_check)

    for sec in range(9):
        cells_to_check = [local_to_global(sec,i,j) for i,j in product(range(3),range(3))]
        func(cells_to_check)

def ban_numbers(sudoku, row,col,numbers,rule, cells_used):
    for number in numbers:
        sudoku.ban(row,col,number,rule,cells_used)

def nake_pair(sudoku):
    """RULE: if v and w can be written only to two cells in this row/col/sec, then remove it from the other cells of the row/col/sec."""
    made_deduction = False
    
    def search_for_nake_pairs(elems):
        """Returns a list of 2-tuples, where every tuple contains the indeces of the same input"""
        return [(i,j) for i in range(len(elems)) for j in range(i+1,len(elems)) if len(elems[i])==2 and elems[i]==elems[j]]
    
    def search_and_ban_in_subset(cells_to_check):
        """Searches all nake-pairs in a subset of cells and bans these numbers from the other elements of subset."""
        allowed_numbers = []
        for cell in cells_to_check:
            if sudoku.board[cell[0]][cell[1]] != 0:
                allowed_numbers.append((sudoku.board[cell[0]][cell[1]],))
            else:
                allowed_numbers.append(tuple(sudoku.allowed[cell[0]][cell[1]].allowed()))
        nake_pairs = search_for_nake_pairs(allowed_numbers)
        for pair in nake_pairs:
            current_naked_cell1 = cells_to_check[pair[0]]
            current_naked_cell2 = cells_to_check[pair[1]]
            deleted_numbers = sudoku.allowed[current_naked_cell1[0]][current_naked_cell1[1]].allowed()
            cells_used = sudoku.allowed[current_naked_cell1[0]][current_naked_cell1[1]].notNones()+sudoku.allowed[current_naked_cell2[0]][current_naked_cell2[1]].notNones()
            for cell in cells_to_check:
                if cell not in (cells_to_check[pair[0]],cells_to_check[pair[1]]):
                    made_deduction = True
                    ban_numbers(sudoku,cell[0],cell[1],deleted_numbers,"nake_pair",cells_used)

    _apply_for_nines(search_and_ban_in_subset)
    
    return made_deduction


