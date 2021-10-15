# ==========================================
#       SUDOKU MANAGEMENT & SOLVING
# ==========================================
from boardio import *
from itertools import product
import numpy as np
import copy

class Sudoku:
    '''A class representing a 9×9 sudoku board. Capable of solving the sudoku. Contains large amounts of helper data.'''

    def __init__(self, board=None, tuples=None):
        '''Initialize a sudoku either with:
        board: list of lists
            A matrix representation of the sudoku table, with 0s in empty cells.
        tuples: Iterable of (row, column, value) tuples
            An Iterable containing an entry for each filled cell of the board.'''
        if tuples is not None:
            pass
        elif board is not None:
            tuples = init_tuples_from_array(board)
        else:
            raise ValueError("'board' or 'tuples' must be given in the contructor.")
        
        self.board=[[0 for _ in range(9)] for _ in range(9)] # the board containing the filled in values and 0 in the empty cells
        self.allowed=[[set(range(1,10)) for _ in range(9)] for _ in range(9)] # values which can be still written here

        self.rowpos=[[set(range(9)) for _ in range(9)] for _ in range(9)] # j. sorban az i hova mehet meg
        self.colpos=[[set(range(9)) for _ in range(9)] for _ in range(9)] # j. oszlopban az i hova mehet meg
        self.secpos=[[set([(i,j) for i in range(3) for j in range(3)]) for _ in range(9)] for _ in range(9)] # az adott sectionben az adott szám hova mehet
        
        self.missing = 9*9
        for row, col, val in tuples:
            self[row, col] = val
    
    def __setitem__(self, key, val):
        '''Fill in the given cell with the given value.
        Take note of the new restricions this causes, and stop tracking this value & position further.'''
        if val == 0:
            raise NotImplementedError("Cannot assign 0 to any cell!")
        self.missing -= 1
        row = key[0]
        col = key[1]
        self.board[row][col]=val
        # stop tracking this value
        self.rowpos[row][val-1] = set()
        self.colpos[col][val-1] = set()
        self.secpos[cell_section(row,col)][val-1] = set()
        # no more values can be written this position...
        self.allowed[row][col] = set()
        for i in range(9): # ...in this 3×3 section
            self.secpos[cell_section(row,col)][i].discard(global_to_local(row,col))
        for i in range(9): # ...in this row and column
            self.rowpos[row][i].discard(col)
            self.colpos[col][i].discard(row)

        # this value can't be written anymore...
        #   ...in this row, column and section:
        for i in range(9):
            self.allowed[i][col].discard(val)
            self.allowed[row][i].discard(val)
            p = local_to_global(cell_section(row, col),i//3,i%3)
            self.allowed[p[0]][p[1]].discard(val)
        #   ...in certain positions in other rows/columns:
        for i in range(9):
            self.rowpos[i][val-1].discard(col)
            self.colpos[i][val-1].discard(row)
        #   ...in certain positions in other secs:
        for i in range(9):
            self.secpos[cell_section(i,col)][val-1].discard(global_to_local(i,col))
        for i in range(9):
            self.secpos[cell_section(row,i)][val-1].discard(global_to_local(row,i))

    def __getitem__(self, key):
        return self.board[key[0]][key[1]]
    
    def solve(self): # TODO: make this more interactive AND/OR make this terminate more nicely
        '''Attempts to solve this sudoku only using a fixed set of deductions. This set currently is:
        - only 1 value can be written to (i,j), as all others are present in this row+column+section
        - v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them'''
        last_missing = self.missing+1
        while last_missing != self.missing:
            last_missing = self.missing
            # RULE: only 1 value can be written to this cell, as all others are present in this row+column+section
            for i, j in product(range(9), range(9)):
                if self.board[i][j]!=0:
                    continue
                tmp = self.allowed[i][j] # which numbers are not present in this row+column+section?
                if len(tmp)==0: # if nothing is allowed in this empty cell: CONTRADICTION!
                    print(f"cannot fill cell {i},{j}")
                    return
                if len(tmp)==1: # if only a single value is allowed: FILL!
                    ass = list(tmp)[0]
                    self[i,j] = ass
            # RULE: v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
            for i, j in product(range(9), range(9)):
                if len(self.rowpos[i][j])==1:
                    self[i, list(self.rowpos[i][j])[0]] = j+1
                if len(self.colpos[i][j])==1:
                    self[list(self.colpos[i][j])[0], i] = j+1
                if len(self.secpos[i][j])==1:
                    self[local_to_global(i,*list(self.secpos[i][j])[0])] = j+1
        return self.missing == 0

    def interactive_solve(self):
        '''Interactive solver tool. Type 'h' or 'help' for help.'''
        print_board(self.board)
        while True:
            # INTERACTIVE PART
            k = input()
            if k == "": # Attempt solve
                if self.solve():
                    print("          =========================   SUDOKU COMPLETE   =========================          ")
                    print_board(self.board)
                    return
                else:
                    self.print_status()
            elif k == "print" or k == "p": # Print
                self.print_status()
            elif k == "quit" or k == "q" or k == "exit": # Exit loop
                return
            elif k.startswith("set "):
                m = re.match(r'set\s+(\d)[^\d]*(\d)[^\d]*(\d)\s*', k)
                if m is None:
                    print("ERROR: could not parse input. Please use 'set {row} {col} {value}'")
                    continue
                r = int(m.group(1))
                c = int(m.group(2))
                v = int(m.group(3))
                if self.board[r][c] != 0:
                    print(f"ERROR: ({r}, {c}) is already filled with {self.board[r][c]}")
                    continue
                if v not in self.allowed[r][c]:
                    print(f"ERROR: {v} is not allowed at ({r}, {c}); allowed numbers: {self.allowed[r][c]}")
                    continue  
                self[r,c] = v
                print(f"({r}, {c}) has been set to {v}.")
            elif k.startswith("ban "):
                k = re.sub(r'[^\d:]+','',k)
                halves = k.split(':')
                if len(halves) != 2 or len(halves[0])%2!=0:
                    print("ERROR: could not parse input. Please use 'ban {cell1_row} {cell1_col} {cell2_row} {cell2_col}[...]: {value1} {value2}[...]'")
                    continue
                cells = [(int(halves[0][2*i]),int(halves[0][2*i+1])) for i in range(len(halves[0])//2)]
                to_ban = {int(d) for d in halves[1]}
                for r, c in cells:
                    self.allowed[r][c] -= to_ban
                print(f"{to_ban} banned from the following cells: {cells}")
            elif k == "h" or k == "help":
                print("Commands:")
                print("   print:")
                print("      Print current state of the sudoku.")
                print("   quit, q, exit:")
                print("      Exit the solver.")
                print("   set {row} {column} {value}:")
                print("      Set the value of the specified cell. Indexing of rows/cols starts from 0.")
                print("   ban [{cell_i_row} {cell_i_col} pairs]: [{value} banned values]")
                print("      Ban these values from these cells. Row/col indexing starts from 0.")
                print("   help or h:")
                print("      Print this help.")
                print("   []:")
                print("      The empty command attempts a solve from the current state.")
                
    # >>> UTILITY
    def is_unique(self):
        '''Checks whether this sudoku has a unique solution. See check_unicity().'''
        return check_unicity(self.board, False)
    
    def print_status(self):
        '''Prints a detailed representation of the current state of the puzzle. Each cell contains which numbers can be written there.'''
        print_detailed_board(self.board, [[self.allowed[r][c] for c in range(9)] for r in range(9)])

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

if __name__ == "__main__":
    sud = Sudoku(board=[[0, 0, 8, 0, 0, 0, 6, 0, 3], 
        [0, 2, 0, 0, 0, 9, 0, 0, 0], 
        [0, 0, 0, 8, 0, 0, 4, 5, 0], 
        [8, 5, 6, 0, 7, 0, 0, 0, 0], 
        [0, 0, 4, 0, 0, 0, 5, 0, 0], 
        [0, 0, 0, 0, 6, 0, 8, 9, 7], 
        [0, 8, 7, 0, 0, 6, 0, 0, 0], 
        [0, 0, 0, 3, 0, 0, 0, 8, 0], 
        [2, 0, 3, 0, 0, 0, 1, 0, 0]])
    sud.interactive_solve()
    # solve test
    print("--- Testing solve()")
    sud = Sudoku(tuples=init_tuples_from_text('''
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
    sud.solve()

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