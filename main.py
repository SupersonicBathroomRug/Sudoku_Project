# ======================================================
#                      MAIN WORKSPACE
# ======================================================
from boardio import fetch_puzzle
from sudoku import *


# >>> EXAMPLE 1
# -------------
# ezt innen nem lehet 1 mezőre kizártakat nézve folytatni viszont X helyére mehet csak az ő sorában 7
# 749|   |865|
# 612| 5 | X4|
# 358|  4|   |
# ───┼───┼───
# 4 5|7  | 9 |
#    |4  |   |
#    |5 6|7  |
# ───┼───┼───
# 1  |2 7|   |
# 86 | 9 |  2|
#    |   |   |
# -------------
# Input code for this example:
def example1():
    filled=[
        (0,2,9), (0,6,8), (0,7,6), (0,8,5),
        (1,1,1), (1,2,2), (1,4,5), (1,8,4),
        (2,0,3), (2,5,4),
        (3,0,4), (3,2,5), (3,3,7), (3,7,9),
        (4,3,4),
        (5,3,5), (5,5,6), (5,6,7),
        (6,0,1), (6,3,2), (6,5,7),
        (7,0,8), (7,1,6), (7,4,9), (7,8,2)
    ]
    sud = Sudoku(tuples=filled)
    sud.interactive_solve() # this will actually solve the sudoku now, as this is a stronger solver

# >>> EXAMPLE 2
# ┌─────────┬─────────┬─────────┐
# │         │ 8     1 │         │
# │         │         │    4  3 │
# │ 5       │         │         │
# ├─────────┼─────────┼─────────┤
# │         │    7    │ 8       │
# │         │         │ 1       │
# │    2    │    3    │         │
# ├─────────┼─────────┼─────────┤
# │ 6       │         │    7  5 │
# │       3 │ 4       │         │
# │         │ 2       │ 6       │
# └─────────┴─────────┴─────────┘
# This puzzle has a unique solution, with the minimal number of clues (17) given. No deductions are possible with the first two
# rules, however. Furthermore, checking whether the solution is unique takes too much time now.
def example2():
    s ='''000801000
        000000043
        500000000
        000070800
        000000100
        020030000
        600000075
        003400000
        000200600'''
    b = [[0, 0, 0, 8, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 4, 3],
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 7, 0, 8, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 2, 0, 0, 3, 0, 0, 0, 0],
        [6, 0, 0, 0, 0, 0, 0, 7, 5],
        [0, 0, 3, 4, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 6, 0, 0]]
    sud = Sudoku(board=b)
    #print(check_unicity(b, verbose=True))
    sud.interactive_solve()

# >>> EXAMPLE 3
# This is a not particularly exciting example, but the classic 8-moves do not solve it. However with the help of naked
# tuples it can be completed.
def example3():
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

# >>> EXAMPLE ywing1
# This is an example where you can use ywing
def example_ywing1():
    sud = Sudoku(board=[
        [9, 0, 0, 2, 4, 0, 0, 0, 0], 
        [0, 5, 0, 6, 9, 0, 2, 3, 1], 
        [0, 2, 0, 0, 5, 0, 0, 9, 0], 
        [0, 9, 0, 7, 0, 0, 3, 2, 0], 
        [0, 0, 2, 9, 3, 5, 6, 0, 7], 
        [0, 7, 0, 0, 0, 2, 9, 0, 0], 
        [0, 6, 9, 0, 2, 0, 0, 7, 3], 
        [5, 1, 0, 0, 7, 9, 0, 6, 2], 
        [2, 0, 7, 0, 8, 6, 0, 0, 9]])
    sud.interactive_solve()

# >>> EXAMPLE ywing2
# This is an example where you can use ywing
def example_ywing2():
    sud = Sudoku(board=[
        [9, 0, 0, 2, 4, 0, 0, 0, 0], 
        [0, 5, 0, 6, 9, 0, 2, 3, 1], 
        [0, 2, 0, 0, 5, 0, 0, 9, 0], 
        [0, 9, 0, 7, 0, 0, 3, 2, 0], 
        [0, 0, 2, 9, 3, 5, 6, 0, 7], 
        [0, 7, 0, 0, 0, 2, 9, 0, 0], 
        [8, 6, 9, 0, 2, 1, 0, 7, 3], 
        [5, 1, 0, 0, 7, 9, 0, 6, 2], 
        [2, 0, 7, 0, 9, 6, 0, 0, 9]])
    sud.interactive_solve()


# >>> EXAMPLE hidden_triples
# This is an example where you can use hidden_triples
def example_hidden_triples():
    sud = Sudoku(board=[
        [0, 0, 0, 0, 0, 1, 0, 3, 0], 
        [2, 3, 1, 0, 9, 0, 0, 0, 0], 
        [0, 6, 5, 0, 0, 3, 1, 0, 0], 
        [6, 7, 8, 9, 2, 4, 3, 0, 0], 
        [1, 0, 3, 0, 5, 0, 0, 0, 6], 
        [0, 0, 0, 1, 3, 6, 7, 0, 0], 
        [0, 0, 9, 3, 6, 0, 5, 7, 0], 
        [0, 0, 6, 0, 1, 9, 8, 4, 3], 
        [3, 0, 0, 0, 0, 0, 0, 0, 0]])
    sud.interactive_solve()


# >>> EXAMPLE TO COPY
# TODO
def example_to_copy():
    sud = Sudoku(board=[
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 0, 0, 0, 0, 0, 0]])
def xwingtest():
    sud=Sudoku(board=
        [[1,0,0,0,0,0,5,6,9],
         [4,9,2,0,5,6,1,0,8],
         [0,5,6,1,0,9,2,4,0],
         [0,0,9,6,4,0,8,0,1],
         [0,6,4,0,1,0,0,0,0],
         [2,1,8,0,3,5,6,0,4],
         [0,4,0,5,0,0,0,1,6],
         [9,0,5,0,6,1,4,0,2],
         [6,2,1,0,0,0,0,0,5]])
    sud.interactive_solve()

def swordfishtest():
    sud=Sudoku(board=
        [[5,2,9,4,1,0,7,0,3],
         [0,0,6,0,0,3,0,0,2],
         [0,0,3,2,0,0,0,0,0],
         [0,5,2,3,0,0,0,7,6],
         [6,3,7,0,5,0,2,0,0],
         [1,9,0,6,2,7,5,3,0],
         [3,0,0,0,6,9,4,2,0],
         [2,0,0,8,3,0,6,0,0],
         [9,6,0,7,4,2,3,0,5]])
    sud.interactive_solve()

def fetchsolve(url="https://nine.websudoku.com/?level=4&set_id=6169806040"):
    sud=Sudoku(board=fetch_puzzle(url))
    sud.interactive_solve()

if __name__ == "__main__":
    fetchsolve()