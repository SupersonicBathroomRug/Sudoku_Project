# ======================================================
#       CONVERTING INTPUT TO A STANDARDISED FORMAT
#                           &
#                 DRAWING PRETTY OUTPUT
# ======================================================
import re
import numpy as np
import requests
import bs4 # type: ignore
import sys
import builtins

from Getch import getch
from consolestyle import bclr

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

# >>> Custom print to make printing to files easier.
class MyPrint:
    '''Wrapper for the print funtcion to make printing to files with it easier.'''
    def __init__(self):
        self.file = sys.stdout
    
    def set_file(self, path):
        '''From now on print into this file! (None or '': print to console.)'''
        if self.file != sys.stdout:
            self.file.close()
        if path is None or path == '':
            self.file = sys.stdout
        else:
            self.file = open(path, 'w', encoding='utf-8')
    
    def reset(self):
        '''Return to printing to the console.'''
        if self.file != sys.stdout:
            self.file.close()
            self.file = sys.stdout
    
    def __call__(self, *args, **kwargs):
        builtins.print(*args,**kwargs,file=self.file) # noqa

print = MyPrint()

# >>> MANAGING INPUT FROM TEXT/LISTS
def init_tuples_from_text(s):
    '''Given a text with 9 rows, each containing 9 characters, create a list of `(row, col, value)` tuples for the characters in the text
    which are in `{1,2,3,4,5,6,7,8,9}`.'''
    nums=set(map(str,range(1,10)))
    ret=[]
    rows = re.findall(r'(\S{9})(?!(?=\S))', s) # finds all occurences of exactly-9-non-whitespace characters
    if len(rows) != 9:
        raise ValueError(f"Could not interpret input as a sudoku table: number of rows were {len(rows)}")
    for r, row in enumerate(rows):
        for c in range(9):
            if row[c] in nums:
                ret.append((r,c,int(row[c])))
    return ret

def init_tuples_from_array(a):
    ret = []
    for r, row in enumerate(a):
        for c in range(9):
            if 0 < row[c]:
                ret.append((r,c,row[c]))
    return ret

def gridtext_to_arraytext(s):
    '''Given a text with 9 rows, each containing 9 digits, create a repr of a list of lists containing these numbers.'''
    return '['+',\n '.join(('['+', '.join(c for c in row)+']') for row in s.split())+']'

# >>> ADVANCED
def edit_sudoku(board=None):
    '''Edit a sudoku board. Navigate the cells with `wasd`, delete with 0 or `x`, fill a cell by typing the desired number.\\
    Quit with `q`, get this help with `h`.'''
    if board is None: board = [[0 for _ in range(9)] for _ in range(9)]
    selected = [4, 4]
    nums = set(map(str,range(10)))
    while(True):
        print_board(board, selected)
        i = getch().decode('utf-8')
        if i in nums:
            board[selected[0]][selected[1]] = int(i)
        elif i == 'w':
            selected[0] = (selected[0]+8)%9
        elif i == 's':
            selected[0] = (selected[0]+1)%9
        elif i == 'a':
            selected[1] = (selected[1]+8)%9
        elif i == 'd':
            selected[1] = (selected[1]+1)%9
        elif i == 'x':
            board[selected[0]][selected[1]] = 0
        elif i == 'h':
            print('''Edit a sudoku board. Navigate the cells with wasd, delete with 0 or x, fill a cell by typing the desired number.
Quit with 'q', get this help with 'h'.''')
        elif i == 'q':
            return board

def fetch_puzzle(url):
    '''Downloads a puzzle from a given `url`, and converts it into a `list` of `list`s. Currently only supports 
    puzzles on http://nine.websudoku.com/.'''
    if re.match(r'https?://(?:nine|www)\.websudoku\.com/', url) is not None:
        results = requests.get(url, headers=headers)
        soup = bs4.BeautifulSoup(results.text, features='lxml')
        buttons = [row.select('input') for row in soup.select('table[id="puzzle_grid"] tr')]
        values = [[int(button['value']) if 'value' in button.attrs else 0 for button in row] for row in buttons]
        return values
    else:
        raise ValueError(f"Downloading puzzles is not supported from {url}.")

