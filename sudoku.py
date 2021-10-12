# ==========================================
#       SUDOKU MANAGEMENT & SOLVING
# ==========================================
from boardio import *
from itertools import product
import numpy as np

board=[[0 for _ in range(9)] for _ in range(9)] # the board containing the filled in values and 0 in the empty cells
rows=[{i for i in range(1,10)} for j in range(9)] # values missing from the row
cols=[{i for i in range(1,10)} for j in range(9)] # values missing from the column
sections=[{i for i in range(1,10)} for j in range(9)] # values missing from the 3×3 sections

rowpos=[[set(range(9)) for i in range(9)] for j in range(9)] # j. sorban az i hova mehet meg
colpos=[[set(range(9)) for i in range(9)] for j in range(9)] # j. oszlopban az i hova mehet meg
squarepos=[[set([(i,j) for i in range(3) for j in range(3)]) for _ in range(9)] for _ in range(9)] # az adott sectionben az adott szám hova mehet

# >>> HELPERS
def cell_section(i,j):
    '''the 0-9 id of the 3×3 section containing this cell given in the 9×9 grid'''
    return ((i)//3)*3+j//3

def local_to_global(sec,i,j):
    '''global coordinates of local i,j in sector sec'''
    return (sec//3*3+i,sec%3*3+j)

def global_to_local(i,j):
    '''coordinates of a cell given in the 9×9 grid, inside its 3×3 section'''
    return (i%3,j%3)

# >>> MANAGE BOARD WITH SOLVING IN MIND
def assign_cell(row,col,val):
    '''Fill in the given cell with the given value.
    Take note of the new restricions this causes, and stop tracking this value & position further.'''
    board[row][col]=val
    # stop tracking this value
    rowpos[row][val-1]=set()
    colpos[col][val-1]=set()
    squarepos[cell_section(row,col)][val-1]=set()
    # no more values can be written this position...
    for i in range(9): # ...in this 3×3 section
        squarepos[cell_section(row,col)][i].discard(global_to_local(row,col))
    for i in range(9): # ...in this row and column
        rowpos[row][i].discard(col)
        colpos[col][i].discard(row)

    # this value can't be written anymore...
    #   ...in this row, column and section:
    rows[row].discard(val)
    cols[col].discard(val)
    sections[cell_section(row,col)].discard(val)
    #   ...in certain positions in other rows/columns:
    for i in range(9):
        rowpos[i][val-1].discard(col)
        colpos[i][val-1].discard(row)
    #   ...in certain positions in other sections:
    for i in range(9):
        squarepos[cell_section(i,col)][val-1].discard(global_to_local(i,col))
    for i in range(9):
        squarepos[cell_section(row,i)][val-1].discard(global_to_local(row,i))

def init_board(given):
    '''Initializes the board with some values given with their coordinates,
    given: list of tuples (row,col,val)'''
    global board
    board=[[0 for _ in range(9)] for _ in range(9)]
    global rows
    rows=[{i for i in range(1,10)} for j in range(9)]
    global cols
    cols=[{i for i in range(1,10)} for j in range(9)]
    global sections
    sections=[{i for i in range(1,10)} for j in range(9)]
    for row,col,val in given:
        assign_cell(row,col,val)

# >>> SOLVERS
def check_unicity(board_to_solve, verbose=False):
    '''Attempts to decide whether this sudoku has a unique solution with a DFS search.
    Returns (True, [unique_solution]), if the solution is unique,
            [solution_no1, solution_no2] if there are at least two solutions.'''
    b=np.array(board_to_solve)
    sols=[]
    
    def nextcell(row,col):
        '''Returns the coordinates of the next cell in reading order. ISN'T CYCLIC, doesn't work for the last cell.'''
        x=row*9+col+1
        return (x//9,x%9)

    def dfs(row,col):
        '''Attempts to fill this cell and then recursively all cells after this.
        Returns True if at least 2 solutions have been found during the search, and False before that.'''
        if row==9: # if we filled the entire grid, save this as a solution, and possibly terminate the search.
            sols.append(b.copy())
            if verbose: print(b)
            return len(sols)>1
        if b[row][col]!=0: # if cell is already filled, skip to the next one
            return dfs(*nextcell(row,col))
            
        # Decide which numbers can be written in this cell without causing a conflict with previously filled cells:
        possible=[True for i in range(9)]
        for i in range(9): # discard numbers present in this row
            if b[row][i]!=0:
                possible[b[row][i]-1]=False
        for i in range(9): # discard numbers present in this column
            if b[i][col]!=0:
                possible[b[i][col]-1]=False
        # discard numbers present in this section:
        sec=cell_section(row,col)
        for i,j in product(range(3), range(3)):
            tmp=b[local_to_global(sec, i, j)]
            if tmp!=0:
                possible[tmp-1]=False
        # fill this cell in all ways possible, and continue recursively to the next cell:       
        for i in range(9):
            if possible[i]:
                b[row][col]=i+1
                if dfs(*nextcell(row,col)):
                    return True
        b[row][col]=0
        return False
        
    dfs(0,0)
    if len(sols)==1:
        return (True,sols)
    else:
        return sols    

def solve(): # TODO: make this more interactive AND/OR make this terminate more nicely
    '''Attempts to solve this sudoku only using a fixed set of deductions. This set currently is:
    - only 1 value can be written to (i,j), as all others are present in this row+column+section
    - v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
    Press ENTER to try and use all of these deductions for all cells in some order. This means MANY (or even zero) deductions may
    happen, and a deduction may use information from  previous one made in this turn.
    The program will print a message if it finds the sudoku contradictory.
    Controls:
    '':         make deductions
    'q':        quit the solver
    'fuck':     print the numbers which can be written in each empty cell
    '80':       print the numbers which can be written in row 8 column 0'''
    while True:
        # RULE: only 1 value can be written to this cell, as all others are present in this row+column+section
        for i, j in product(range(9), range(9)):
            if board[i][j]!=0:
                continue
            tmp=rows[i]&cols[j]&sections[cell_section(i,j)] # which numbers are not present in this row+column+section?
            if len(tmp)==0: # if nothing is allowed in this empty cell: CONTRADICTION!
                print(f"cannot fill cell {i},{j}")
                return
            if len(tmp)==1: # if only a single value is allowed: FILL!
                ass=list(tmp)[0]
                assign_cell(i,j,ass)
        # RULE: v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
        for i, j in product(range(9), range(9)):
            if len(rowpos[i][j])==1:
                assign_cell(i,list(rowpos[i][j])[0],j+1)
            if len(colpos[i][j])==1:
                assign_cell(list(colpos[i][j])[0],i,j+1)
            if len(squarepos[i][j])==1:
                assign_cell(*local_to_global(i,*list(squarepos[i][j])[0]),j+1)
        k=input()
        print_board(board)
        if k=="": # Deduce once
            continue
        if k=="q": # Exit loop
            return
        if k=="fuck": # Print possible values for each empty cell
            for row, col in product(range(9), range(9)):
                if board[row][col]!=0:
                    continue
                print(f"{row},{col}: {rows[row]&cols[col]&sections[cell_section(row,col)]}")
        else: # For an input consisting of two digits 0-8, print the possible values for the cell determined by it 
            row=int(k[0])
            col=int(k[1])
            print(rows[row]&cols[col]&sections[cell_section(row,col)])

if __name__ == "__main__":
    # solve test
    print("--- Testing solve()")
    init_board(init_tuples_from_text('''
1....847.
5........
.4...1.3.
...2.....
...3.46..
..81.....
....6...5
...8.5.2.
.6.437...
'''[1:]))
    solve()

    # unicity test 1
    print("--- Testing check_unicity() #1")
    ret = check_unicity([
        [0,0,0,0,0,0,1,9,0],
        [2,3,0,0,0,0,6,0,0],
        [0,0,0,2,4,0,0,0,0],
        [0,0,0,0,0,0,9,6,0],
        [0,0,0,1,6,0,0,7,0],
        [0,4,8,0,7,0,0,0,0],
        [0,0,1,0,0,3,4,0,5],
        [0,0,9,0,0,8,0,0,0],
        [0,0,6,0,0,5,8,0,0]
    ])
    print(ret)

    # unicity test 2
    print("--- Testing check_unicity() #2")
    ret = check_unicity([[1, 0, 0, 0, 0, 8, 4, 7, 0, ],
        [5, 0, 0, 0, 0, 0, 0, 0, 0, ],
        [0, 4, 0, 0, 0, 1, 0, 3, 0, ],
        [0, 0, 0, 2, 0, 0, 0, 0, 0, ],
        [0, 0, 0, 3, 0, 4, 6, 0, 0, ],
        [0, 0, 8, 1, 0, 0, 0, 0, 0, ],
        [0, 0, 0, 0, 6, 0, 0, 0, 5, ],
        [0, 0, 0, 8, 0, 5, 0, 2, 0, ],
        [0, 6, 0, 4, 3, 7, 0, 0, 0]])
    print(ret)