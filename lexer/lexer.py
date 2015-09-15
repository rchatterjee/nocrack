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
from lexer_helper import Date, KeyBoard, RuleSet, ParseTree
from helper.helper import open_, getIndex
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from honeyvault_config import MEMLIMMIT, GRAMMAR_DIR
from collections import OrderedDict, defaultdict
from pprint import pprint
import resource  # For checking memory usage

# Dictionaries:
# English_30000.dawg
# facebook-firstnames-withcount.dawg
# facebook-lastnames-withcount.dawg            


NonT_length2classmap = {
    "W": {"1": [1, 2], "2": [3, 3], "3": [4, 4], "4": [5, 5], "5": [6, 6], 
          "6": [7, 7], "7": [8, 8], "8": [9, 9], "9": [9, 30]},
    "D": {"1": [1, 1], "2": [2, 3], "3": [4, 6], "4": [7, 9], "5": [10, 30]},
    "Y": {"1": [1, 1], "2": [2, 30]}
    }
def get_nont_class(nt, word):
    A = NonT_length2classmap.get(nt, {})
    n = len(word)
    for k,v in A.items():
        if n>=v[0] and n<=v[1]:
            return k

class NonT(object): # baseclass
    def __init__(self):
        #self.sym = 'G'
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
        p_tree = ParseTree()
        if isinstance(self.prod, basestring):
            return self.prod
        elif isinstance(self.prod, list):
            for p in self.prod:
                p_tree.add_rule((p.sym,p.parse_tree()))
        else:
            return self.prod.parse_tree()
        return p_tree

    def rule_set(self):
        rs = RuleSet()
        if isinstance(self, NonT):
            rs.add_rule('G', self.sym)
        if isinstance(self.prod, basestring):
            rs.add_rule(self.sym, self.prod)
        elif isinstance(self.prod, list):
            for p in self.prod:
                rs.update_set(p.rule_set())
        else:
            return self.prod.rule_set()
        return rs

    def __nonzero__(self):
        return bool(self.prod) and bool(self.prob)
    __bool__ = __nonzero__


class NonT_L(NonT):
    sym, prod, prob  = 'L', '', 0.0
    def __init__(self, v, w):
        super(NonT_L, self).__init__()
        self.prod = 'l33t' if not w.isalpha() \
            else 'Caps' if w.istitle()  \
            else 'lower' if w.islower() \
            else 'UPPER'
        self.r = w
        self.l = v
        if self.prod == 'l33t':
            c = len([c for c,d in zip(self.l,self.r)
                     if c != d.lower()])
            self.prob = 1 - c/len(self.r)
        else:
            self.prob = 1.0

    def parse_tree(self):
        p_tree = ParseTree()
        p_tree.add_rule(('L', self.prod))
        L = ['L_%s' % c for c in self.l]
        if self.prod == 'l33t':
            p_tree.add_rule(('l33t', zip(L, self.r)))
        return p_tree
    
    def rule_set(self):
        rs = RuleSet()
        rs.add_rule('L', self.prod)
        if self.prod is 'l33t':
            for c,d in zip(self.l, self.r):
                rs.add_rule('L_%s'%c,d)
        return rs

    def __str__(self):
        return "NonT_L: ({}, {})".format(self.l, self.r)

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
            k = d.similar_keys(w, self.l33t_replaces)
            if k:
                dawg.append((d,k[0]))
        if dawg:
            v = list(set([d[1] for d in dawg]))
            if len(v) > 1 or not v[0].isalpha():
                return 
            v = v[0]
            f = sum([d[0][v] for d in dawg])
            self.prod = v
            self.sym  = 'W%s' % get_nont_class('W', v)
            self.L = NonT_L(v, word)
            self.prob = self.L.prob * float(f)/self.total_f 

    def parse_tree(self):
        pt = ParseTree()
        pt.add_rule((self.sym, self.prod))
        pt.extend_rule(self.L.parse_tree())
        return pt

    def rule_set(self):
        rs = RuleSet()
        rs.add_rule(self.sym, self.prod)
        rs.update_set(self.L.rule_set())
        return rs

    def __str__(self):
        return '%s: %s<%s> (%g)' % (self.sym, self.prod,
                                    self.L, self.prob)

class NonT_D(NonT):
    sym, prod, prob = 'D', '', 0.0
    def __init__(self, w):
        # super(NonT_D, self).__init__()
        if w.isdigit():
            self.prod = w
            self.prob = 0.001
            self.sym  = 'D%s' % get_nont_class('D', w)
        d = Date(w)
        if d:
            self.sym = 'T'
            self.prod = d
            self.prob = 10**(len(w)-8)

    def parse_tree(self):
        if isinstance(self.prod, basestring):
            return ParseTree(self.sym, self.prod)
        else:
            return self.prod.parse_tree()

    def rule_set(self):
        if isinstance(self.prod, basestring):
            return RuleSet(self.sym, self.prod)
        else:
            return self.prod.rule_set()


