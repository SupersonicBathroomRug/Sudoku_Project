# ==========================================
#       SUDOKU MANAGEMENT & SOLVING
# ==========================================
from boardio import *
import copy
import numpy as np

board=[[0 for _ in range(9)] for _ in range(9)]
rows=[{i for i in range(1,10)} for j in range(9)]
cols=[{i for i in range(1,10)} for j in range(9)]
sections=[{i for i in range(1,10)} for j in range(9)]

rowpos=[[set(range(9)) for i in range(9)] for j in range(9)] #j. sorban az i hova mehet meg
colpos=[[set(range(9)) for i in range(9)] for j in range(9)] #j. oszlopban az i hova mehet meg
squarepos=[[set([(i,j) for i in range(3) for j in range(3)]) for _ in range(9)] for _ in range(9)]

# >>> HELPERS
def cell_section(i,j):
    return ((i)//3)*3+j//3

def local_to_global(sec,i,j):
    '''global coordinates of local i,j in sector sec'''
    return (sec//3*3+i,sec%3*3+j)

def global_to_local(i,j):
    return (i%3,j%3)

# >>> MANAGE BOARD WITH SOLVING IN MIND
def assign_cell(row,col,val):
    board[row][col]=val
    rows[row].discard(val)
    cols[col].discard(val)
    sections[cell_section(row,col)].discard(val)
    rowpos[row][val-1]=set()
    colpos[col][val-1]=set()
    squarepos[cell_section(row,col)][val-1]=set()
    for i in range(9):
        squarepos[cell_section(row,col)][i].discard(global_to_local(row,col))
    for i in range(9): #update rows and cols because of intersection
        rowpos[i][val-1].discard(col)
        colpos[i][val-1].discard(row)
    for i in range(9): #update own row and col
        rowpos[row][i].discard(col)
        colpos[col][i].discard(row)
        
    #update squarepos
    for i in range(9):
        squarepos[cell_section(i,col)][val-1].discard(global_to_local(i,col))
    for i in range(9):
        squarepos[cell_section(row,i)][val-1].discard(global_to_local(row,i))

def init_board(given):
    '''unsolved: list of tuples (row,col,val)'''
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
def check_unicity(board_to_solve):
    b=np.array(board_to_solve)
    sols=[]
    
    def nextcell(row,col):
        x=row*9+col+1
        return (x//9,x%9)

    def dfs(row,col):
        if row==9:
            sols.append(b.copy())
            print(b)
            return len(sols)>1
        if b[row][col]!=0:
            if dfs(*nextcell(row,col)):
                return True
            else:
                return False
            
        #filter possibilities
        possible=[True for i in range(9)]
        for i in range(9):
            if b[row][i]!=0:
                possible[b[row][i]-1]=False
        for i in range(9):
            if b[i][col]!=0:
                possible[b[i][col]-1]=False
        sec=cell_section(row,col)
        for i,j in [(i,j) for i in range(3) for j in range(3)]:
            tmp=b[sec//3*3+i][sec%3*3+j]
            if tmp!=0:
                possible[tmp-1]=False
        #recurse        
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

def solve():
    while True:
        for i in range(9):
            for j in range(9):
                if board[i][j]!=0:
                    continue
                tmp=rows[i]&cols[j]&sections[cell_section(i,j)]
                if len(tmp)==0:
                    print(f"cannot fill cell {i},{j}")
                    return
                if len(tmp)==1:
                    ass=list(tmp)[0]
                    assign_cell(i,j,ass)
                    
        for i in range(9):
            for j in range(9):
                if len(rowpos[i][j])==1:
                    assign_cell(i,list(rowpos[i][j])[0],j+1)
                if len(colpos[i][j])==1:
                    assign_cell(list(colpos[i][j])[0],i,j+1)
                if len(squarepos[i][j])==1:
                    assign_cell(*local_to_global(i,*list(squarepos[i][j])[0]),j+1)
        k=input()
        print_board(board)
        if k=="":
            continue
        if k=="q":
            break
        if k=="fuck":
            for row in range(9):
                for col in range(9):
                    if board[row][col]!=0:
                        continue
                    print(f"{row},{col}: {rows[row]&cols[col]&sections[cell_section(row,col)]}")
        else:
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
    #solve()

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