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
