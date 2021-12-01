from itertools import combinations, permutations, product
from tracker import MustBe
from util import cell_section, global_to_local, local_to_global


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
            made_deduction |= sudoku.make_deduction(MustBe((i,sudoku.secpos[i][j].last_one()),j+1,'secpos'),
                'secpos',sudoku.secpos[i][j].notNones())
    return made_deduction

def _apply_for_nines(func):
    made_deduction = False
    for row in range(9):
        cells_to_check = [(row,col) for col in range(9)]
        made_deduction |= func(cells_to_check, {"type": "row", "idx": row})

    for col in range(9):
        cells_to_check = [(row,col) for row in range(9)]
        made_deduction |= func(cells_to_check, {"type": "col", "idx": row})

    for sec in range(9):
        cells_to_check = [local_to_global(sec,i,j) for i,j in product(range(3),range(3))]
        made_deduction |= func(cells_to_check, {"type": "square", "idx": row})
    return made_deduction

def _ban_numbers(sudoku, cell,numbers,rule, cells_used,details=None):
    made_deduction = False
    for number in numbers:
        made_deduction |= sudoku.ban(cell[0],cell[1],number,rule,cells_used,details)
    return made_deduction

def _allowed_numbers(sudoku, cells):
    """Returns a list of tuples, where i-th element in the list contains the allowed numbers in cells[i]"""
    allowed_numbers = []
    for cell in cells:
        if sudoku.board[cell[0]][cell[1]] != 0:
            allowed_numbers.append((sudoku.board[cell[0]][cell[1]],))
        else:
            allowed_numbers.append(tuple(sudoku.allowed[cell[0]][cell[1]].allowed()))
    return allowed_numbers


def naked_pair(sudoku):
    """RULE: if only the same two numbers can be written in two cells in a row/col/sec, then remove them from the other cells of the row/col/sec."""
    
    def search_for_naked_pairs(elems):
        """Returns a list of 2-tuples, where every tuple contains the indeces of the same input"""
        return [(i,j) for i in range(len(elems)) for j in range(i+1,len(elems)) if len(elems[i])==2 and elems[i]==elems[j]]
    
    def search_and_ban_in_subset(cells_to_check, section):
        """Searches all nake-pairs in a subset of cells and bans these numbers from the other elements of subset."""
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        naked_pairs = search_for_naked_pairs(allowed_numbers)
        for pair in naked_pairs:
            cell1 = cells_to_check[pair[0]]
            cell2 = cells_to_check[pair[1]]
            deleted_numbers = sudoku.allowed[cell1[0]][cell1[1]].allowed()
            cells_used = sudoku.allowed[cell1[0]][cell1[1]].notNones()+sudoku.allowed[cell2[0]][cell2[1]].notNones()
            for cell in cells_to_check:
                if cell not in (cells_to_check[pair[0]],cells_to_check[pair[1]]):
                    made_deduction |= _ban_numbers(sudoku,cell,deleted_numbers,"naked_pair",cells_used, {'cell1':cell1, 'cell2':cell2, 'nums': deleted_numbers, 'section': section})
        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)

def hidden_pair(sudoku):
    """RULE: If two number lying in two cells in the same row/col/sec, then ban the remaining numbers from these cells."""
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

    def search_and_ban_in_subset(cells_to_check, section):
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        pairs = search_hidden_pairs(allowed_numbers)
        for pair,except_nums in pairs.items():
            cell0 = cells_to_check[pair[0]]
            cell1 = cells_to_check[pair[1]]
            used_nums = set(range(1,10))-set(except_nums)
            cells_used = []
            for cell in cells_to_check:
                if cell not in (cell0, cell1):
                    cells_used += [sudoku.allowed[cell[0]][cell[1]][n] for n in used_nums if n in _allowed_numbers(sudoku,[cell])]
            made_deduction |= _ban_numbers(sudoku, cell0, filter(lambda x: x not in except_nums, allowed_numbers[pair[0]]), "hidden_pair",cells_used, {'cell1': cell0, 'cell2': cell1,'nums':except_nums,'section': section})
            made_deduction |= _ban_numbers(sudoku, cell1, filter(lambda x: x not in except_nums, allowed_numbers[pair[1]]), "hidden_pair",cells_used, {'cell1': cell0, 'cell2': cell1,'nums':except_nums,'section': section})

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
                        made_deduction|=sudoku.ban(r,c,val+1,"col_square",reason)
    return made_deduction

