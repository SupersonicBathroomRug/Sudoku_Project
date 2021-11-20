# =======================================================
#       TRACKING AND STORING WHAT IMPLIES WHAT
#                          &
#               PRETTY PRINTING PROOFS
# =======================================================

from util import local_to_global
import pulp as pl # type: ignore
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
        elif self.rule == 'nake_pair':
            return 'because of nake_pair' # TODO
        elif self.rule == 'hidden_pair':
            return 'because of hidden_pair' # TODO
        else:
            return 'because UNDEFINED RULE'
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
            (set(self.rule) == set(other.rule)) and \
            (self.of == other.of) and \
            (self.details == other.details)
    
    def __hash__(self):
        return hash((self.rule, tuple(self.of)))

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
        stripping away redundant Consequences recursively; the resulting proof structure will be acyclic.
        `chosen_reasons`: Deduction -> Consequence (which reasoning did we choose?)'''
        self.proof_order = {}
        self.proof = []
        self.k = 0
        self.chosen_reasons = {}
        self.approximation = False
        # ^this may be set to True later on!
        chosen_deduction = None # which value of `deductions` will we use?
        if k_opt:
            allowed_paths = {} # Deduction -> list(Consequence): which Consequences may be used without causing cycles?
            #   only contain Deductions which can be resolved; serves as a "resolved" set too
            stack = set()
            # REMOVE CYCLES
            for ded in deductions:
                self._make_acyclic(ded, stack, allowed_paths)
            # CREATE IP PROBLEM
            prob = pl.LpProblem(name='k-optimize') # LP problem
            isvalue_used = [] # list of LpBinary, containing all LpBinary-s corresponding to IsValue instances
            # final_deductions = {} # filler_deduction -> LpBinary; see below
            knowledge_used = {} # Knowledge/Deduction -> LpBinary dict, collecting all variables describing knowledge usage
            reasons_chosen = {} # Deduction -> {Consequence -> LpBinary}
            # CREATE CONSTRAINTS & VARIABLES
            final_deductions = {ded: self._add_to_lp_problem(ded,prob,knowledge_used,isvalue_used,reasons_chosen,allowed_paths)
                for ded in deductions}
            # > fill at least 1 cell
            prob += (pl.lpSum((v for v in final_deductions.values())) >= 1)
            # > optimize for minimal k
            prob += pl.lpSum((v for v in isvalue_used))
            # SOLVE IP PROBLEM
            if prob.solve(pl.PULP_CBC_CMD(msg=0)) == 1: # if solve failed: revert to bruteforce
                # CONVERT SOLUTION TO PROOFSTEP
                for ded in deductions:
                    if pl.value(knowledge_used[ded]) == 1.0:
                        self._choose_resolution_by_IP(ded, reasons_chosen, allowed_paths)
                        chosen_deduction = ded
                        break
            else:
                print('ERROR: IP solver failed.')
                k_opt = False
        if not k_opt: # k_opt == False, or k-optimization failed miserably
            self.approximation = True
            chosen_deduction = next(iter(deductions))
            # REMOVE CYCLES AND REDUNDANCY
            self._choose_resolution_greedy(chosen_deduction, stack=set(), resolved=set())
        # CREATE TOPOLOGICAL ORDERING OF PROOF
        self._topological_ordering(chosen_deduction) # top. order
        ProofStep._remove_fulfilled_deductions(deductions, chosen_deduction) # remove redundant goals
        self.position = chosen_deduction.result.get_pos() # save core info
        self.value = chosen_deduction.result.value
        self.k_opt = k_opt
    
    # >>> __init__ HELPERS (RECURSIONS)
    def _make_acyclic(self, step, stack, allowed_paths):
        '''Calculate `allowed_paths`, so for each `Deduction` check which `Consequence`s don't lead to cycles, and store them in
        `allowed_path[ded]`, a `list`. Return `True` if `step` can be resolved. The main goal of this function is to fill `allowed_paths` and
        make it possible for the IP solver to solve the problem properly.\\
        Of course, this function may be used instead of `_chose_resolution_greedy()` for `k_opt==False` too, but it would not eliminate the need
        for a separate `choose_resolution` function for that case, and would deactivate some speedups implemented in `_chose_resolution_greedy()`
        too.\n
        `stack` is a set of the `step`s which depend on this `step`, and are currently being processed in the recursion. `allowed_paths` is a dict
        that assignes to resolvable `Deduction`s the `Consequences` it can use to resolve itself.'''
        if step in stack:
            return False
        elif step in allowed_paths:
            return True
        elif isinstance(step, Knowledge):
            return True
        stack.add(step)
        possibles = []
        for cons in step.consequence_of: # iterate over all possible reasonings...
            for info in cons.of: # if all predicates can be peacefully resolved:
                if not self._make_acyclic(info, stack, allowed_paths):
                    self.approximation = True
                    break
            else:
                possibles.append(cons)
        stack.remove(step)
        if len(possibles) == 0:
            return False
        allowed_paths[step] = possibles
        return True
    def _add_to_lp_problem(self, step, prob, knowledge_used, isvalue_used, reasons_chosen, allowed_paths):
        '''Recursively add this `step` and everything it depends on to the LP problem (and save the new variables to the next 3 parameters).
        This means create a variable for it and save its constraints. Returns with `knowledge_used[step]` for convenience reasons.\n
        `knwoledge_used` is a `dict` that contains the IP variables for each `Knowledge/Deduction`\\
        `isvalue_used` is a `list` of all IP variables which correspond to `IsValue` instances\\
        `reasons_chosen` is a `dict(Deduction->dict(Consequence->IP_var))` structure\\
        `allowed_paths` is a `dict` which tells for each `Deduction` which of its `Consequence`s can be used (calculated by `_make_acyclic()`)'''
        if step in knowledge_used: # if this has already been visited and converted: return
            return knowledge_used[step]
        ipvar = pl.LpVariable(name=f'd_{id(step)}',cat=pl.LpBinary)
        knowledge_used[step] = ipvar # save
        if isinstance(step, IsValue):
            isvalue_used.append(ipvar)
        if isinstance(step, Knowledge):
            return ipvar
        # isinstance(step, Deduction)
        cipvars = {}
        for cons in allowed_paths[step]:
            cipvar = pl.LpVariable(name=f'o_{id(cons)}',cat=pl.LpBinary)
            cipvars[cons] = cipvar
            # > if we want to use a reasoning, we have to fulfill all its criteria
            prob += (cipvar*(-len(cons.of)) + pl.lpSum((self._add_to_lp_problem(info,prob,knowledge_used,isvalue_used,reasons_chosen,allowed_paths)
                for info in cons.of)) >= 0)
        reasons_chosen[step] = cipvars # save these variables too for later use
        # > if we want to use this deduction, we have to use at least 1 of its reasonings
        prob += (ipvar*(-1) + pl.lpSum((v for v in cipvars.values())) >= 0)
        return ipvar
    def _choose_resolution_by_IP(self, step, reasons_chosen, allowed_paths):
        '''Convert the IP solution data of the `reasons_chosen` variable to a resolution of `step`'''
        if not isinstance(step, Deduction):
            return
        elif step in self.chosen_reasons: # if already decided
            return
        for cons in allowed_paths[step]:
            if pl.value(reasons_chosen[step][cons]) == 1.0: # if this is the chosen reasoning for this Deduction
                for info in cons.of:
                    self._choose_resolution_by_IP(info, reasons_chosen, allowed_paths)
                self.chosen_reasons[step] = cons
                return
    def _choose_resolution_greedy(self, step, stack, resolved):
        '''If `step` is a `Deduction` instance in a possibly cyclic proof structure, choose one of its `Consequence` objects that don't lead
        to cyclic reasoning, and also do this for every `Deduction` instance that that `Consequence` instance depends on, and so on. Return `True`,
        if this `step` can be resolved. This function's purpose is to fill `self.chosen_reasons`.\\
        `stack` is a `set` that contains the `Knowledge`/`Deduction` instances which are going to be part of the resolution, but depend on this
        `step`: this helps eliminate cyclic proofs. `resolved` is a `set` of all instances that have a proper resolution assigned to them.'''
        if step in stack:
            return False
        elif step in resolved:
            return True
        elif isinstance(step, Knowledge):
            return True
        stack.add(step)
        # isinstance(step, Deduction)
        for cons in step.consequence_of: # iterate over all possible reasonings...
            for info in cons.of: # if all the predicates can be properly resolved...
                if not self._choose_resolution_greedy(info, stack, resolved):
                    break
            else:
                self.chosen_reasons[step] = cons
                break
        else:
            stack.remove(step)
            return False
        resolved.add(step)
        stack.remove(step)
        return True
    def _topological_ordering(self, step):
        '''Using `self.chosen_reasons`, find a topological ordering of the (selected) proof, and store it in `self.proof` & `self.proof_order`.
        Also, determine `self.k` by increasing it with each `Knowledge` instance added to the proof.\\
        Finds a topological ordering for the given `step` and everything it depends on.'''
        if step in self.proof_order: # if already processed...
            return
        elif isinstance(step, Knowledge): # isinstance(step, IsValue)
            self.proof_order[step] = len(self.proof)
            self.proof.append(step)
            self.k += 1
            return
        # isinstance(step, Deduction)
        for info in self.chosen_reasons[step].of:
            self._topological_ordering(info)
        self.proof_order[step] = len(self.proof)
        self.proof.append(step)
    
    # >>> OTHER FUNCTIONS
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