# >>> OUTPUT   
def print_board(board, selected=(9,9)):
    '''Print the 9×9 board, with spaces in cells containing 0.'''
    print("┌─────────┬─────────┬─────────┐")
    for i in range(9):
        if i%3==0 and i!=0:
            print("├─────────┼─────────┼─────────┤")
        for j in range(9):
            if j%3==0:
                print("│",end="")
            to_print = ' ' if board[i][j]==0 else board[i][j]
            if i == selected[0] and j == selected[1]:
                print(f"[{to_print}]",end="")
            else:
                print(f" {to_print} ",end="")
        print("│")
    print("└─────────┴─────────┴─────────┘")

def print_detailed_board(board, possibles, selected=(9,9)):
    '''Print a detailed version of an ongoing solve. Only printing happens here.'''
    print("╔═════════╤═════════╤═════════╦═════════╤═════════╤═════════╦═════════╤═════════╤═════════╗")
    for i in range(9):
        if i%3 != 0:
            print("╟─────────┼─────────┼─────────╫─────────┼─────────┼─────────╫─────────┼─────────┼─────────╢")
        elif i != 0:
            print("╠═════════╪═════════╪═════════╬═════════╪═════════╪═════════╬═════════╪═════════╪═════════╣")
        for r in range(3):
            for j in range(9):
                if j%3 == 0:
                    print("║",end="")
                else:
                    print("│",end="")
                if board[i][j] == 0:
                    tp = [' ' if 3*r+k+1 not in possibles[i][j] else 3*r+k+1 for k in range(3)]
                    print((bclr.RED if selected==(i,j) else "") +f" {tp[0]}  {tp[1]}  {tp[2]} {bclr.ENDC}",end="")
                elif r == 0:
                    print((bclr.RED if selected==(i,j) else "")+f"  ┏━━━┓  {bclr.ENDC}",end="")
                elif r == 1:
                    print((bclr.RED if selected==(i,j) else "")+f"  ┃ {board[i][j]} ┃  {bclr.ENDC}",end="")
                else:
                    print((bclr.RED if selected==(i,j) else "")+f"  ┗━━━┛  {bclr.ENDC}",end="")
            print("║")
    print("╚═════════╧═════════╧═════════╩═════════╧═════════╧═════════╩═════════╧═════════╧═════════╝")

def print_raw_board(board):
    '''Print the board with only the numbers visible, 0-s for empty cells, newlines between lines of the board.'''
    for line in board:
        print(''.join((str(i) for i in line)))

def print_array_board(board):
    '''Print the board in an array format'''
    for i, line in enumerate(board):
        print("[[" if i==0 else " [",', '.join((str(i) for i in line)),'],' if i < 8 else ']]',sep='')

if __name__ == "__main__":
    # init_tuples_from_text test
    print("--- Testing init_tuples_from_text()")
    s='''
    1....847.
    5........
    .4...1.3.
    ...2.....
    ...3.46..
    ..81.....
    ....6...5
    ...8.5.2.
    .6.437...
    '''
    tupes=init_tuples_from_text(s)
    print(repr(tupes))

    # gridtext_to_arraytext test
    print("--- Testing gridtext_to_arraytext()")
    print(gridtext_to_arraytext('''100008470
        500000000
        040001030
        000200000
        000304600
        008100000
        000060005
        000805020
        060437000'''))
    
    # edit_sudoku test
    print("--- Testing edit_sudoku()")
    print(np.array(edit_sudoku()))

    # fetch_puzzle test
    print("--- Testing fetch_puzzle()")
    print_board(fetch_puzzle("https://nine.websudoku.com/?level=3&set_id=10297219193"))