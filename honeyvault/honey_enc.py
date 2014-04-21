#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import sys, os, math, struct, bz2, resource
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from io import BytesIO
from Crypto.Random import random
import marisa_trie
from collections import deque
from scanner.scanner_helper import GrammarStructure
from scanner.scanner import Scanner, Grammar
import honeyvault_config as hny_config
from helper.helper import getIndex, convert2group
from helper.vault_dist import VaultDistribution
from honeyvault_config import NONTERMINAL, TERMINAL
# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

class DTE(object):
    def __init__(self, grammar=None):
        self.G = grammar
        if not self.G:
            self.G = Grammar()
            self.G.load(hny_config.GRAMMAR_DIR+'/grammar.cfg')

    def encode(self, lhs, rhs):
        assert lhs in self.G
        s, e  = self.G.get_freq_range(lhs, rhs)
        return convert2group(random.randint(s, e),
                             self.G[lhs]['__total__'])

    def decode(self, lhs, pt):
        if not lhs or lhs not in self.G:
            return '', 0, TERMINAL
        assert lhs in self.G
        return self.G.get_rhs(lhs, pt)

    def encode_pw(self, pw):
        code_g = [] #convert2group(0,1) for i in \
                    #  range(hny_config.PASSWORD_LENGTH)])
        T, W, U = self.G.parse_pw(pw)
        rule = ','.join(T)
        code_g.append(self.encode('G', rule))
        for i,p in enumerate(T):
            t=self.encode(p, W[i])
            if t==-1: 
                print "Sorry boss! iQuit!"
                return Encode_spcl(pw, grammar)
            code_g.append( t )
            # TODO - make it better with Capitalize, AllCaps, L33t etc
            if W[i] != U[i]:
                for c,d in zip(W[i], U[i]):
                    code_g.append(self.encode(c,d))
        # padd the encoding with some random numbers to make it 
        # of size PASSWORD_LENGTH 
        extra = hny_config.PASSWORD_LENGTH - len(code_g);
        code_g.extend([convert2group(0,1) for x in range(extra)])
        return code_g
    
    def decode_pw(self, P):
        assert len(P) == hny_config.PASSWORD_LENGTH
        iterp = iter(P)
        plaintext = '';
        stack = ['G']
        while stack:
            head = stack.pop()
            print head, stack, plaintext
            rhs, freq, typ = self.decode(head, iterp.next())
            if typ == NONTERMINAL:
                arr = rhs.split(',')
                arr.reverse()
                stack.extend(arr)
            else:
                plaintext += rhs
        return plaintext

    def __eq__(self, o_dte):
        return self.G == o_dte.G


