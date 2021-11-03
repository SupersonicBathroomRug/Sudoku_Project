# =======================================================
#       TRACKING AND STORING WHAT IMPLIES WHAT
#                          &
#               PRETTY PRINTING PROOFS
# =======================================================

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
    
    def notNones(self):
        '''Return a list of all values which are not None.'''
        return [v for v in self.d.values() if v is not None]
    
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
    '''Contains some information about a cell that can help solve the sudoku. Stores a `value` and a `position`, which signify different things
    in each subclass. All derived classes must implement a `__str__` method.'''
    def __init__(self, position, value, coordtype="cell"):
        '''Initiates a `Knowledge` instance. `position` tells which cell this knowledge talks about. It can be given in multiple coordinate
        systems. 
        -   `"cell"` means `(0-8,0-8)` tuple,
        -   `"rowpos"` means `(row_idx, col_idx)` tuple,
        -   `"colpos"` means `(col_idx, row_idx)` tuple,
        -   `"secpos"` means `(sec_idx, (0-3,0-3))` tuple.'''
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
            return local_to_global(self.position[0], *self.position[1])
    
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
        return f"{self.get_pos()} is {self.value}"

class MustBe(Knowledge):
    '''Says that this cell should contain this value.'''
    def __str__(self):
        return f"{self.get_pos()} must be {self.value}"

class CantBe(Knowledge):
    '''Says that this cell can't contain this value because it is restricted for some reason.'''
    def __str__(self):
        return f"{self.get_pos()} can't be {self.value}"

# >>> DEDUCTION CLASSES
class Consequence:
    '''Stores the reasons for a given deduction. This is a separate class, because a given deduction may have multiple proofs.'''
    def __init__(self, of, rule, details=None):
        '''Initiates a `Consequence` object. `rule` is a string id of the rule being applied. `of` is a `list` of 
        `Knowledge` or `Deduction` instances, which imply the result. `details` may store additional info about the deduction
        (such as which are the two cells we use `<naked pairs>` for).'''
        self.rule = rule
        self.of = list(set(of))
        self.details = details
    
    def __str__(self):
        if self.rule == 'deus_ex':
            return 'because the gods said so'
        elif self.rule == 'allowed':
            return 'because only this number can be written here'
        elif self.rule == 'rowpos':
            return 'because this number can only go here in its row'
        elif self.rule == 'colpos':
            return 'because this number can only go here in its column'
        elif self.rule == 'secpos':
            return 'because this number can only go here in its 3x3 square'
        else:
            raise 'because [UNDEFINED RULE]'
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
            (set(self.rule) == set(other.rule)) and \
            (self.of == other.of) and \
            (self.details == other.details)
    
    def __hash__(self):
        return hash((self.rule, self.of))

class Deduction:
    '''Stores a `Knowledge` achieved by deduction with the possible ways to deduce this information.'''
    def __init__(self, consequence_of, result):
        '''Initiates a `Deduction object`. `consequence_of` is a list of `Consequence` instances, `result` is the knowledge deduced.'''
        self.result = result
        self.consequence_of = consequence_of
    
    def add_reason(self, reason):
        '''If `reason` is not already in `consequence_of`, append it. Return `True` if this was a new reason.'''
        if reason not in self.consequence_of:
            self.consequence_of.append(reason)
            return True
        return False
    
    def __str__(self):
        '''Only converts the first reasoning to string!'''
        return str(self.result)+", "+str(self.consequence_of[0])
    
    def __eq__(self, other):
        return id(self) == id(other)
    
    def __hash__(self):
        return hash(id(self)) # len: stop infinite recursion HERE!

