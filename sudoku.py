# ==========================================
#       SUDOKU MANAGEMENT & SOLVING
# ==========================================

# standard modules
import numpy as np
import re
import time
import builtins
from sys import argv
from getopt import getopt
from itertools import product
import os.path
# custom modules
from consoleapp import ConsoleApp
import boardio
from boardio import print
from deduction_rules import hidden_pair, nake_pair, only_one_value, only_this_cell
from tracker import CantBe, Consequence, Deduction, IsValue, MustBe, ProofStep
from graph import print_graph
from util import cell_section, local_to_global, global_to_local, diclen

sudoku_app = ConsoleApp(description='INTERACTIVE SUDOKU SOLVER')
sudoku_app.add_variable(r'k[-_]opt(?:imi[zs]ation)?',ConsoleApp.Patterns.BOOLONOFF,'Should we minimize k in the solving process?')
sudoku_app.add_variable(r'[iI][pP][-_][tT](?:ime)?(?:[-_]?[lL]im(?:it)?)?',ConsoleApp.Patterns.FLOAT,
    'How much time should be given to the IP solver in each iteration? Setting to non-positive values will disable the time limit.')
sudoku_app.add_function(r'set',[(r'row',r'\d'),(r'col(?:umn)?',r'\d:?'),(r'val(?:ue)?',r'\d')],description=
    '''Set the cell given by 'row' and 'column' to value 'value', if possible.''')
sudoku_app.add_function(r'ban',[(r'cells',r'(?:\d[,;\s]*\d[,;\s]*)+:'),(r'values',r'(?:[,;\s]*\d)*')],description=
    '''Ban from the cells given in 'cells' in the format 'cell1_row,cell1_col cell2_row,cell2_col ...:' the values given in 'values'.
Note that there must be a separating ':' between 'cells' and 'values'.''')
sudoku_app.add_function(r'u(?:nique)?|check_unicity',[],description=
    '''Check whether this sudoku has a unique solution. Prints the solution if it is so, or two solutions, if it is not.''')
sudoku_app.add_function(r'print',[(r'file',ConsoleApp.Patterns.TEXT,"")],r'-?-?r(?:aw)?',r'-?-?a(?:rray)?',r'-?-?s(?:mall)?',description=
    '''Prints the board to the console (to a file, if a file is specified in a string). Flags:
--raw:   print only the numbers which are filled in, with 0 for empty cells, no superfluous characters
--array: print the Sudoku.board array in a python array-style
--small: the sudoku will be pretty printed, but only the filled in values are shown''')
sudoku_app.add_function(r'proof',[(r'slice',r'\d*\s*:\s*\d*',':'),(r'file',ConsoleApp.Patterns.TEXT,"")],
    r'-?-?r(?:ef(?:erence)?)?',r'-?-?[Ii](?:s[Vv]alue)?',description=
    '''Prints the proof constructed so far to the console (or the given file, e.g. "proof.txt"). A 'slice' is a start:end slice notation,
where either or both arguments may be omitted: if this is given, only these proof steps will be printed.''')
sudoku_app.add_function(r'stat(?:istic)?s?',[(r'file',ConsoleApp.Patterns.TEXT,"")],description=
    '''Prints some detailed statistics about the solving process so far, such as total runtime.''')
sudoku_app.add_function(r'origin(?:al)?|og?|puzzle',[],description=
    '''Prints the original puzzle to the console.''')
sudoku_app.add_function(r'export',[(r'file',ConsoleApp.Patterns.TEXT)],
    r'-?-?n(?:ostats?)?',r'-?-?r(?:aw)?',r'-?-?a(?:rray)?',r'-?-?r(?:ef(?:erence)?)?',r'-?-?[Ii](?:s[Vv]alue)?',description=
    '''Prints information about this session to a file. If --nostats is enabled, statistics will not be printed.''')
sudoku_app.add_function(r'step',[(r'n',ConsoleApp.Patterns.UINT,'1'),(r'file',ConsoleApp.Patterns.TEXT,'')],r'-?-?graph',r'-?-?proof',description=
    '''Fill a cell 'n' times. If the '--graph' flag is enabled, print a graph of k-optimization problem in each step to
'file' (if it is not specified, to the console). If the '--proof' flag is enabled, the ProofStep of the current steps will be printed.''')
sudoku_app.add_function(r'',[],description=
    '''Attempts to solve the sudoku from this state.''')