def naked_trios(sudoku):
    """RULE: Any group of three cells in the same unit that contain IN TOTAL three candidates is a Naked Triple.
    Each cell can have two or three numbers, as long as in combination all three cells have only three numbers.
    When this happens, the three candidates can be removed from all other cells in the same unit.
    """

    def search_for_naked_trios(elems):
        """Returns a list of 3-tuples, where every 3-tuple contains the indeces of `elems` which form a Naked Triple.
        The combinations of candidates for a Naked Triple will be one of the following:
        (123) (123) (123) - {3/3/3} (in terms of candidates per cell)
        (123) (123) (12) - {3/3/2} (or some combination thereof)
        (123) (12) (23) - {3/2/2}
        (12) (23) (13) - {2/2/2}
        """
        l = []
        for comb in combinations(range(9),3):
            cell0 = set(elems[comb[0]])
            cell1 = set(elems[comb[1]])
            cell2 = set(elems[comb[2]])
            for cell0, cell1, cell2 in permutations((cell0, cell1, cell2)):
                if len(cell0) == 3 and cell0 == cell1 and cell1 == cell2:
                    l.append(tuple(sorted((comb[0],comb[1],comb[2]))))
                    break
                elif len(cell0) == 3 and cell0 == cell1 and len(cell2) == 2 and cell2.issubset(cell1):
                    l.append(tuple(sorted((comb[0],comb[1],comb[2]))))
                    break
                elif len(cell0) == 3 and len(cell1) == 2 and len(cell2) == 2 and \
                    cell1.issubset(cell0) and cell2.issubset(cell0) and len(cell1&cell2) == 1:
                    l.append(tuple(sorted((comb[0],comb[1],comb[2]))))
                    break
                elif len(cell0) == 2 and len(cell1) == 2 and len(cell1) == 2 and \
                    len(cell0&cell1) == 2 and len(cell1&cell2) == 2 and \
                    len(cell0&cell2) == 2 and len(cell0&cell1&cell2) == 1:
                    l.append(tuple(sorted((comb[0],comb[1],comb[2]))))
                    break
        return l
    
    def search_and_ban_in_subset(cells_to_check, section):
        """Searches all naked-trios in a subset of cells and bans these numbers from the other elements of subset."""
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        naked_trios = search_for_naked_trios(allowed_numbers)
        for trio in naked_trios:
            cell0 = cells_to_check[trio[0]]
            cell1 = cells_to_check[trio[1]]
            cell2 = cells_to_check[trio[2]]
            deleted_numbers = set(sudoku.allowed[cell0[0]][cell0[1]].allowed() + sudoku.allowed[cell1[0]][cell1[1]].allowed() + sudoku.allowed[cell2[0]][cell2[1]].allowed())
            cells_used = sudoku.allowed[cell0[0]][cell0[1]].notNones()+sudoku.allowed[cell1[0]][cell1[1]].notNones()+sudoku.allowed[cell2[0]][cell2[1]].notNones()
            for cell in cells_to_check:
                if cell not in (cell0, cell1, cell2):
                    made_deduction |= _ban_numbers(sudoku,cell,deleted_numbers,"naked-trios",cells_used, {'cell1':cell1, 'cell2':cell2, 'nums': deleted_numbers, 'section': section})
        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)

def hidden_trios(sudoku):
    """RULE: If three number lying in three cells in the same row/col/sec, then ban the remaining numbers from these cells."""
    def search_hidden_trios(elems):
        res = dict()
        where_can_go = {i:set() for i in range(1,10)} # i-th number in which indices of elems can go
        for idx,elem in enumerate(elems):
            for num in elem:
                where_can_go[num].add(idx)
        
        for nums in combinations(range(1,10),3):
            nums_can_go = tuple(where_can_go[nums[0]] | where_can_go[nums[1]] | where_can_go[nums[2]])
            if len(where_can_go[nums[0]]) > 1 and len(where_can_go[nums[1]]) > 1 and len(where_can_go[nums[2]]) > 1 and\
                len(nums_can_go)==3:
                res[nums_can_go] = nums
        return res

    def search_and_ban_in_subset(cells_to_check, section):
        made_deduction = False
        allowed_numbers = _allowed_numbers(sudoku,cells_to_check)
        trios = search_hidden_trios(allowed_numbers)
        for trio,except_nums in trios.items():
            cell0 = cells_to_check[trio[0]]
            cell1 = cells_to_check[trio[1]]
            cell2 = cells_to_check[trio[2]]
            used_nums = set(range(1,10))-set(except_nums)
            cells_used = []
            for cell in cells_to_check:
                if cell not in (cell0, cell1, cell2):
                    cells_used += [sudoku.allowed[cell[0]][cell[1]][n] for n in used_nums if n in _allowed_numbers(sudoku,[cell])]
            made_deduction |= _ban_numbers(sudoku, cell0, filter(lambda x: x not in except_nums, allowed_numbers[trio[0]]), "hidden-trio",cells_used)
            made_deduction |= _ban_numbers(sudoku, cell1, filter(lambda x: x not in except_nums, allowed_numbers[trio[1]]), "hidden-trio",cells_used)
            made_deduction |= _ban_numbers(sudoku, cell2, filter(lambda x: x not in except_nums, allowed_numbers[trio[2]]), "hidden-trio",cells_used)
        return made_deduction

    return _apply_for_nines(search_and_ban_in_subset)


