# ======================================================
#       CONVERTING INTPUT TO A STANDARDISED FORMAT
#                           &
#                 DRAWING PRETTY OUTPUT
# ======================================================

# >>> MANAGING INPUT FROM TEXT/LISTS
def init_tuples_from_text(s):
    '''Given a text with 9 rows, each containing 9 characters, create a list of (row, col, value) tuples for the characters in the text
    which are in {1,2,3,4,5,6,7,8,9}.'''
    nums=set(map(str,range(1,10)))
    ret=[]
    r=0
    c=0
    for i in range(90):
        if i%10==9:
            r+=1
            c=0
            continue
        if s[i] in nums:
            ret.append((r,c,int(s[i])))
        c+=1
    return ret

def gridtext_to_arraytext(s):
    '''Given a text with 9 rows, each containing 9 digits, create a repr of a list of lists containing these numbers.'''
    n="[["
    for char in s:
        if char=='\n':
            n+="],\n["
        else:
            n+=char+", "
    return n
        
# >>> OUTPUT   
def print_board(board):
    '''Print the 9×9 board, with spaces in cells containing 0.'''
    for i in range(9):
        if i%3==0 and i!=0:
            print("─────────┼─────────┼─────────")
        for j in range(9):
            if board[i][j]==0:
                print("   ",end="")
            else:
                print(f" {board[i][j]} ",end="")
            if j%3==2:
                print("|",end="")
        print()

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
'''[1:]
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