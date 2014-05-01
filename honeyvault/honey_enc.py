#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import sys, os, math, struct, bz2, resource
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from io import BytesIO
import string
from Crypto.Random import random
import marisa_trie
from collections import deque
from lexer.pcfg import TrainedGrammar, SubGrammar 
import honeyvault_config as hny_config
from helper.helper import getIndex, convert2group
from helper.vault_dist import VaultDistribution
from honeyvault_config import NONTERMINAL, TERMINAL
MAX_INT = hny_config.MAX_INT

# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

class DTE(object):
    def __init__(self, grammar=None):
        self.G = grammar
        if not self.G:
            self.G = TrainedGrammar()
            # self.G.load(hny_config.GRAMMAR_DIR+'/grammar.cfg')

    def encode(self, lhs, rhs):
        assert lhs in self.G
        a = self.G.encode_rule(lhs, rhs)
        if not a:
            print "NonERROR", lhs, rhs, a
            exit(0)
        return a

    def decode(self, lhs, pt):
        return self.decode_rule(lhs, pt)

    def encode_pw(self, pw):
        return self.G.encode_pw(pw)
    
    def decode_pw(self, P):
        return self.G.decode_pw(P)

    def __eq__(self, o_dte):
        return self.G == o_dte.G


class DTE_random(DTE):
    punct = "!@#%&*_+=~"
    All = string.ascii_letters + string.digits + punct
    must_set = [punct, string.digits, string.ascii_uppercase, string.ascii_lowercase]
    fact_map = [1, 2, 6, 24, 120, 720, 
                # 1, 2, 3, 4,  5,   6,
                5040, 40320, 362880, 3628800, 39916800,
                # 7,    8,     9,      10,      11
                479001600, 6227020800, 87178291200, 1307674368000, 20922789888000,
                # 12,      13,         14,          15,            16,
                355687428096000, 6402373705728000, 121645100408832000, 2432902008176640000
                # 17,            18,               19,                 20
                ]
    MAX_ALLOWED = 14
    RANDOM_LEN_PART = MAX_ALLOWED - 8 # 8 is the minimum length of the pass
    
    def __init__(self, size=10):
        self.pw, self.encoding = self.generate_and_encode_password(size)

    def generate_and_encode_password(self, size=10):
        N = [random.randint(0, MAX_INT) for i in range(size+1)]
        N[0] +=  (size - N[0] % self.MAX_ALLOWED)
        P = [s[N[i+1]%len(s)] for i,s in enumerate(self.must_set)]
        P.extend(self.All[n%len(self.All)] for n in N[len(self.must_set)+1:])
        n = random.randint(0, MAX_INT) 
        password = self.decode2string(n, P)
        N.append(n)
        extra = hny_config.PASSWORD_LENGTH - len(N);
        N.extend([convert2group(0,1) for x in range(extra)])
        return password, N

    @staticmethod
    def get_char(s, char_grp):
        for i, c in enumerate(s):
            if c in char_group:
                return i, c
        return 0, s[0]

    @staticmethod
    def get_random_for_this( c, arr ):
        i = arr.index(c)
        n = len(arr)
        return random.randint(0, MAX_INT/n) * n + t

    @staticmethod
    def encode2number( s ):
        sorted_s = sorted(s)
        n = len(s)
        code = 0
        for i, ch in enumerate(s):
            l = sorted_s.index(ch)
            code += l*DTE_random.fact_map[n-i-2]
            del sorted_s[l]
        p = random.randint(0, MAX_INT/DTE_random.fact_map[n-1])
        return DTE_random.fact_mapp[n-1] * p + code
    
    @staticmethod
    def decode2string(num, s):
        sorted_s = sorted(s)
        n = len(s)
        st = ['' for i in range(n)]
        num %= DTE_random.fact_map[n-1]
        for i in range(n):
            x = num/DTE_random.fact_map[n-i-2]
            num -= x*DTE_random.fact_map[n-i-2]
            st[i] = sorted_s[x]
            del sorted_s[x]
        return ''.join(st)
    
    def encode_pw(self, pw):
        p = list(pw[:])
        must_4 = [DTE_random.get_char(p, m) for m in must_set]
        for x in must_4:
            del p[x[0]]
        pw_random_order = DTE_random.decode2string(
            random.randint(0, self.fact_map[len(p)-1]),
            p )
        code_g = [random.randint(0, MAX_INT/self.MAX_ALLOWED) * \
                      self.MAX_ALLOWED + len(pw)]
        for i, x in enumerate(must_4):
            code_g.append(DTE_random.get_random_for_this(
                    x[1],must_set[i]))
        for p in pw_random_order:
            code_g.append(DTE_random.get_random_for_this(
                    p, All))
        code_g.append(encode2number(pw))
        extra = hny_config.PASSWORD_LENGTH - len(code_g);
        code_g.extend([convert2group(0,1) for x in range(extra)])
        return code_g
        
    def decode_pw(self, N):
        assert len(N) == hny_config.PASSWORD_LENGTH
        n = 8 + N[0] % self.RANDOM_LEN_PART # TODO: convert this info to public
        N = N[1:n+2]
        P = [s[N[i]%len(s)] for i,s in enumerate(self.must_set)]
        P.extend(self.All[n%len(self.All)] for n in N[len(self.must_set):-1])
        n = N[-1]
        password = self.decode2string(n, P)
        return password
        
        
    def generate_random_password(self, size=10 ):
        """
        Generates random password of given size
        it ensures -
        1 uppercase
        1 lowercase
        1 digit
        1 punc
        """
        get_rand = lambda L, c: [random.choice(L) for i in range(c)]
        P = [get_rand(g, 1) for g in self.must_set]
        P.extend([random.choice(self.All) for i in range(size - len(P))])
        n = random.randint(0, fact_map[size-1])
        return n, decode2string(n, P)