def ywing(sudoku):
    '''RULE: If three of the corners of a rectangular have two candidates AC, AB and BC, respectively, then C can be removed from the fourth corner.
    Note that we don't actually need a rectangular, it is also enought to have a circle.
    E.g. (C+ means that there can be other numbers as C)
     ============================
     || C+  AB  C || -  AC  -  ||
     || -   -   - || -  -   -  ||
     || BC  -   - || C+ C+  C+ ||
     ============================'''
    # (i,j)=AC and (k,l)=BC
    def allowed_nums_multicells(*args):
        """Input: cells. Output: numbers that can be written in all cell."""
        return set.intersection(*[set(_allowed_numbers(sudoku,[arg])[0]) for arg in args])
    
    def cells_in_same_sec(cell, col={0,1,2}, row={0,1,2}):
        """Returns a list with the cells that are not set and are in the same sec as the input.
        You can also set the (local)col or (local)row."""
        sec = cell_section(cell[0],cell[1])
        res = []
        for i,j in product(range(3),range(3)):
            if i in row and j in col:
                new_cell = local_to_global(sec, i, j)
                if len(allowed_nums_multicells(new_cell)) > 0:
                    res.append(new_cell)
        return res

    made_deduction = False
    for cell1 in product(range(9),range(9)):
        for cell2 in product(range(9),range(9)):
            if len(allowed_nums_multicells(cell1)) == 2 and len(allowed_nums_multicells(cell2)) == 2 and \
               len(allowed_nums_multicells(cell1,cell2)) == 1 and \
               not (cell1[0] == cell2[0] and cell1[1] == cell2[1]):
                if len(set((cell1[0],cell2[0]))) == 2 and len(set((cell1[1],cell2[1]))) == 2:
                    # It is a rectangle
                    cell0 = (cell1[0], cell2[1])
                    cell3 = (cell2[0], cell1[1])
                    if len(allowed_nums_multicells(cell0)) == 2 and \
                       len(allowed_nums_multicells(cell0,cell1)) == 1 and \
                       len(allowed_nums_multicells(cell0,cell2)) == 1 and \
                       len(allowed_nums_multicells(cell0,cell1,cell2)) == 0:
                        # Good rectangle.
                        deleted_number = set.intersection(allowed_nums_multicells(cell1,cell2)).pop()
                        cells_used = sudoku.allowed[cell0[0]][cell0[1]].notNones()+sudoku.allowed[cell1[0]][cell1[1]].notNones()+sudoku.allowed[cell2[0]][cell2[1]].notNones()
                        details = {'main':cell0,'main_allowed':allowed_nums_multicells(cell3),'second1':cell1,'second1_allowed':allowed_nums_multicells(cell1),'second2':cell2,'second2_allowed':allowed_nums_multicells(cell2)}
                        made_deduction |= sudoku.ban(cell3[0],cell3[1],deleted_number,"ywing",cells_used, details)
                    if len(allowed_nums_multicells(cell3)) == 2 and \
                       len(allowed_nums_multicells(cell3,cell1)) == 1 and \
                       len(allowed_nums_multicells(cell3,cell2)) == 1 and \
                       len(allowed_nums_multicells(cell3,cell1,cell2)) == 0:
                        # Good rectangle.
                        deleted_number = set.intersection(allowed_nums_multicells(cell1,cell2)).pop()
                        cells_used = sudoku.allowed[cell3[0]][cell3[1]].notNones()+sudoku.allowed[cell1[0]][cell1[1]].notNones()+sudoku.allowed[cell2[0]][cell2[1]].notNones()
                        details = {'main':cell3,'main_allowed':allowed_nums_multicells(cell3),'second1':cell1,'second1_allowed':allowed_nums_multicells(cell1),'second2':cell2,'second2_allowed':allowed_nums_multicells(cell2)}
                        made_deduction |= sudoku.ban(cell0[0],cell0[1],deleted_number,"ywing",cells_used, details)
                elif cell1[0] == cell2[0] and cell_section(cell1[0],cell1[1]) != cell_section(cell2[0],cell2[1]):
                    # One row, but not in the same sec
                    main_cell = cell1
                    second_cell = cell2
                    other_cells = cells_in_same_sec(main_cell, row = {0,1,2}-{global_to_local(second_cell[0],second_cell[1])[0]})
                    for cell3 in other_cells:
                        if len(allowed_nums_multicells(cell3)) == 2 and  \
                            len(allowed_nums_multicells(main_cell,cell3)) == 1 and len(allowed_nums_multicells(second_cell,cell3)) == 1 and \
                            len(allowed_nums_multicells(main_cell,second_cell, cell3)) == 0:
                            deleted_number = allowed_nums_multicells(second_cell,cell3).pop()
                            cells_used = sudoku.allowed[main_cell[0]][main_cell[1]].notNones() + sudoku.allowed[second_cell[0]][second_cell[1]].notNones() + sudoku.allowed[cell3[0]][cell3[1]].notNones()
                            for cell4 in cells_in_same_sec(second_cell,row={global_to_local(cell3[0],cell3[1])[0]}):
                                if deleted_number in allowed_nums_multicells(cell4):
                                    details = {'main':main_cell,'main_allowed':allowed_nums_multicells(main_cell),'second1':second_cell,'second1_allowed':allowed_nums_multicells(second_cell),'second2':cell3,'second2_allowed':allowed_nums_multicells(cell3)}
                                    made_deduction != sudoku.ban(cell4[0],cell4[1],deleted_number,"ywing",cells_used, details)

                elif cell1[1] == cell2[1] and cell_section(cell1[0],cell1[1]) != cell_section(cell2[0],cell2[1]):
                    # One col, but not in the same sec
                    main_cell = cell1
                    second_cell = cell2
                    other_cells = cells_in_same_sec(main_cell, col = {0,1,2}-{global_to_local(second_cell[0],second_cell[1])[1]})
                    for cell3 in other_cells:
                        if len(allowed_nums_multicells(cell3)) == 2 and  \
                            len(allowed_nums_multicells(main_cell,cell3)) == 1 and len(allowed_nums_multicells(second_cell,cell3)) == 1 and \
                            len(allowed_nums_multicells(main_cell,second_cell, cell3)) == 0:
                            deleted_number = allowed_nums_multicells(second_cell,cell3).pop()
                            cells_used = sudoku.allowed[main_cell[0]][main_cell[1]].notNones() + sudoku.allowed[second_cell[0]][second_cell[1]].notNones() + sudoku.allowed[cell3[0]][cell3[1]].notNones()
                            for cell4 in cells_in_same_sec(second_cell,col={global_to_local(cell3[0],cell3[1])[1]}):
                                if deleted_number in allowed_nums_multicells(cell4):
                                    details = {'main':main_cell,'main_allowed':allowed_nums_multicells(main_cell),'second1':second_cell,'second1_allowed':allowed_nums_multicells(second_cell),'second2':cell3,'second2_allowed':allowed_nums_multicells(cell3)}
                                    made_deduction != sudoku.ban(cell4[0],cell4[1],deleted_number,"ywing",cells_used, details)
    return made_deduction