class NonT_R(NonT): # repeat
    sym, prod, prob = 'R', '', 0.0
    def __init__(self, w):
        x = len(set(w))/float(len(w))
        if x<0.2:
            self.prob = 1 - float(x)/len(w)
            self.prod = w


class NonT_Q(NonT):
    sym, prod, prob = 'Q', '', 0.0
    ascii_u = string.ascii_uppercase
    ascii_l = string.ascii_uppercase
    pass

class NonT_K(NonT):
    pass


class NonT_Y(NonT):
    sym, prod, prob = 'Y', '', 0.0
    regex = r'^[\W_]+$'
    def __init__(self, word):
        #super(NonT_Y, self).__init__()
        if re.match(self.regex, word):
            self.prod = word
            self.prob = 0.01
            self.sym = 'Y%s' % get_nont_class('Y', word)


class NonT_combined(NonT):
    sym, prod, prob = 'C', '', 0.0
    def __init__(self, *nont_set):
        for p in nont_set:
            if not p: return
        self.sym = ','.join([x.symbol() for x in nont_set])
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
                NonT_Y, NonT_R]
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
    return NonT_combined(A[(0, len(word)-1)])



def check_resource(n=0):
    r = MEMLIMMIT*1024 - \
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
    print "Memory Usage:", (MEMLIMMIT - r/1024.0), "Lineno:", n
    if r < 0:
        print '''
Hitting the memory limit of 1GB,
please increase the limit or use smaller data set.
Lines processed, {0:d}
'''.format(n)
        return 0;
    return r/10+100;

    
def buildpcfg(passwd_dictionary, start=0, end=-1):
    #MIN_COUNT=1000
    R = RuleSet()
    # resource track
    out_grammar_fl = GRAMMAR_DIR + '/grammar.cfg.bz2'
    resource_tracker = 5240
    for n, line in enumerate(open_(passwd_dictionary)):
        if n<start: continue
        if n>end: break
        if n>resource_tracker:
            l = check_resource(n)
            if not l:
                break
            else:
                resource_tracker += l
        # if n%1000==0: print n;
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w, c = ' '.join(line[1:]), int(line[0])
        else:
            continue
            w, c = ' '.join(line), 1
        try:
            w.decode('ascii')
        except UnicodeDecodeError:
            continue    # not ascii hence return
        if c < MIN_COUNT : # or (len(w) > 2 and not w[:-2].isalnum() and len(re.findall(allowed_sym, w)) == 0):
            print "Word frequency dropped to %d for %s" % (c, w), n
            break  # Careful!!!
        T = parse(w)
        R.update_set(T.rule_set(), with_freq=True, freq=c)
    if end>0: return R
    R.save(bz2.BZ2File(out_grammar_fl, 'wb'))

def wraper_buildpcfg( args ):
    return buildpcfg( *args )

def parallel_buildpcfg(password_dictionary):
    from multiprocessing import Pool
    p = Pool()
    Complete_grammar = RuleSet()
    load_each = 10000
    a = [(password_dictionary, c, c+load_each)
         for c in range(0, 10**6, load_each)]
    R = p.map(wraper_buildpcfg, a)
    for r in R:
        Complete_grammar.update_set(r, with_freq=True)
    out_grammar_fl = GRAMMAR_DIR + '/grammar.cfg.bz2'
    Complete_grammar.save(bz2.BZ2File(out_grammar_fl, 'wb'))


if __name__ == "__main__":
    if sys.argv[1] == '-buildG':
        print buildpcfg(sys.argv[2], 0, 100)
    elif sys.argv[1] == '-buildparallelG':
        parallel_buildpcfg(sys.argv[2])
    elif sys.argv[1]=='-file':
        R = RuleSet()
        with open_(sys.argv[2]) as f:
            for i, line in enumerate(f):
                if i<5000: continue
                l = line.strip().split()
                w, c = ' '.join(l[1:]), int(l[0])
                try: w.decode('ascii')
                except UnicodeDecodeError:
                    continue    # not ascii hence return
                if not w or len(w.strip())<1:
                    continue
                T = parse(w)
                R.update_set(T.rule_set(), with_freq=True, freq=c)
                if i%100==0: print i
                if i>5200: break
        print R
    elif sys.argv[1] == '-parse':
        print parse(sys.argv[2]).parse_tree()
    elif sys.argv[1] == '-ruleset':
        T = parse(sys.argv[2])
        print T.rule_set()