class Sudoku:
    '''A class representing a 9×9 sudoku board. Capable of solving the sudoku. Contains large amounts of helper data.'''

    # >>> DATA MANIPULATION
    def __init__(self, board=None, tuples=None, k_opt=False, ip_time_limit=0.5):
        '''Initialize a sudoku either with:\n
        `board`: `list` of `list`s
        >   A matrix representation of the sudoku table, with 0s in empty cells.\n
        `tuples`: `Iterable` of `(row, column, value)` tuples
        >   An `Iterable` containing an entry for each filled cell of the board.'''
        if tuples is not None:
            pass
        elif board is not None:
            tuples = boardio.init_tuples_from_array(board)
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
        self.ip_time_limit = ip_time_limit
        self.deduction_time = 0
        self.k_opt_time = 0
        self.fill_time = 0
        self.failed_solves = 0
        self.deus_ex_sets = 0
        for row, col, val in tuples:
            self[row, col] = val
        self.starting_board = [[self.board[i][j] for j in range(9)] for i in range(9)]
    
    def __setitem__(self, key, val):
        '''Fill in the given cell with the given value.\\
        Take note of the new restricions this causes, and stop tracking this value & position further.'''
        if val == 0:
            raise ValueError("Cannot assign 0 to any cell!")
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
        '''Store a deduction which yields `knowledge` applying `rule` to `Knowlegde` instances `reasons`.\\
        Return `True` if this is a new deduction.'''
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
        '''Given a Knowledge instance `k`, returns the data stored at its position, corresponding to its value.\\
        This means it either returns a `Deduction` instance (if this knowledge has been already acquired), and `None` otherwise.'''
        if k.coordtype == "cell":
            return self.allowed[k.position[0]][k.position[1]][k.value]
        elif k.coordtype == "rowpos":
            return self.rowpos[k.position[0]][k.value-1][k.position[1]]
        elif k.coordtype == "colpos":
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
        elif k.coordtype == "colpos":
            self.colpos[k.position[0]][k.value-1][k.position[1]] = deduction
        elif k.coordtype == "secpos":
            self.secpos[k.position[0]][k.value-1][k.position[1]] = deduction
    
    # >>> SOLVERS
    def solve_step(self, graph=False):
        '''Attempts to fill a single cell of the sudoku using a fixed set of deductions. Return `True` if the sudoku is complete, `False` if
        the filling attempt failed, and `None` otherwise. If `graph` is True, a graph of the k-optimization problem will be printed using `print`.'''
        if self.missing == 0:
            return True
        timestamp = time.time()
        made_deduction = True
        # MAKE DEDUCTIONS WHILE POSSIBLE
        while made_deduction:
            made_deduction = False
            only_one_value(self)
            only_this_cell(self)
            made_deduction |= nake_pair(self)
            made_deduction |= hidden_pair(self)

        self.deduction_time += time.time() - timestamp
        timestamp = time.time()
        # EXIT IF NECESSARY
        if len(self.filler_deductions) == 0:
            self.failed_solves += 1
            return False
        # DECIDE HOW TO PROVE THIS STEP
        if graph:
            print_graph(self.filler_deductions)
        proofstep = ProofStep(self.filler_deductions, self.k_opt, self.ip_time_limit)
        self.proof.append(proofstep)
        self.k_opt_time += time.time() - timestamp
        timestamp = time.time()
        # FILL THE SELECTED CELL
        self[proofstep.position] = proofstep.value
        self.fill_time += time.time() - timestamp
        return None

    def solve(self): # TODO: shortcut in case of k_opt==False?
        '''Attempts to solve this sudoku only using a fixed set of deductions. Return `True` if the sudoku has been solved, and `False` if the
        solve failed.'''
        answer = None
        while answer is None:
            answer = self.solve_step()
        return answer

    def interactive_solve(self):
        '''Interactive solver tool. Type `'h'` or `'help'` for help.'''
        print("   INTERACTIVE SOLVER STARTED  ")
        boardio.print_board(self.board)
        for action, rname, data in sudoku_app:
            if action == 'func' and rname == "step":
                file = ConsoleApp.get_text(data['params']['file'])
                base, ext = os.path.splitext(file)
                if file != '':
                    if data['flags'][r'-?-?graph']:
                        print(f"Printing graphs to file {base+'(i)'+ext}.")
                    else:
                        print("WARNING: '--graph' flag is OFF, no graph printing will happen.")
                for i in range(int(data['params']['n'])):
                    print.set_file((base+f'({i})'+ext) if file != '' else '')
                    ret = self.solve_step(data['flags'][r'-?-?graph'])
                    print.reset()
                    if ret is None:
                        if data['flags'][r'-?-?proof']:
                            self.print_proof(len(self.proof)-1)
                        else:
                            print(f"Step #{i} complete, there are still empty cells.")
                    elif ret:
                        print("          =========================   SUDOKU COMPLETE   =========================          ")
                        boardio.print_board(self.board)
                    else:
                        print("Solver got stuck at this state:")
                        self.print_status()
                        break
            if action == 'func' and rname == "": # Attempt solve
                if self.solve():
                    print("          =========================   SUDOKU COMPLETE   =========================          ")
                    boardio.print_board(self.board)
                else:
                    print("Solver got stuck at this state:")
                    self.print_status()
            elif action == 'func' and rname == r'print': # Print
                file = ConsoleApp.get_text(data['params']['file'])
                if file != '':
                    print(f"Printing board to file {file}")
                print.set_file(file)
                if data['flags'][r'-?-?r(?:aw)?']:
                    boardio.print_raw_board(self.board)
                elif data['flags'][r'-?-?a(?:rray)?']:
                    boardio.print_array_board(self.board)
                elif data['flags'][r'-?-?s(?:mall)?']:
                    boardio.print_board(self.board)
                else:
                    self.print_status()
                print.reset()
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
                    boardio.print_board(sols[0])
                else:
                    print("[NOT UNIQUE] This puzzle has multiple solutions. Two of these are:")
                    boardio.print_board(sols[0])
                    boardio.print_board(sols[1])
            elif action == 'func' and rname == 'proof':
                file = ConsoleApp.get_text(data['params']['file'])
                if file != '':
                    print(f"Printing output to {file}")
                # Simplify k:
                data['params']['slice'] = re.sub(r'[^\d:]','',data['params']['slice'])
                # Process k into proper slice indicies:
                halves = data['params']['slice'].split(':')
                start = int(halves[0]) if halves[0] != '' else 0
                end = int(halves[1]) if halves[1] != '' else len(self.proof)
                if end > len(self.proof):
                    builtins.print(f"WARNING: specified range too large; proof only has {len(self.proof)} steps so far.")
                # Execute printing:
                print.set_file(file)
                self.print_proof(start, min(end, len(self.proof)),
                    isvalue=data['flags'][r'-?-?[Ii](?:s[Vv]alue)?'], 
                    reference=data['flags'][r'-?-?r(?:ef(?:erence)?)?'])
                print.reset()
            elif action == 'get_var' and rname == r'k[-_]opt(?:imi[zs]ation)?':
                print(f"k-optimization: {'ON' if self.k_opt else 'OFF'}")
            elif action == 'set_var' and rname == r'k[-_]opt(?:imi[zs]ation)?':
                self.k_opt = ConsoleApp.str_to_bool(data)
                print(f"k-optimization was set to {self.k_opt}")
            elif action == 'get_var' and rname == r'[iI][pP][-_][tT](?:ime)?(?:[-_]?[lL]im(?:it)?)?':
                if self.ip_time_limit is None:
                    print("ip-time-limit is UNLIMITED")
                else:
                    print(f"ip-time-limit: {self.ip_time_limit} s")
            elif action == 'set_var' and rname == r'[iI][pP][-_][tT](?:ime)?(?:[-_]?[lL]im(?:it)?)?':
                f = float(data)
                if f <= 0:
                    self.ip_time_limit = None
                    print(f"ip-time-limit was set to UNLIMITED")
                else:
                    self.ip_time_limit = f
                    print(f"ip-time-limit was set to {f} s")
            elif action == 'func' and rname == r'stat(?:istic)?s?':
                file = ConsoleApp.get_text(data['params']['file'])
                if file != '':
                    print(f"Printing statistics to {file}")
                print.set_file(file)
                self.print_stats()
                print.reset()
            elif action == 'func' and rname == r'export':
                file = ConsoleApp.get_text(data['params']['file'])
                print(f"Exporting session data to {file}")
                print.set_file(file)
                print("STARTING BOARD:")
                if data['flags'][r'-?-?r(?:aw)?']:
                    boardio.print_raw_board(self.starting_board)
                elif data['flags'][r'-?-?a(?:rray)?']:
                    boardio.print_array_board(self.starting_board)
                else:
                    boardio.print_board(self.starting_board)
                print("FINAL BOARD:")
                if data['flags'][r'-?-?r(?:aw)?']:
                    boardio.print_raw_board(self.board)
                elif data['flags'][r'-?-?a(?:rray)?']:
                    boardio.print_array_board(self.board)
                else:
                    boardio.print_board(self.board)
                print("PROOF:")
                self.print_proof(isvalue=data['flags'][r'-?-?[Ii](?:s[Vv]alue)?'], reference=data['flags'][r'-?-?r(?:ef(?:erence)?)?'])
                if not data['flags'][r'-?-?n(?:ostats?)?']:
                    print("STATISTICS:")
                    self.print_stats()
                print.reset()
            elif action == 'func' and rname == r'origin(?:al)?|og?|puzzle':
                boardio.print_board(self.starting_board)
                
    # >>> UTILITY
    def is_unique(self):
        '''Checks whether this sudoku has a unique solution. See `check_unicity()`.'''
        return check_unicity(self.board, False)
    
    def print_status(self):
        '''Prints a detailed representation of the current state of the puzzle. Each cell contains which numbers can be written there.'''
        boardio.print_detailed_board(self.board, [[self.allowed[r][c].allowed() for c in range(9)] for r in range(9)])
    
    def proof_to_string(self, idx, isvalue=False, reference=False):
        '''Converts the data of the ith proof step to a string.'''
        ret = f"[#{idx}, k={self.proof[idx].k}, k-opt={self.proof[idx].k_opt}, approx={self.proof[idx].approximation}]\n"
        ret += f"  {self.proof[idx].position} is {self.proof[idx].value}, because:\n\t"
        ret += "\n\t".join(self.proof[idx].to_strings(reference,isvalue))
        return ret

    def print_proof(self, start=0, end=None, isvalue=False, reference=False):
        '''Prints proof steps from #start to #end (default: 0 and last) to the specified file, or the console if file is None.'''
        if end is None: end = len(self.proof)
        for i in range(start, end):
            print(self.proof_to_string(i,isvalue,reference))

    def print_stats(self):
        print(f"RUNTIME:                   {self.deduction_time+self.k_opt_time+self.fill_time} s")
        print(f"| Deduction time:          {self.deduction_time} s")
        print(f"| k-optimization time:     {self.k_opt_time} s")
        print(f"| Fill time:               {self.fill_time} s\n")
        print(f"k-opzimization:            {'ON' if self.k_opt else 'OFF'}")
        print(f"ip-time-limit:             {'UNLIMITED' if self.ip_time_limit is None else f'{self.ip_time_limit} s'}\n")
        print(f"| Failed solves:           {self.failed_solves}")
        print(f"| Deus ex bans used:       {len(set().union(*(s.deus_ex_steps() for s in self.proof)))}")
        print(f"| Deus ex sets:            {self.deus_ex_sets}\n")
        print(f"Proof steps made:          {len(self.proof)}")
        print(f"| k-optimized steps:       {sum((1 if s.k_opt else 0 for s in self.proof))}")
        print(f"| Weak k-approximations:   {sum((1 if s.approximation and s.k>8 else 0 for s in self.proof))}")
        print(f"| Strong k-approximations: {sum((1 if s.approximation and s.k<=8 else 0 for s in self.proof))}")
        print(f"| Maximal k:               {max((step.k for step in self.proof),default=0)}")
        print(f"| Maximal optimized k:     {max((step.k for step in self.proof if step.k_opt),default=0)}")
        print(f"| Mean k:                  {0 if len(self.proof)==0 else sum((step.k for step in self.proof))/len(self.proof)}")

    def ban(self, row, col, value, rule, cells_used):
        '''Ban `value` from `(row, col)` using `rule` (`str`  identifier) applied to `cells_used` (`list` of `Knowledge`/`Deduction` instances).'''
        made_deduction = False
        made_deduction |= self.make_deduction(CantBe((row,col),value,'cell'),rule,cells_used)
        made_deduction |= self.make_deduction(CantBe((row,col),value,'rowpos'),rule,cells_used)
        made_deduction |= self.make_deduction(CantBe((col,row),value,'colpos'),rule,cells_used)
        made_deduction |= self.make_deduction(CantBe((cell_section(row,col),global_to_local(row,col)),value,'secpos'),rule,cells_used)
        return made_deduction

