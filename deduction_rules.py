import itertools
from itertools import product
from tracker import MustBe
from util import cell_section, local_to_global


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

def _ban_numbers(sudoku, cell,numbers,rule, cells_used,details=None):
    made_deduction = False
    for number in numbers:
        made_deduction |= sudoku.ban(cell[0],cell[1],number,rule,cells_used,details)
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
            cell1 = cells_to_check[pair[0]]
            cell2 = cells_to_check[pair[1]]
            deleted_numbers = sudoku.allowed[cell1[0]][cell1[1]].allowed()
            cells_used = sudoku.allowed[cell1[0]][cell1[1]].notNones()+sudoku.allowed[cell2[0]][cell2[1]].notNones()
            for cell in cells_to_check:
                if cell not in (cells_to_check[pair[0]],cells_to_check[pair[1]]):
                    made_deduction |= _ban_numbers(sudoku,cell,deleted_numbers,"nake_pair",cells_used)
        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)

def hidden_pair(sudoku):
    """RULE: if only v and w has number x and y then delete every number from v and w except x and y."""
    def search_hidden_pairs(elems):
        where_can_go = {i:[] for i in range(1,10)} # i-th number in which indices of elems can go
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

def square_line(sudoku):
    '''RULE: if number can only go in one line within square ban that number from rest of the line'''
    made_deduction=False
    for sec in range(9):
        for val in range(9):
            places=sudoku.secpos[sec][val].allowed()
            #for row
            if len(set((i for i,j in places)))==1:
                row,_=local_to_global(sec,*places[0])
                reason=[info for key, info in sudoku.secpos[sec][val].items() if key[0] != row and info is not None]
                for col in range(9):
                    if col//3!=sec%3: #trust me, I'm an engineer
                        made_deduction|=sudoku.ban(row,col,val+1,"square_line",reason,details={'rc':'row', 'line':row, 'sec': sec})
            #for col
            if len(set((j for i,j in places)))==1:
                _,col=local_to_global(sec,*places[0])
                reason = [info for key, info in sudoku.secpos[sec][val].items() if key[1] != col and info is not None]
                for row in range(9):
                    if row//3!=sec//3:
                        made_deduction|=sudoku.ban(row,col,val+1,"square_line",reason,details={'rc':'col', 'line':row, 'sec': sec})
    return made_deduction

def line_square(sudoku):
    '''RULE: if number can only go in one square within a line ban that number from rest of the line'''
    made_deduction=False
    for row in range(9):
        for val in range(9):
            places=sudoku.rowpos[row][val].allowed()
            if len(set(i//3 for i in places))==1:
                sec=cell_section(row,places[0])
                reason=[info for key, info in sudoku.rowpos[row][val].items() if key // 3 != places[0] // 3 and info is not None]
                for i,j in product(range(3),range(3)):
                    r,c=local_to_global(sec,i,j)
                    if r!=row:
                        made_deduction|=sudoku.ban(r,c,val+1,"line_square",reason,details={'rc':'row', 'line':row, 'sec': sec})
    for col in range(9):
        for val in range(9):
            places=sudoku.colpos[col][val].allowed()
            if len(set(i//3 for i in places))==1:
                sec=cell_section(places[0],col)
                reason=[info for key, info in sudoku.rowpos[col][val].items() if key // 3 != places[0] // 3 and info is not None]
                for i,j in product(range(3),range(3)):
                    r,c=local_to_global(sec,i,j)
                    if c!=col:
                        made_deduction|=sudoku.ban(r,c,val+1,"line_square",reason,details={'rc':'col', 'line':col, 'sec': sec})
    return made_deduction

def xwing(sudoku):
    '''RULE: if for two rows/cols a given number can only go in 2 places each and these 4 places form a rectangle then ban given number from corresponding cols/rows'''
    made_deduction=False
    for val in range(9):
        #rows with 2
        possible={i:sudoku.rowpos[i][val].allowed() for i in range(9) if len(sudoku.rowpos[i][val])==2}
        for i,j in itertools.combinations(possible.keys(),2):
            if possible[i]==possible[j]:
                reason = sudoku.rowpos[i][val].notNones() + sudoku.rowpos[j][val].notNones()
                for r in range(9):
                    for c in possible[i]:
                        if r!=i and r!=j:
                            made_deduction|=sudoku.ban(r,c,val+1,"xwing",reason,details={'rc':'rows', 'lines':[i,j]})
        #cols with 2
        possible={i:sudoku.colpos[i][val].allowed() for i in range(9) if len(sudoku.colpos[i][val])==2}
        for i,j in itertools.combinations(possible.keys(),2):
            if possible[i]==possible[j]:
                reason=sudoku.colpos[i][val].notNones()+sudoku.colpos[j][val].notNones()
                for c in range(9):
                    for r in possible[i]:
                        if c!=i and c!=j:
                            made_deduction|=sudoku.ban(r,c,val+1,"xwing",reason,details={'rc':'cols', 'lines':[i,j]})
    return made_deduction

def swordfish(sudoku):
    '''RULE: if for 3 rows/cols a given number can only go in 2 or 3 places each, and these are in 3 cols/rows then ban given number from cols/rows'''
    made_deduction=False
    stripped_dict = lambda dic, banned: [info for key,info in dic.items() if (key not in banned) and info is not None] #for processing
    #rows
    for val in range(9):
        possible = {i: sudoku.rowpos[i][val].allowed() for i in range(9) if len(sudoku.rowpos[i][val]) in [2,3]}
        for i,j,k in itertools.combinations(possible.keys(),3):
            cols=list(set().union(possible[i],possible[j],possible[k]))
            if len(cols)==3:
                reason = stripped_dict(sudoku.rowpos[i][val],cols) + stripped_dict(sudoku.rowpos[j][val],cols) + stripped_dict(sudoku.rowpos[k][val],cols)
                for r in range(9):
                    for c in cols:
                        if r not in [i,j,k]:
                            made_deduction |= sudoku.ban(r, c, val + 1, "swordfish", reason,details={'rc':'rows', 'lines':[i,j,k]})
    #cols
    for val in range(9):
        possible = {i: sudoku.colpos[i][val].allowed() for i in range(9) if len(sudoku.colpos[i][val]) in [2,3]}
        for i,j,k in itertools.combinations(possible.keys(),3):
            rows=list(set().union(possible[i],possible[j],possible[k]))
            if len(rows)==3:
                reason = stripped_dict(sudoku.colpos[i][val],rows) + stripped_dict(sudoku.colpos[j][val],rows) + stripped_dict(sudoku.colpos[k][val],rows)
                for c in range(9):
                    for r in rows:
                        if c not in [i,j,k]:
                            made_deduction |= sudoku.ban(r, c, val + 1, "swordfish", reason,details={'rc':'cols', 'lines':[i,j,k]})
    return made_deduction