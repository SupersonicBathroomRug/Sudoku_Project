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
    init_board(filled)
    solve() # this will actually solve the sudoku now, as this is a stronger solver

if __name__ == "__main__":
    example1()