class DTE_large(DTE):
    """
    encodes a rule
    """
    def __init__(self, grammar=None):
        self.G = grammar
        if not self.G:
            self.G = TrainedGrammar()
            # self.G.load(hny_config.GRAMMAR_DIR+'/grammar.cfg')

    def encode(self, lhs, rhs):
        return self.G.encode_rule(lhs,rhs)

    def decode(self, lhs, pt):
        return self.G.decode_rule(lhs, pt)
        
    def get_freq(self, lhs, rhs):
        return self.G.get_freq(lhs, rhs)
        try:
            s, e = self.G.get_freq_range(lhs, rhs)
            return e-s
        except ValueError: 
            print "ValueError in get_freq -- %s is not in %s:" % \
                (rhs,self.G[lhs][0])
            return -1
    
    def encode_grammar(self, G):
        # Encode sub-grammar
        vd = VaultDistribution()
        stack = ['G']
        code_g = []
        done = []
        while stack:
            head = stack.pop()
            assert head not in done
            done.append(head)
            rule_dict = G[head]
            t_set = []
            for rhs, f in rule_dict.items():
                if rhs != '__total__':
                    r = filter(lambda x: x not in done+stack, 
                               self.G.get_actual_NonTlist(head, rhs))
                    if r:
                        for x in r:
                            if (x not in t_set):
                                t_set.append(x)
            t_set.reverse()
            stack.extend(t_set)
            print stack, '~~>', head, rule_dict
            n = len(rule_dict.keys())-1
            code_g.append(vd.encode_vault_size(head, n))
            if n<0: 
                print "Sorry I cannot encode your password! Please choose"
                print "something different, password12"
                exit(0)
            assert n == vd.decode_vault_size(head, code_g[-1])
            code_g.extend([self.encode(head, r) 
                           for r in rule_dict.keys()
                           if r != '__total__'])
        extra = hny_config.HONEY_VAULT_GRAMMAR_SIZE - len(code_g);
        code_g.extend([convert2group(0,1) for x in range(extra)])
        return code_g

    def decode_grammar(self, P):
        g=SubGrammar(self.G)
        vd = VaultDistribution()
        iterp = iter(P)
        stack = ['G']
        done = []
        while stack:
            head = stack.pop()
            assert head not in done
            done.append(head)
            p = iterp.next()
            n = vd.decode_vault_size(head, p)
            # print "RuleSizeDecoding:", head, n
            t_set = []
            for x in range(n):
                rhs = self.decode(head, iterp.next())
                # print "Decoding:", head, '==>', rhs
                if rhs != '__totoal__':
                    r = filter(lambda x: x not in done+stack, 
                               self.G.get_actual_NonTlist(head, rhs))
                    if r:
                        for x in r:
                            if (x not in t_set):
                                t_set.append(x)
                g.add_rule(head, rhs)
            t_set.reverse()
            stack.extend(t_set)
        g.fix_freq()
        return g

    def update_dte_for_vault(self, G):
        self.term_files_bak = self.term_files
        self.G_bak = self.G.G
        self.term_files = {}
        self.G.G = G;
        
        