class DTE_large(DTE):
    """
    encodes a rule
    """
    def __init__(self, grammar=None):
        self.term_files = {}
        self.g_struc = GrammarStructure()
        for k, f in self.g_struc.getTermFiles().items():
            sys.path.append(hny_config.GRAMMAR_DIR)
            X = __import__('%s' % f)
            self.term_files[k] = {
                'trie' : marisa_trie.Trie().load(hny_config.GRAMMAR_DIR+f+'.tri'),
                'arr' : eval("X.%s"%k),
                'trie_fl' : hny_config.GRAMMAR_DIR+f+'.tri'
                }
        super(DTE_large, self).__init__(grammar)

    @staticmethod
    def word2prob( w, T, A ):       
        i = T.key_id(unicode(w))
        if i<0:
            print "Could not find {w} in the trie.".format(**locals())
            exit(0)
        else:
            S = sum( A[:i] )
            t = random.randint( S, S+A[i] )
            totalC = A[-1]
            return convert2group(t, totalC)

    @staticmethod    
    def prob2word( p, T, A):
        i = getIndex(p, A)
        w = T.restore_key(i)
        return w, A[i]

    def encode(self, lhs, rhs):
        if  lhs in self.term_files:
            return self.word2prob(rhs, self.term_files[lhs]['trie'],
                                 self.term_files[lhs]['arr'] )
        return super(DTE_large, self).encode(lhs, rhs) 

    def decode(self, lhs, pt):
        if  lhs in self.term_files:
            w, f = self.prob2word(pt, 
                                 self.term_files[lhs]['trie'],
                                 self.term_files[lhs]['arr'])
            return w, f, TERMINAL
        return super(DTE_large, self).decode(lhs, pt) 
        
    def get_freq(self, lhs, rhs):
        if lhs in self.term_files:
            try:
                i = self.term_files[lhs]['trie'].key_id(unicode(rhs))
            except KeyError:
                print "ERROR! Could not find '%s' in '%s'. Go debug!!"\
                    % ( rhs, self.term_files[lhs]['trie_fl'] )
                print self.term_files[lhs]['trie'].keys()
                exit(0)
                return -1
            if i<0:
                print "KeyError in get_freq1:", lhs, rhs
                return -1, -1
            return self.term_files[lhs]['arr'][i]
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
                if rhs != '__total__' and f[1] == NONTERMINAL:
                    for x in rhs.split(','):
                        if x not in done and x not in t_set and \
                                x not in stack:
                            t_set.append(x)
            t_set.reverse()
            stack.extend(t_set)
            n = len(rule_dict.keys())-1
            code_g.append(vd.encode_vault_size(n))
            print "RuleSizeEncoding:", head, n
            assert n == vd.decode_vault_size(code_g[-1])
            #print "Encoding", '\n'.join(['%s --> %s' %(head, r) 
            #                             for r in rule_dict.keys()])
            code_g.extend([self.encode(head, r) 
                           for r in rule_dict.keys()
                           if r != '__total__'])
        extra = hny_config.HONEY_VAULT_GRAMMAR_SIZE - len(code_g);
        code_g.extend([convert2group(0,1) for x in range(extra)])     
        return code_g

    def decode_grammar(self, P):
        g=Grammar(Empty=True)
        vd = VaultDistribution()
        iterp = iter(P)
        stack = ['G']
        done = []
        while stack:
            head = stack.pop()
            assert head not in done
            done.append(head)
            p = iterp.next()
            n = vd.decode_vault_size(p)
            print "RuleSizeDecoding:", head, n
            t_set = []
            for x in range(n):
                rhs, freq, typ = self.decode(head, iterp.next())
                # print "Decoding:", head, '==>', rhs
                g.addRule_lite(head, rhs, freq, typ, True)
                if rhs != '__totoal__' and typ == NONTERMINAL:
                    for x in rhs.split(','):
                        if x not in done and x not in t_set and \
                                x not in stack:
                            t_set.append(x)
            t_set.reverse()
            stack.extend(t_set)
        g.update_total_freq()
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


def Encode(m, scanner, dte ):
    P, W, U = scanner.tokenize(m, True)
    E = []
    print P, W, U;
    # Grammar is of the form: S -> L3D2Y1 | L3Y2D5 | L5D2
    t = dte.encode('G', ','.join([ str(x) for x in P]) )
    print 't:', t; 
    if t==-1: # use the default .* parsing rule..:P 
        print "Encode Spcl"
        exit (0) 
        return Encode_spcl( m, grammar );
    else: E.append( t );

    for i,p in enumerate(P):
        t=dte.encode(p, W[i])
        if t==-1: 
            return Encode_spcl(m, grammar)
        E.append( t )
        continue;
        if W[i].isalpha():
            for w,u in zip(W[i], U[i]):
                try:
                    t = getVal(grammar[w], u) 
                    if t!=-1: E.append( t )
                    else: 
                        print 'here2', w, u
                        return Encode_spcl(m, grammar)
                except KeyError:
                    print 'here3', w, u
                    return Encode_spcl(m, grammar)
    print "Actual:", E;
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend( [ convert2group(0,1) for x in range(extra) ] )
    c_struct = struct.pack('%sI' % len(E), *E )
    return c_struct


# c is of the form set of numbers... 
# probabilities, CDF
def Decode ( c, dte ):
    # c is io.BytesIO
    t = len( c );
    P = struct.unpack('%sI'%(t/4), c)
    #if ( len(P) != PASSWORD_LENGTH ):
        # print "Encryptino is not of correct length"
        
    plaintext = '';
    #queue = deque(['S']);
    stack = ['G']
    for p in P:
        try:
            g = dte.decode( stack.pop(), p )
        except IndexError: 
            #print plaintext, g
            #print "empty queue"
            break;
        if g[2] == NONTERMINAL: 
            arr = g[0].split(',')
            arr.reverse()
            stack.extend(arr)
        elif g[2] == NONTERMINAL+1:
            arr = list(g[0])
            arr.reverse()
            stack.extend(arr)
        else: # zero, terminal add 
            plaintext += g[0]
        print g, stack, plaintext
    return plaintext

    
        
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
    print "After Decoding:", m
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
