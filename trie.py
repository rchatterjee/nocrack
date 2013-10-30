from __future__ import print_function
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
try:
    from reprlib import repr
except ImportError:
    pass

def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


##### Example call #####

#if __name__ == '__main__':
#    d = dict(a=1, b=2, c=3, d=[4,5,6,7], e='a string of chars')
#    print(total_size(d, verbose=True))



import os,sys

END = '#'
class Trie:
    def __init__(self):
        self.Tree = dict()
    
    def insert( self, w):
        T=self.Tree 
        for c in w:
            if c in T:
                T = T[c]
            else:
                T[c] = dict()
                T = T[c]
        T[END]=dict()

    def max_prefix_match(self, w):
        T=self.Tree
        for i,c in enumerate(w):
            if c in T:
                T = T[c]
            else:
                return w[:i]
        return w;
    
    def __str__(self):
        return str(self.Tree)

    def __sizeof__(self):
        T = self.Tree
        s = 0;
        for k in T:
            s += getsizeof(T[k]) + sys.getsizeof(k)
        return s;

if __file__ == sys.argv[0]:
    T = Trie()
    with open("cain.txt.bz2") as f:
        #for w in "a am iam anya anything anyt anarchy".split():
        for l in f.readlines():
            T.insert(l.strip()) 

    #print (T);
    print (T.__sizeof__(), T.max_prefix_match('anyass'))



