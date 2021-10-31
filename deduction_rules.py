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
    made_deduction = False
    for row in range(9):
        cells_to_check = [(row,col) for col in range(9)]
        made_deduction |= func(cells_to_check)

    for col in range(9):
        cells_to_check = [(row,col) for row in range(9)]
        made_deduction |= func(cells_to_check)

    for sec in range(9):
        cells_to_check = [local_to_global(sec,i,j) for i,j in product(range(3),range(3))]
        made_deduction |= func(cells_to_check)
    return made_deduction

def _ban_numbers(sudoku, cell,numbers,rule, cells_used):
    made_deduction = False
    for number in numbers:
        made_deduction |= sudoku.ban(cell[0],cell[1],number,rule,cells_used)
    return made_deduction

def _allowed_numbers(sudoku, cells):
    """Returns a list where i-th element contains the allowed numbers in cells[i]"""
    allowed_numbers = []
    for cell in cells:
        if sudoku.board[cell[0]][cell[1]] != 0:
            allowed_numbers.append((sudoku.board[cell[0]][cell[1]],))
        else:
            allowed_numbers.append(tuple(sudoku.allowed[cell[0]][cell[1]].allowed()))
    return allowed_numbers


def nake_pair(sudoku):
    """RULE: if v and w can be written only to two cells in this row/col/sec, then remove it from the other cells of the row/col/sec."""
    
    def search_for_nake_pairs(elems):
        """Returns a list of 2-tuples, where every tuple contains the indeces of the same input"""
        return [(i,j) for i in range(len(elems)) for j in range(i+1,len(elems)) if len(elems[i])==2 and elems[i]==elems[j]]
    
    def search_and_ban_in_subset(cells_to_check):
        """Searches all nake-pairs in a subset of cells and bans these numbers from the other elements of subset."""
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        nake_pairs = search_for_nake_pairs(allowed_numbers)
        for pair in nake_pairs:
            current_naked_cell1 = cells_to_check[pair[0]]
            current_naked_cell2 = cells_to_check[pair[1]]
            deleted_numbers = sudoku.allowed[current_naked_cell1[0]][current_naked_cell1[1]].allowed()
            cells_used = sudoku.allowed[current_naked_cell1[0]][current_naked_cell1[1]].notNones()+sudoku.allowed[current_naked_cell2[0]][current_naked_cell2[1]].notNones()
            for cell in cells_to_check:
                if cell not in (cells_to_check[pair[0]],cells_to_check[pair[1]]):
                    made_deduction |= _ban_numbers(sudoku,cell,deleted_numbers,"nake_pair",cells_used)
        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)

def hidden_pair(sudoku):
    def search_hidden_pairs(elems):
        where_can_go = {i:[] for i in range(1,10)} # i-th number in which indeces of elems can go
        for idx,elem in enumerate(elems):
            for num in elem:
                where_can_go[num].append(idx)

        two_potential_place = {k: tuple(v) for k,v in where_can_go.items() if len(v)==2}
        triple_pairs = set([pair for pair in two_potential_place.values() if list(two_potential_place.values()).count(pair) >= 3])
        if len(triple_pairs)>0 :
            raise Exception("Contradiction in hidden pair") # TODO: better error handle
        double_pairs = set([pair for pair in two_potential_place.values() if list(two_potential_place.values()).count(pair) == 2])
        return {pair: tuple([k for k,v in two_potential_place.items() if v==pair]) for pair in double_pairs}

    def search_and_ban_in_subset(cells_to_check):
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        pairs = search_hidden_pairs(allowed_numbers)
        for pair,except_nums in pairs.items():
            current_hidden_cell0 = cells_to_check[pair[0]]
            current_hidden_cell1 = cells_to_check[pair[1]]
            cells_used = sudoku.allowed[current_hidden_cell0[0]][current_hidden_cell0[1]].notNones()+sudoku.allowed[current_hidden_cell1[0]][current_hidden_cell1[1]].notNones()
            made_deduction |= _ban_numbers(sudoku, current_hidden_cell0, filter(lambda x: x not in except_nums, allowed_numbers[pair[0]]), "hidden_pair",cells_used)
            made_deduction |= _ban_numbers(sudoku, current_hidden_cell1, filter(lambda x: x not in except_nums, allowed_numbers[pair[1]]), "hidden_pair",cells_used)

        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)