def getVal( arr, val ):
    """
    arr -> is a list of values of type same as 'val' and also has a frequency
    e.g. arr: [['a',0,123], ['asd', 1, 31], ['ADR', 1, 345]]
    val -> is a value of same type of values in arr, e.g. 'asd'
    returns: a random number between, cumulative probability of 'asd' and
    the element just before it, i.e. 'a'.
    """
    c=0
    found = False
    totalC=0;
    t=-1;
    for i,x in enumerate(arr):
        #print x
        c += x[2]
        totalC += x[2]
        if not found and x[0] == val:
            if i==0: a = 0;
            else: a = c - x[2]
            t = random.randint( a, c-1 )
            found = True
            print x, t
    if t>-1:
        # to deal with floating this is used, basically converted the numebrs in (mod totalC)
        # ASSUMPTION: max value of sum of frequency is 4,294,967,295, i.e. ~ 4.29 billion!!
        return convert2group(t, totalC)
    return t


# def getIndex( arr, s, e, x ):
#     """
#     Binary searches for 'x' in 'arr' between indices 's' and 'e'.
#     :return `integer` index of x in arr s.t. arr[index-1] <= x < arr[index] 
#     """
#     if arr[s] > x: return s
#     if arr[e] < x: return e;
#     if arr[(s+e)/2] > x: return getIndex( arr, s, (s+e)/2, x )
#     else: return getIndex( arr, (s+e)/2+1, e, x);


def getGenerationAtRule( lhs, prob, grammar):
    """
    given a left hand side of a rule and the grammar it finds the exact rhs
    which has CP(cumulative Probability) in the ruleset just more than the given 
    `prob`
    :returns `('IloveYou',0,420)`
    """
    # REMEMBER: every array in grammar rule should have start with a
    # dummy entry('',0,0) and prob zero!!
    d = [0]

    d.extend([x[2] for x in grammar[lhs]])
    for i in xrange(1, len(d)):
        d[i] += d[i-1];
    prob = prob % d[-1]
    t = getIndex ( d, 0, len(d)-1, prob ) - 1;
    return grammar[lhs][t]


def Encode_spcl( m, grammar ):
    print "Special Encoding::::", m
    return None # TODO
    W = m # break_into_words(m, trie)
    P = ['%s%d' % (whatchar(w), len(w)) for w in W ]
    E = [];
    for w,p in zip(W[:-1], P[:-1]):
        E.append( getVal( grammar['S'], p+',S') )
        E.append( getVal( grammar[ p ], w ) );
    E.append( getVal( grammar[ 'S' ], P[-1]))
    E.append( getVal( grammar[P[-1]], W[-1]));
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend( [ convert2group(0,1) for x in range(extra) ] )
    return E;


def main():
    #print T.tokenize('P@$$w0rd', True)
    #exit(0)
    dte = DTE()
    scanner = Scanner()
    print "Resource:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
    #p='(NH4)2Cr2O7' # sys.stdin.readline().strip()
    p=u'iloveyou69'
    c = Encode(p, scanner, dte);
    #print "Encoding:", c
    m = Decode(c, dte);
    # print "After Decoding:", m
    #return
    #     if PASSWORD_LENGTH>0:
    for s in range(0000):
        E = []
        E.extend( [ convert2group(0,1) for x in range(PASSWORD_LENGTH) ] )
        c_struct = struct.pack('%sI' % len(E), *E )
        m = Decode(c_struct, dte);
        print s, ":", m



if __name__ == "__main__":
    main();