# >>> SOLVERS
def check_unicity(board_to_solve, verbose=False):
    '''Attempts to decide whether this sudoku has a unique solution with a DFS search.\\
    Returns 
    -   `(True, [unique_solution])`, if the solution is unique,
    -   `[solution_no1, solution_no2]` if there are at least two solutions.'''
    b=np.array(board_to_solve)
    sols=[]
    
    def nextcell(row,col):
        '''Returns the coordinates of the next cell in reading order. ISN'T CYCLIC, doesn't work for the last cell.'''
        x=row*9+col+1
        return (x//9,x%9)

    def dfs(row,col):
        '''Attempts to fill this cell and then recursively all cells after this.\\
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
                listoflists = boardio.fetch_puzzle(arg)
            except ValueError as e:
                print(f"ERROR: {str(e)}")
                print("Initializing empty board...")
                listoflists = [[0 for _ in range(9)] for _ in range(9)]
    for opt, arg in opts.items():
        if opt == '-e' or opt == '--editor':
            print("Starting sudoku editor. Press 'h' for help. Press 'q' to start the solving process.")
            listoflists = boardio.edit_sudoku(listoflists)
    if listoflists != None:
        su = Sudoku(board=listoflists)
        if ('-p' in opts) or ("--passive" in opts):
            su.solve()
            boardio.print_board(su.board)
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
        sud = Sudoku(tuples=boardio.init_tuples_from_text('''
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