def xwing(sudoku):
    '''RULE: if for two rows/cols a given number can only go in 2 places each and these 4 places form a rectangle then ban given number from corresponding cols/rows'''
    made_deduction=False
    for val in range(9):
        #rows with 2
        possible={i:sudoku.rowpos[i][val].allowed() for i in range(9) if len(sudoku.rowpos[i][val])==2}
        for i,j in combinations(possible.keys(),2):
            if possible[i]==possible[j]:
                reason = sudoku.rowpos[i][val].notNones() + sudoku.rowpos[j][val].notNones()
                for r in range(9):
                    for c in possible[i]:
                        if r!=i and r!=j:
                            made_deduction|=sudoku.ban(r,c,val+1,"xwing",reason,details={'rc':'rows', 'lines':[i,j]})
        #cols with 2
        possible={i:sudoku.colpos[i][val].allowed() for i in range(9) if len(sudoku.colpos[i][val])==2}
        for i,j in combinations(possible.keys(),2):
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
        for i,j,k in combinations(possible.keys(),3):
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
        for i,j,k in combinations(possible.keys(),3):
            rows=list(set().union(possible[i],possible[j],possible[k]))
            if len(rows)==3:
                reason = stripped_dict(sudoku.colpos[i][val],rows) + stripped_dict(sudoku.colpos[j][val],rows) + stripped_dict(sudoku.colpos[k][val],rows)
                for c in range(9):
                    for r in rows:
                        if c not in [i,j,k]:
                            made_deduction |= sudoku.ban(r, c, val + 1, "swordfish", reason,details={'rc':'cols', 'lines':[i,j,k]})
    return made_deduction