class ProofStep:
    '''Describes the reasoning behind filling a particular cell. Stores a list with the steps of the proof in order.\\
    Can answer questions such as "How many/which cells are used over all?", "What is k?", "Print this!".\n
    Member variables:\\
    `position`: `tuple(0-8, 0-8)`
    >   Which position did we fill?\n
    `value`: `int`
    >   What value did we fill in?\n
    `k`: `int`
    >   How many cells are used overall?\n
    `proof`: `list(Knowledge/Deduction instances)`
    >   The steps of the proof in order.\n
    `proof_order`: `dict(Knowledge/Deduction -> idx)`
    >   Inverse of `proof`.\n
    `k_opt`: `bool`
    >   Was this proofstep optimized to use the smallest `k` possible?`\n
    `approximation`: `bool`
    >   Did this proofstep use some sort of approximation? If `k_opt` is `False`, or k-optimization wasn't "pure" (proof structure
        was not acyclic), then this is `True`.'''
    def __init__(self, deductions, k_opt=False, choose_resolution=True):
        '''Initiates a `ProofStep` instance wrapping deduction. Accepts a set of deductions, and chooses one to use.\n
        If `k_opt` is `True`, it attempt to fill the cell which requires the least amount of knowledge. Otherwise it fills the
        first cell. In that case, if `choose_resolution` is `True`, deduction will be converted to the standard format, 
        stripping away redundant Consequences recursively; the resulting proof structure will be acyclic.'''
        self.proof_order = {}
        self.proof = []
        self.k = 0
        self.k_opt = k_opt
        if True: # TODO: k_opt == False
            self.approximation = True
            deduction = next(iter(deductions))
            ProofStep._remove_fulfilled_deductions(deductions, deduction)
            self.position = deduction.result.get_pos()
            self.value = deduction.result.value
            # REMOVE CYCLES AND REDUNDANCY
            if choose_resolution:
                stack = set() # is this step currently in the recursion stack?
                resolved = set() # has a resolution been found for this step?
                def strip_redundancy(step):
                    '''Strip redundant `Consequence`s. Return `True` if a resolution is found that doesn't use step's consequences,
                    `False` otherwise.'''
                    if step in stack:
                        return False
                    elif step in resolved:
                        return True
                    elif isinstance(step, Knowledge):
                        return True
                    stack.add(step)
                    # isinstance(step, Deduction)
                    chosen_consequence = None
                    for cons in step.consequence_of: # iterate over all possible reasonings...
                        for info in cons.of: # if all the predicates can be properly resolved..
                            if not strip_redundancy(info):
                                break
                        else:
                            chosen_consequence = cons
                            break
                    else:
                        stack.remove(step)
                        return False
                    step.consequence_of = [chosen_consequence]
                    resolved.add(step)
                    stack.remove(step)
                    return True
                strip_redundancy(deduction)
            # CREATE TOPOLOGICAL ORDERING OF PROOF
            def topological_ordering(step):
                '''Find a topological ordering of the proof, and store it in `self.proof`'''
                if step in self.proof_order:
                    return
                elif isinstance(step, Knowledge): # isinstance(step, IsValue)
                    self.proof_order[step] = len(self.proof)
                    self.proof.append(step)
                    self.k += 1
                    return
                # isinstance(step, Deduction)
                for info in step.consequence_of[0].of:
                    topological_ordering(info)
                self.proof_order[step] = len(self.proof)
                self.proof.append(step)
            topological_ordering(deduction)
        else: # k_opt == True
            self.approximation = False
            # ^this may be set to True later on!
    
    def to_strings(self, reference=False, include_isvalue=False):
        '''Return a list of strings, each representing a step of this proof.'''
        if not reference and not include_isvalue:
            i = 0
            ret = []
            for step in self.proof:
                if isinstance(step, Deduction):
                    ret.append(f'(L{i}) '+str(step))
                    i += 1
            return ret
        elif not reference and include_isvalue:
            return [f'(L{i}) '+str(step) for i, step in enumerate(self.proof)]
        elif reference and not include_isvalue:
            d = {}
            ret = []
            i = 0
            for step in self.proof:
                if isinstance(step, Deduction):
                    d[step] = len(ret)
                    ret.append(f'(L{i}) '+str(step)+" [{0}]".format(', '.join((str(d[s]) for s in step.consequence_of[0].of if isinstance(s, Deduction)))))
                    i += 1
            return ret
        else:
            ret = []
            for i, step in enumerate(self.proof):
                if isinstance(step, Deduction):
                    ret.append(f'(L{i}) '+str(step)+" [{0}]".format(', '.join((str(self.proof_order[s]) for s in step.consequence_of[0].of))))
                else: # isinstance(step, IsValue)
                    ret.append(f'(L{i}) '+str(step))
            return ret
    
    # >>> GETTERS
    def cells(self):
        '''Returns which cells are used overall in this proofstep in a `list`.'''
        c = []
        for p in self.proof:
            if isinstance(p, IsValue):
                c.append(p.get_pos())
        return c
    
    def deus_ex_steps(self):
        '''Returns which `Knowledge` instances were obtained directly by `deus ex` in a set.'''
        de = set()
        for p in self.proof:
            if isinstance(p, Deduction) and p.consequence_of[0].rule == "deus_ex":
                de.add(p.result)
        #print(*(str(f) for f in de))
        return de

    @staticmethod
    def _remove_fulfilled_deductions(deductions, deduction):
        '''Removes deductions from `deductions` which deduce the filling of the same cell as in `deduction`. Helper function'''
        to_remove = []
        p = deduction.result.get_pos()
        for d in deductions:
            if d.result.get_pos() == p:
                to_remove.append(d)
        deductions.difference_update(to_remove) # -= is risky!!!

