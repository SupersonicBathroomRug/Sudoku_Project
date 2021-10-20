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

class diclen:
    '''A dictionary which counts how many 'None's it contains. No new keys may be added after creation, and no key can be assigned None
    to speed this code up.'''
    def __init__(self, dic = None):
        if isinstance(dic, dict):
            self.d = dic
            self.size = sum((1 if v == None else 0 for v in dic.values()))
        elif dic is None:
            self.d = {i: None for i in range(9)}
            self.size = 9
        else:
            self.d = {i: None for i in dic}
            self.size = len(self.d)
    
    def __len__(self):
        return self.size

    def __setitem__(self, key, value):
        old = self.d[key]
        self.d[key] = value
        if old is None and value is not None:
            self.size -= 1

    def __getitem__(self, key):
        return self.d[key]
    
    def last_one(self):
        '''Return the first key which has None assigned to it.'''
        for k, v in self.d.items():
            if v is None:
                return k
    
    def allowed(self):
        '''Returns a list of all the keys which have None assigned to them.'''
        return [k for k, v in self.d.items() if v is None]
    
    def items(self):
        return self.d.items()
    def values(self):
        return self.d.values()
    def keys(self):
        return self.d.keys()
    def __iter__(self):
        return iter(self.d)

# >>> KNOWLEDGE CLASSES
class Knowledge:
    '''Contains some information about that can help solve the sudoku. Stores a value and a position, which signify different things
    in each subclass. All derived classes must implement a __str__ method.'''
    def __init__(self, position, value, coordtype="cell"):
        '''Initiates a Knowledge instance. 'position' tells which cell this knowledge talks about. It can be given in multiple coordinate
        systems. "cell" means (0-8,0-8) tuple, "rowpos" means (row_idx, col_idx) tuple, "colpos" means (col_idx, row_idx) tuple,
        "secpos" means (sec_idx, (0-3,0-3)) tuple.'''
        self.position = position
        self.value = value
        self.coordtype = coordtype
    
    def get_pos(self):
        '''Returns the position of the cell this object stores information about in the 9×9 grid.'''
        if self.coordtype == "cell":
            return self.position
        elif self.coordtype == "rowpos":
            return self.position
        elif self.coordtype == "colpos":
            return self.position[1], self.position[0]
        elif self.coordtype == "secpos":
            return local_to_global(self.pos[0], *self.pos[1])
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
            (self.value == other.value) and \
            (self.position == other.position) and \
            (self.coordtype == other.coordtype)
    
    def __hash__(self):
        return hash((self.value, self.position, self.coordtype))

class IsValue(Knowledge):
    '''Says that this cell is already filled with this value'''
    def __str__(self):
        return f"({self.position[0]}, {self.position[1]}) is {self.value}"

class MustBe(Knowledge):
    '''Says that this cell should contain this value.'''
    def __str__(self):
        return f"({self.position[0]}, {self.position[1]}) must be {self.value}"

class CantBe(Knowledge):
    '''Says that this cell can't contain this value because it is restricted for some reason.'''
    def __str__(self):
        return f"({self.position[0]}, {self.position[1]}) can't be {self.value}"

# >>> DEDUCTION CLASSES
class Consequence:
    '''Stores the reasons for a given deduction. This is a separate class, because a given deduction may have multiple proofs.'''
    def __init__(self, of, rule):
        '''Initiates a Consequence object. 'rule' is a string id of the rule being applied. 'of' is a list of 
        Knowledge or Deduction instances, which imply the result.'''
        self.rule = rule
        self.of = of
    
    def __str__(self):
        return "CONSEQUENCE"
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
            (set(self.rule) == set(other.rule)) and \
            (self.of == other.of)
    
    def __hash__(self):
        return hash((self.rule, self.of))

class Deduction:
    '''Stores a Knowledge achieved by deduction with the possible ways to deduce this information.
    This class WON'T be seen at interface level.'''
    def __init__(self, consequence_of, result):
        '''Initiates a Deduction object. 'consequence_of' is a list of Consequence instances, 'result' is the knowledge deduced.'''
        self.result = result
        self.consequence_of = consequence_of
    
    def add_reason(self, reason):
        '''If 'reason' is not already in 'consequence_of', then append it.'''
        if reason not in self.consequence_of:
            self.consequence_of.append(reason)
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
            (self.consequence_of == other.consequence_of) and \
            (self.result == other.result)
    
    def __hash__(self):
        return hash((len(self.consequence_of), self.result)) # len: stop infinite recursion HERE!

# >>> OTHER
def make_deduction(knowledge, rule, cells_used):
    pass