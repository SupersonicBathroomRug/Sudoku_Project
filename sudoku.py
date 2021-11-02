# ==========================================
#       SUDOKU MANAGEMENT & SOLVING
# ==========================================
from consoleapp import ConsoleApp
from boardio import *
from tracker import *
from itertools import product
import numpy as np
import copy
from sys import argv
from getopt import getopt
import time

sudoku_app = ConsoleApp(description='INTERACTIVE SUDOKU SOLVER')
sudoku_app.add_variable(r'k[-_]opt(?:imi[zs]ation)?',ConsoleApp.Patterns.BOOLONOFF,'Should we minimize k in the solving process?')
sudoku_app.add_function(r'print',[(r'file',ConsoleApp.Patterns.TEXT,"")],r'-?-?r(?:aw)?',r'-?-?a(?:rray)?',r'-?-?s(?:mall)?',description=
    '''Prints the board to the console (to a file, if a file is specified in a string). Flags:
--raw:   print only the numbers which are filled in, with 0 for empty cells, no superfluous characters
--array: print the Sudoku.board array in a python array-style
--small: the sudoku will be pretty printed, but only the filled in values are shown''')
sudoku_app.add_function(r'proof',[(r'slice',r'\d*\s*:\s*\d*',':'),(r'file',ConsoleApp.Patterns.TEXT,"")],
    r'-?-?r(?:ef(?:erence)?)?',r'-?-?[Ii](?:s[Vv]alue)?',description=
    '''Prints the proof constructed so far to the console (or the given file, e.g. "proof.txt"). A 'slice' is a start:end slice notation,
where either or both arguments may be omitted: if this is given, only these proof steps will be printed.''')
sudoku_app.add_function(r'set',[(r'row',r'\d'),(r'col(?:umn)?',r'\d:?'),(r'val(?:ue)?',r'\d')],description=
    '''Set the cell given by 'row' and 'column' to value 'value', if possible.''')
sudoku_app.add_function(r'ban',[(r'cells',r'(?:\d[,;\s]*\d[,;\s]*)+:'),(r'values',r'(?:[,;\s]*\d)*')],description=
    '''Ban from the cells given in 'cells' in the format 'cell1_row,cell1_col cell2_row,cell2_col ...:' the values given in 'values'.
Note that there must be a separating ':' between 'cells' and 'values'.''')
sudoku_app.add_function(r'u(?:nique)?|check_unicity',[],description=
    '''Check whether this sudoku has a unique solution. Prints the solution if it is so, or two solutions, if it is not.''')
sudoku_app.add_function(r'stat(?:istic)?s?',[(r'file',ConsoleApp.Patterns.TEXT,"")],description=
    '''Prints some detailed statistics about the solving process so far, such as total runtime.''')
sudoku_app.add_function(r'',[],description=
    '''Attempts to solve the sudoku from this state.''')

