from sys import getsizeof, stderr
from itertools import chain
from collections import deque
# try:
#     from reprlib import repr
# except ImportError:
#     pass

# def total_size(o, handlers={}, verbose=False):
#     """ Returns the approximate memory footprint an object and all of its contents.

#     Automatically finds the contents of the following builtin containers and
#     their subclasses:  tuple, list, deque, dict, set and frozenset.
#     To search other containers, add handlers to iterate over their contents:

#         handlers = {SomeContainerClass: iter,
#                     OtherContainerClass: OtherContainerClass.get_elements}

#     """
#     dict_handler = lambda d: chain.from_iterable(d.items())
#     all_handlers = {tuple: iter,
#                     list: iter,
#                     deque: iter,
#                     dict: dict_handler,
#                     set: iter,
#                     frozenset: iter,
#                    }
#     all_handlers.update(handlers)     # user handlers take precedence
#     seen = set()                      # track which object id's have already been seen
#     default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

#     def sizeof(o):
#         if id(o) in seen:       # do not double count the same object
#             return 0
#         seen.add(id(o))
#         s = getsizeof(o, default_size)

#         if verbose:
#             print(s, type(o), repr(o), file=stderr)

#         for typ, handler in all_handlers.items():
#             if isinstance(o, typ):
#                 s += sum(map(sizeof, handler(o)))
#                 break
#         return s

#     return sizeof(o)


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

import json
import difflib
from mangle import *

def istweak(a, b):
    e = difflib.SequenceMatcher(None, a.lower(),b.lower())
    #s = float(e)/ max(len(a), len(b))
    print a, b, e.ratio()
    return e.ratio()

        
if __file__ == sys.argv[0]:
    # T = Trie()
    # with open("cain.txt.bz2") as f:
    #     #for w in "a am iam anya anything anyt anarchy".split():
    #     for l in f.readlines():
    #         T.insert(l.strip()) 

    # #print (T);
    # print (T.__sizeof__(), T.max_prefix_match('anyass'))
    # V = {}
    # for l in open('weir_data.csv').readlines():
    #     l = l.split(',')
    #     if len(l)<5 or not l[3]: continue
    #     try: l[3].decode('ascii')
    #     except: continue
    #     try: V[l[5]].append(l[3])
    #     except KeyError: V[l[5]] = [l[3]]
    # with open('weir_pass.json', 'w') as fwrite:
    #     json.dump(V, fwrite)
    # exit(0)
    base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(sys.argv[1])
    T = Tokenizer(base_dictionary, tweak_fl)

    f = json.load(open('./weir_pass.json'))
    a=[]
    pass_len_dist = {}
    for v, plist in f.items():
        x = len(plist)
        if x <2: continue
        # print( x); continue
        uniq_ps = sorted(set(plist))
        #Tokens_list = [ T.tokenize(p)[1] for p in uniq_ps ]
        #print Tokens_list
        #continue

        try: pass_len_dist[x].append(len(uniq_ps));
        except: pass_len_dist[x] = [len(uniq_ps)]
        continue
        for i, p in enumerate(uniq_ps):
            for j in xrange(i+1, len(uniq_ps)):
                istweak(p, uniq_ps[j])
        continue
        if len(uniq_ps)>1:
            dist = [ sum([istweak(u,v) for u in uniq_ps])/float(len(uniq_ps)) for v in uniq_ps]
        print(uniq_ps, dist)
        a.append((x, len(uniq_ps), min(dist.count(1.0)+1, len(uniq_ps))))
        
    s=0
    for k,v in pass_len_dist.items():
        if len(v) > 6:
            print k, sum(v)/float(len(v))

#     a = sorted(a, key = lambda x: x[1])
# #    print (a)
#     b = sorted([ float(x[1])/x[0] for x in a] )
# #    print (b)
#     avg = sum(b)/ len(b)
#     print (avg)
