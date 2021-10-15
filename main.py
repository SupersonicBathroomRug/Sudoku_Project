# ======================================================
#                      MAIN WORKSPACE
# ======================================================
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
    print("[SOLVING]")
    sud.interactive_solve()
    
    

if __name__ == "__main__":
    example2()