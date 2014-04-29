#!/usr/bin/python
"""
This is a general grammar file that assumes the following grammar:
W -> <english-word>L | <name>L
D -> <date> | <phone-no> | [0-9]+
Y -> [^\W]+  # symbol
K -> <keyboard-sequence>
R -> repeat
S -> sequence # 123456, abcdef, ABCDEFG
L -> Capitalize | ALL-UPPER | all-lower | l33t
G -> <some-combination-of-those-NonTs>
"""

import os, sys, string
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG, DAWG
import marisa_trie
import struct, json, bz2, re
from lexer_helper import Date, KeyBoard, RuleSet
from helper.helper import open_, getIndex
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from collections import OrderedDict, defaultdict
from pprint import pprint

# Dictionaries:
# English_30000.dawg
# facebook-firstnames-withcount.dawg
# facebook-lastnames-withcount.dawg            

class NonT(object): # baseclass
    def __init__(self):
        self.sym = 'G'
        self.prob = 0.0
        self.prod = ''
    
    def symbol(self):
        return self.sym

    def probability(self):
        return self.prob

    def production(self):
        return self.prod

    def __str__(self):
        p_str = [str(p) for p in self.prod] \
            if isinstance(self.prod, list) \
            else self.prod
        
        return '%s: %s (%g)' % (self.sym, p_str,
                                self.prob)

    def parse_tree(self):
        p_tree = OrderedDict([('G', OrderedDict())])
        if isinstance(self.prod, basestring):
            return self.prod
        elif isinstance(self.prod, list):
            for i,c in enumerate(zip(self.sym, self.prod)):
                k, p = c
                k = '%s:%d' % (k, i)
                if isinstance(p, basestring):
                    p_tree['G'][k] = p
                else:
                    p_tree['G'][k] = p.parse_tree()
        else:
            return self.prod.parse_tree()
        return p_tree

    def rule_set(self):
        rs = RuleSet()
        pass

    def __nonzero__(self):
        return bool(self.prod) and bool(self.prob)
    __bool__ = __nonzero__


class NonT_L(NonT):
    sym, prod, prob  = 'L', '', 0.0
    def __init__(self, w, v):
        super(NonT_L, self).__init__()
        self.prod = None if not w.isalpha \
            else 'Caps' if w.istitle()  \
            else 'lower' if w.islower() \
            else 'UPPER' if w.isupper() \
            else 'l33t'
        self.r = w
        self.l = v
        if self.prod == 'l33t':
            c = len([c for c,d in zip(self.l,self.r)
                     if c != d])
            self.prob = 1 - c/len(self.r)
        else:
            self.prob = 1.0

    def pars_tree(self):
        p_tree = OrderedDict(dict)
        if self.prod == 'l33t':
            p_tree.update(dict(zip(self.l, self.r)))
        return p_tree

class NonT_W(NonT):
    sym, prod, prob = 'W', '', 0.0
    word_dawg  = IntDAWG().load('data/English_30000.dawg')
    fname_dawg = IntDAWG().load('data/facebook-firstnames-withcount.dawg')
    lname_dawg = IntDAWG().load('data/facebook-lastnames-withcount.dawg')
    total_f = word_dawg[u'__total__'] + \
        fname_dawg[u'__total__'] + \
        lname_dawg[u'__total__']

    l33t_replaces = DAWG.compile_replaces({
            '3':'e', '4':'a', '@':'a',
            '$':'s', '0':'o', '1':'i',
            'z':'s'
            })

    def __init__(self, word):
        # super(NonT_W, self).__init__()
        w = unicode(word.lower())
        dawg = []
        for d in [self.word_dawg, 
                  self.fname_dawg, 
                  self.lname_dawg]:
            k = d.similar_keys(unicode(w), self.l33t_replaces)
            if k:
                dawg.append((d,k[0]))
        if dawg:
            v = list(set([d[1] for d in dawg]))
            if len(v) > 1 or not v[0].isalpha():
                return 
            v = v[0]
            f = sum([d[0].get_value(unicode(v)) for d in dawg])
            L = NonT_L(word, v)
            self.prod = word
            self.L = L
            self.prob = L.prob * float(f)/self.total_f 

    def __str__(self):
        return '%s: %s<%s> (%g)' % (self.sym, self.prod,
                                    self.L, self.prob)
        
class NonT_D(NonT):
    sym, prod, prob = 'D', '', 0.0
    def __init__(self, w):
        # super(NonT_D, self).__init__()
        self.prod = Date(w)
        if not self.prod:
            if w.isdigit():
                self.prod = w
                self.prob = 0.001
        else:
            self.prob = 10**(len(w)-8)

class NonT_R(NonT): # repeat
    sym, prod, prob = 'D', '', 0.0
    def __init__(self, w):
        x = len(set(w))/float(len(w))
        if x<0.2:
            self.prob = 1 - float(x)/len(w)
            self.prod = w


class NonT_Q(NonT):
    ascii_u = string.ascii_uppercase
    ascii_l = string.ascii_uppercase
    pass

class NonT_K(NonT):
    pass


class NonT_Y(NonT):
    sym, prod, prob = 'Y', '', 0.0
    regex = r'^\W+$'
    def __init__(self, word):
        #super(NonT_Y, self).__init__()
        if re.match(self.regex, word):
            self.prod = word
            self.prob = 0.01

class NonT_combined(NonT):
    sym, prod, prob = 'C', '', 0.0
    def __init__(self, *nont_set):
        for p in nont_set:
            if not p: return 
        self.sym = ''.join([x.symbol() for x in nont_set])
        self.prod = []
        for p in nont_set:
            if isinstance(p.production(), list):
                self.prod.extend(p.production())
            else:
                self.prod.append(p)
        self.prob = prod([p.probability()
                          for p in nont_set])


def get_all_gen_rules(word):
    if not word: return None
    NonT_set = [NonT_W, NonT_D,
                NonT_Y]
    rules = filter(lambda x: x, [f(word) for f in NonT_set])
    if rules:
        return max(rules, key=lambda x: x.probability())

def prod(args):
    p = 1.0
    for i in args:
        p = p*i
    return p

def join_rules( *args ):
    for a in args:
        if not a: return None
    return NonT_combined(*args)

def gen_rule_set(nont):
    G = OrderedDict({'G': nont.symbol()})
    G.update(nont.rules())
    return G

def parse(word):
    A = {}
    for j in range(len(word)):
        for i in range(len(word)-j):
            A[(i, i+j)] = get_all_gen_rules(word[i:j+i+1])
            t = [A[(i, i+j)]]
            t.extend([NonT_combined(A[(i,k)], A[(k+1, i+j)])
                      for k in range(i, i+j)])
            t = filter(lambda x: x, t)
            if t:
                A[(i, i+j)] = \
                    max(t, key = lambda x: x.probability())
            else:
                A[(i, i+j)] = NonT()
                print "Not sure why it reached here. But it did!"
                print i, j, word[i: i+j+1]
                # exit(0)
    return A[(0, len(word)-1)]




if __name__ == "__main__":
    if sys.argv[1]=='-file':
        with open_(sys.argv[2]) as f:
            for i, line in enumerate(f):
                if i<1000: continue
                l = line.strip().split()
                w, c = ' '.join(l[1:]), int(l[0])
                print parse(w)
                if i>1200: break
    elif sys.argv[1] == '-word':
        print parse(sys.argv[2])
    elif sys.argv[1] == '-parse':
        T = parse(sys.argv[2])
        print T.parse_tree()
