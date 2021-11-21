from tracker import Knowledge
from boardio import print

def _make_acyclic(step, stack, allowed_paths):
    '''Nearly exact copy of `ProofStep._make_acyclic`. Copied here, because for graph printing we don't want to init a new `ProofStep`.
    
    Calculate `allowed_paths`, so for each `Deduction` check which `Consequence`s don't lead to cycles, and store them in
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
            if not _make_acyclic(info, stack, allowed_paths):
                break
        else:
            possibles.append(cons)
    stack.remove(step)
    if len(possibles) == 0:
        return False
    allowed_paths[step] = possibles
    return True

def print_graph(deductions):
    '''Prints a graph of the acyclic version of the tree grown from the roots in the set `deductions`.'''
    # >>> REMOVE CYCLES
    allowed_paths = {} # Deduction -> list(Consequence): which Consequences may be used without causing cycles?
    #   only contain Deductions which can be resolved; serves as a "resolved" set too
    stack = set()
    for ded in deductions:
        _make_acyclic(ded, stack, allowed_paths)

    # >>> PREPARAIONS
    depth = {} # Deduction -> int: how deep is this node in the BFS tree?
    used_cols = set() # which cols are in use already?
    smallest_free_col = [] # for a depth layer, what is the first possibly free column (not blocked by previous Deduction-s in this layer)
    col = {} # Knowledge/Deduction -> int: what is the id of this Knowledge
    layers = [] # list[list[Deduction/Knowledge]]: nodes in this layer in order
    def _get_col(step, d):
        '''Get a free column at depth d, and update `used_cols` and `smallest_free_col`'''
        if d == len(smallest_free_col): # extend smallest_free_col and layers if necessary
            smallest_free_col.append(0) 
            layers.append([])
        i = smallest_free_col[d]
        while i in used_cols:
            i += 1
        used_cols.add(i)
        layers[d].append(step)
        if isinstance(step, Knowledge): # update smallest_free_col
            smallest_free_col[d] = i + 1
        else: # isinstance(step, Deduction)
            smallest_free_col[d] = i + len(allowed_paths[step])
        return i
    def _organize_tree(step):
        '''Calculate the `depth` or `col` value of this step and all others below it. Return the `depth` value of this `step`.'''
        if step in depth: # if already finished, return
            return depth[step]
        if isinstance(step, Knowledge):
            depth[step] = 0
            col[step] = _get_col(step, 0)
            return 0
        # isinstance(step, Deduction)
        d = 1
        for cons in allowed_paths[step]:
            for info in cons.of:
                d = max(d, _organize_tree(info)+1)
        depth[step] = d
        col[step] = _get_col(step, d)
        return d
    for ded in deductions:
        _organize_tree(ded)
    
    # >>> PRINT
    width = (max(col.values())+1)*2
    is_active = [False for _ in range(width)]
    base = lambda: ['│' if is_active[c] else ' ' for c in range(width)] # ||| vertical lines where necessary
    num_cons = lambda ded: len(allowed_paths[ded]) # number of consequences in this ded
    cons_col = lambda ded, i: (col[ded]-num_cons(ded)+1+i)*2 # col of the ith cons of ded
    for layer in layers[:0:-1]:
        for ded in layer:
            is_active[col[ded]*2+1] = False
            for i in range(num_cons(ded)):
                is_active[cons_col(ded, i)] = True
        factory = base()
        #  ┌─┬─┬O   │┌─┬O  ┌O
        for ded in layer:
            factory[col[ded]*2+1] = '0' if ded in deductions else 'O'
            factory[(col[ded]-num_cons(ded)+1)*2] = '┌'
            factory[(col[ded]-num_cons(ded)+1)*2+1:col[ded]*2+1] = '─┬'*(num_cons(ded)-1)
        print(''.join(factory))
        factory = base()
        #  k s│t    │q w   s
        for ded in layer:
            for i, cons in enumerate(allowed_paths[ded]):
                factory[cons_col(ded,i)] = cons.rule[0]
        print(''.join(factory))
        #  │ │││    ││ │   │
        print(''.join(base()))
        # ┌┴──┤│    │└┐│   │
        for j, ded in enumerate(layer):
            for i, cons in enumerate(allowed_paths[ded]):
                # prepare
                factory = base()
                joined_cols = {col[info] for info in cons.of}
                if len(joined_cols) == 0:
                    factory[cons_col(ded, i)] = '*'
                    print(''.join(factory))
                    continue
                first = min(joined_cols)*2+1
                last = max(joined_cols)*2+1
                source = cons_col(ded, i)
                # create text
                factory[min(first,source):max(last,source)+1] = '─'*(max(last,source)+1-min(first,source))
                for jc in joined_cols:
                    factory[2*jc+1] = '┬' #if not is_active[2*jc+1] else '┼'
                if source <= first:
                    factory[source] = '└'
                    factory[last]   = '┐' #if not is_active[last] else '┤'
                elif source > last:
                    factory[source] = '┘'
                    factory[first]  = '┌' #if not is_active[first] else '├'
                else:
                    factory[source] = '┴'
                    factory[first]  = '┌' #if not is_active[first] else '├'
                    factory[last]   = '┐' #if not is_active[last] else '┤'
                # update activity
                for jc in joined_cols:
                    is_active[2*jc+1] = True
                is_active[source] = False
                # print
                print(''.join(factory))
        #  │ │││    ││ │   │
        print(''.join(base()))
    # ***
    print(''.join(('*' if is_active[i] else ' ' for i in range(width))))