class Sudoku:
    '''A class representing a 9×9 sudoku board. Capable of solving the sudoku. Contains large amounts of helper data.'''

    # >>> DATA MANIPULATION
    def __init__(self, board=None, tuples=None, k_opt=True):
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
        # cell-based variables:
        self.board=[[0 for _ in range(9)] for _ in range(9)] # the board containing the filled in values and 0 in the empty cells
        self.allowed=[[diclen(range(1,10)) for _ in range(9)] for _ in range(9)] # values which can be still written here
        # position-based variables:
        self.rowpos=[[diclen() for _ in range(9)] for _ in range(9)] # j. sorban az i hova mehet meg
        self.colpos=[[diclen() for _ in range(9)] for _ in range(9)] # j. oszlopban az i hova mehet meg
        self.secpos=[[diclen(((i,j) for i in range(3) for j in range(3))) for _ in range(9)] for _ in range(9)] # az adott sectionben az adott szám hova mehet
        # proof storage
        self.missing = 9*9
        self.proof = []
        self.filler_deductions = set()
        # stats:
        self.k_opt = k_opt
        self.deduction_time = 0
        self.k_opt_time = 0
        self.fill_time = 0
        self.failed_solves = 0
        self.deus_ex_sets = 0
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
        im_filled = IsValue((row, col), val)
        # stop tracking this value
        for i in range(9):
            self.rowpos[row][val-1][i] = im_filled
            self.colpos[col][val-1][i] = im_filled
            self.secpos[cell_section(row,col)][val-1][(i//3,i%3)] = im_filled
        # no more values can be written this position...
        # TODO: this is useless, as these values won't be accessed again
        #for i in range(9):
        #    self.allowed[row][col][i] = im_filled
        for i in range(9): # ...in this 3×3 section
            self.secpos[cell_section(row,col)][i][global_to_local(row, col)] = im_filled
        for i in range(9): # ...in this row and column
            self.rowpos[row][i][col] = im_filled
            self.colpos[col][i][row] = im_filled

        # this value can't be written anymore...
        #   ...in this row, column and section:
        for i in range(9):
            self.allowed[i][col][val] = im_filled
            self.allowed[row][i][val] = im_filled
            p = local_to_global(cell_section(row, col),i//3,i%3)
            self.allowed[p[0]][p[1]][val] = im_filled
        #   ...in certain positions in other rows/columns:
        for i in range(9):
            self.rowpos[i][val-1][col] = im_filled
            self.colpos[i][val-1][row] = im_filled
        #   ...in certain positions in other secs:
        for i in range(9):
            self.secpos[cell_section(i,col)][val-1][global_to_local(i,col)] = im_filled
        for i in range(9):
            self.secpos[cell_section(row,i)][val-1][global_to_local(row,i)] = im_filled

    def __getitem__(self, key):
        return self.board[key[0]][key[1]]
    
    # >>> STORING DEDUCTIONS
    def make_deduction(self, knowledge, rule, reasons=None):
        '''Store a deduction which yields 'knowledge' applying 'rule' to Knowlegde instances 'reasons'.
        Return True if this is a new deduction.'''
        p = knowledge.get_pos()
        if self.board[p[0]][p[1]] != 0:
            return False
        cons = Consequence(reasons, rule)
        if isinstance(knowledge, MustBe):
            for ded in self.filler_deductions: # if this deduction was already made, save this as an alternative proof
                if ded.result == knowledge:
                    return ded.add_reason(cons)
            # if this deduction has not been made yet, create and save it!
            self.filler_deductions.add(Deduction([cons], knowledge))
            return True
        elif isinstance(knowledge, CantBe):
            # find this Knowledge if it exists:
            old = self._get_knowledge(knowledge)
            if isinstance(old, Deduction): # this deduction already exists
                return old.add_reason(cons)
            else:
                self._store_new_deduction(Deduction([cons], knowledge))
                return True
    
    def _get_knowledge(self, k):
        '''Given a Knowledge instance 'k', returns the data stored at its position, corresponding to its value.
        This means it either returns a Deduction instance (if this knowledge has been already acquired), and None otherwise.'''
        if k.coordtype == "cell":
            return self.allowed[k.position[0]][k.position[1]][k.value]
        elif k.coordtype == "rowpos":
            return self.rowpos[k.position[0]][k.value-1][k.position[1]]
        elif k.coordtype == "cellpos":
            return self.colpos[k.position[0]][k.value-1][k.position[1]]
        elif k.coordtype == "secpos":
            return self.secpos[k.position[0]][k.value-1][k.position[1]]
    
    def _store_new_deduction(self, deduction):
        '''Stores a given deduction in the correct place.'''
        k = deduction.result
        if k.coordtype == "cell":
            self.allowed[k.position[0]][k.position[1]][k.value] = deduction
        elif k.coordtype == "rowpos":
            self.rowpos[k.position[0]][k.value-1][k.position[1]] = deduction
        elif k.coordtype == "cellpos":
            self.colpos[k.position[0]][k.value-1][k.position[1]] = deduction
        elif k.coordtype == "secpos":
            self.secpos[k.position[0]][k.value-1][k.position[1]] = deduction
    
    # >>> SOLVERS
    def solve(self): # TODO: make this more interactive AND/OR make this terminate more nicely
        '''Attempts to solve this sudoku only using a fixed set of deductions. This set currently is:
        - only 1 value can be written to (i,j), as all others are present in this row+column+section
        - v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them'''
        timestamp = time.time()
        while self.missing > 0:
            made_deduction = True
            # MAKE DEDUCTIONS WHILE POSSIBLE
            while made_deduction:
                made_deduction = False
                # RULE: only 1 value can be written to this cell, as all others are present in this row+column+section
                for i, j in product(range(9), range(9)):
                    if self.board[i][j]!=0: # left here to enable contradiction check
                        continue
                    tmp = self.allowed[i][j] # which numbers are not present in this row+column+section?
                    if len(tmp)==0: # if nothing is allowed in this empty cell: CONTRADICTION!
                        print(f"cannot fill cell {i},{j}")
                        return
                    if len(tmp)==1: # if only a single value is allowed: FILL!
                        ass =tmp.last_one()
                        made_deduction |= self.make_deduction(MustBe((i,j),ass),
                            'allowed',tmp.notNones())
                # RULE: v can be written only to this cell in this row/column/section, as all other cells are filled/v cannot be written in them
                # ignoring already filled cells is done be make_deduction
                for i, j in product(range(9), range(9)):
                    if len(self.rowpos[i][j]) == 1:
                        made_deduction |= self.make_deduction(MustBe((i,self.rowpos[i][j].last_one()),j+1,'rowpos'),
                            'rowpos',self.rowpos[i][j].notNones())
                    if len(self.colpos[i][j])==1:
                        made_deduction |= self.make_deduction(MustBe((i,self.colpos[i][j].last_one()),j+1,'colpos'),
                            'colpos',self.colpos[i][j].notNones())
                    if len(self.secpos[i][j])==1:
                        p = local_to_global(i,*self.secpos[i][j].last_one())
                        made_deduction |= self.make_deduction(MustBe((i,self.secpos[i][j].last_one()),j+1,'secpos'),
                            'secpos',self.secpos[i][j].notNones())
            self.deduction_time += time.time() - timestamp
            timestamp = time.time()
            # EXIT IF NECESSARY
            if len(self.filler_deductions) == 0:
                self.failed_solves += 1
                return False
            # DECIDE HOW TO PROVE THIS STEP
            proofstep = ProofStep(self.filler_deductions, self.k_opt)
            self.proof.append(proofstep)
            self.k_opt_time += time.time() - timestamp
            timestamp = time.time()
            # FILL THE SELECTED CELL
            self[proofstep.position] = proofstep.value
            self.fill_time += time.time() - timestamp
            timestamp = time.time()  
        return True

    def interactive_solve(self):
        '''Interactive solver tool. Type 'h' or 'help' for help.'''
        print("   INTERACTIVE SOLVER STARTED  ")
        print_board(self.board)
        for action, rname, data in sudoku_app:
            if action == 'func' and rname == "": # Attempt solve
                if self.solve():
                    print("          =========================   SUDOKU COMPLETE   =========================          ")
                    print_board(self.board)
                else:
                    print("Solver got stuck at this state:")
                    self.print_status()
            elif action == 'func' and rname == r'print': # Print
                # TODO: --raw, --small, --array, file
                self.print_status()
            elif action == 'func' and rname == r'set':
                r = int(data['params']['row'])
                c = int(re.sub('[^\d]','',data['params']['col(?:umn)?']))
                v = int(data['params']['val(?:ue)?'])
                if self.board[r][c] != 0:
                    print(f"ERROR: ({r}, {c}) is already filled with {self.board[r][c]}")
                    continue
                if self.allowed[r][c][v] is not None:
                    print(f"ERROR: {v} is not allowed at ({r}, {c}); allowed numbers: {self.allowed[r][c].allowed()}")
                    continue  
                self[r,c] = v
                self.deus_ex_sets += 1
                print(f"({r}, {c}) has been set to {v}.")
            elif action == 'func' and rname == r'ban':
                pure_cell_str = re.sub('[^\d]','',data['params']['cells'])
                cells = [(int(pure_cell_str[2*i]),int(pure_cell_str[2*i+1])) for i in range(len(pure_cell_str)//2)]
                to_ban = {int(d) for d in re.sub(r'[^\d]','',data['params']['values'])}
                for r, c in cells:
                    for val in to_ban:
                        self.ban(r,c,val,'deus_ex',[])
                print(f"{to_ban} banned from the following cells: {cells}")
            elif action == 'func' and rname == r'u(?:nique)?|check_unicity':
                print("Checking unicity of the puzzle. Please wait.")
                u, sols = self.is_unique()
                if u:
                    print("[UNIQUE] This puzzle has a unique solution. It is the following:")
                    print_board(sols[0])
                else:
                    print("[NOT UNIQUE] This puzzle has multiple solutions. Two of these are:")
                    print_board(sols[0])
                    print_board(sols[1])
            elif action == 'func' and rname == 'proof':
                if data['params']['file'] == '': 
                    data['params']['file'] = None
                else:
                    print(f"Printing output to {data['params']['file']}.")
                # Simplify k:
                data['params']['slice'] = re.sub(r'[^\d:]','',data['params']['slice'])
                # Process k into proper slice indicies:
                halves = data['params']['slice'].split(':')
                start = int(halves[0]) if halves[0] != '' else 0
                end = int(halves[1]) if halves[1] != '' else len(self.proof)
                if end > len(self.proof):
                    print(f"WARNING: specified range too large; proof only has {len(self.proof)} steps so far.")
                # Execute printing:
                self.print_proof(data['params']['file'], start, min(end, len(self.proof)),
                    isvalue=data['flags'][r'-?-?[Ii](?:s[Vv]alue)?'], 
                    reference=data['flags'][r'-?-?r(?:ef(?:erence)?)?'])
            elif action == 'get_var' and rname == r'k[-_]opt(?:imi[zs]ation)?':
                print(f"k-optimization: {'ON' if self.k_opt else 'OFF'}")
            elif action == 'set_var' and rname == r'k[-_]opt(?:imi[zs]ation)?':
                self.k_opt = ConsoleApp.str_to_bool(data)
            elif action == 'func' and rname == r'stat(?:istic)?s?':
                print(f"RUNTIME:                   {self.deduction_time+self.k_opt_time+self.fill_time} s")
                print(f"| Deduction time:          {self.deduction_time} s")
                print(f"| k-optimization time:     {self.k_opt_time} s")
                print(f"| Fill time:               {self.fill_time} s\n")
                print(f"k-opzimization:            {'ON' if self.k_opt else 'OFF'}\n")
                print(f"| Failed solves:           {self.failed_solves}")
                print(f"| Deus ex bans used:       {len(set().union(*(s.deus_ex_steps() for s in self.proof)))}")
                print(f"| Deus ex sets:            {self.deus_ex_sets}\n")
                print(f"Proof steps made:          {len(self.proof)}")
                print(f"| Weak k-approximations:   {sum((1 if (s.approximation or (not s.k_opt)) and s.k>8 else 0 for s in self.proof))}")
                print(f"| Strong k-approximations: {sum((1 if (s.approximation or (not s.k_opt)) and s.k<=8 else 0 for s in self.proof))}")
                print(f"| Maximal k:               {0 if len(self.proof)==0 else max((step.k for step in self.proof))}")
                
    # >>> UTILITY
    def is_unique(self):
        '''Checks whether this sudoku has a unique solution. See check_unicity().'''
        return check_unicity(self.board, False)
    
    def print_status(self):
        '''Prints a detailed representation of the current state of the puzzle. Each cell contains which numbers can be written there.'''
        print_detailed_board(self.board, [[self.allowed[r][c].allowed() for c in range(9)] for r in range(9)])
    
    def proof_to_string(self, idx, isvalue=False, reference=False):
        '''Converts the data of the ith proof step to a string.'''
        ret = f"[#{idx}, k={self.proof[idx].k}] {self.proof[idx].position} is {self.proof[idx].value}, because:\n\t"
        ret += "\n\t".join(self.proof[idx].to_strings(reference,isvalue))
        return ret

    def print_proof(self, file=None, start=0, end=None, isvalue=False, reference=False):
        '''Prints proof steps from #start to #end (default: 0 and last) to the specified file, or the console if file is None.'''
        if end is None: end = len(self.proof)
        if file is None:
            for i in range(start, end):
                print(self.proof_to_string(i,isvalue,reference))
        else:
            with open(file, 'w') as f:
                for i in range(start, end):
                    f.write(self.proof_to_string(i,isvalue,reference)+'\n')
    
    def ban(self, row, col, value, rule, cells_used):
        '''Ban value from (row, col) using 'rule' applied to 'reasons'.'''
        self.make_deduction(CantBe((row,col),value,'cell'),rule,cells_used)
        self.make_deduction(CantBe((row,col),value,'rowpos'),rule,cells_used)
        self.make_deduction(CantBe((col,row),value,'colpos'),rule,cells_used)
        self.make_deduction(CantBe((cell_section(row,col),global_to_local(row,col)),value,'secpos'),rule,cells_used)

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
    return (len(sols) == 1), sols 

if __name__ == "__main__":
    _opts, args = getopt(argv[1:],"hepl:",["link=","editor","passive"])
    opts = dict(_opts)
    listoflists = None
    if '-h' in opts:
        print("python sudoku.py {--link <link>} {--editor}")
    for opt, arg in opts.items():
        if opt == '-l' or opt == "--link":
            try:
                listoflists = fetch_puzzle(arg)
            except ValueError as e:
                print(f"ERROR: {str(e)}")
                print("Initializing empty board...")
                listoflists = [[0 for _ in range(9)] for _ in range(9)]
    for opt, arg in opts.items():
        if opt == '-e' or opt == '--editor':
            print("Starting sudoku editor. Press 'h' for help. Press 'q' to start the solving process.")
            listoflists = edit_sudoku(listoflists)
    if listoflists != None:
        su = Sudoku(board=listoflists)
        if ('-p' in opts) or ("--passive" in opts):
            su.solve()
            print_board(su.board)
        else:
            su.interactive_solve()
    else:
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
    if False: # TODO: move this to a different file?
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