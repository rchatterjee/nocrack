#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import sys, os, math, struct, bz2, resource
from io import BytesIO
from Crypto.Random import random
import marisa_trie
from collections import deque
from scanner_helper import *
from scanner import *

# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p


class DTE:
    """
    encodes a rule
    """
    def __init__(self):
        self.g_struc = GrammarStructure()
        self.term_files = {}
        for k, f in self.g_struc.getTermFiles().items():
            sys.path.append(GRAMMAR_DIR)
            X = __import__('%s' % f)
            self.term_files[k] = {
                'trie' : marisa_trie.Trie().load(GRAMMAR_DIR+f+'.tri'),
                'arr' : eval("X.%s"%k),
                'trie_fl' : GRAMMAR_DIR+f+'.tri'
                }
        self.G = Grammar()
        self.G.load(GRAMMAR_DIR+'/grammar.cfg')


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
            return t + random.randint(0, (4294967295-t)/totalC) * totalC

    @staticmethod    
    def prob2word( p, T, A, freq_also = False ):
        i = getIndex(p, A)
        w = T.restore_key(i)
        return w if not freq_also else w, A[i]

    def encode(self, lhs, rhs):
        if  lhs in self.term_files:
            return DTE.word2prob(rhs, self.term_files[lhs]['trie'],
                             self.term_files[lhs]['arr'] )
        assert lhs in self.G
        rule_set = self.G[lhs][0]
        freq_list= [ x[0] for x in self.G[lhs][1] ] # [[freq, type(N/T)]]
        i = rule_set.index(rhs)
        assert i>=0
        S = sum( freq_list[:i] )
        t = random.randint( S, S+freq_list[i] )
        totalC = self.G[lhs][2]
        return convert2group(t, totalC)
    
    def decode(self, lhs, prob, freq_also=False):
        if  lhs in self.term_files:
            w, f = DTE.prob2word(prob, 
                                 self.term_files[lhs]['trie'],
                                 self.term_files[lhs]['arr'], 
                                 freq_also )
            if freq_also:
                return w, f, TERMINAL
            else: 
                return w, TERMINAL
        
        assert lhs in self.G
        rule_set = self.G[lhs][0]
        # print "KEYERROR Test:", self.G[lhs]
        freq_list= [x[0] for x in self.G[lhs][1]]
        freq_list.append( self.G[lhs][2] )
        i = getIndex(prob, freq_list)
        if freq_also:
            return rule_set[i], freq_list[i], self.G[lhs][1][i][1]
        else:
            return rule_set[i], self.G[lhs][1][i][1]

    def get_freq(self, lhs, rhs):
        if lhs in self.term_files:
            try:
                i = self.term_files[lhs]['trie'].key_id(unicode(rhs))
            except KeyError:
                print "ERROR! Could not find '%s' in '%s'. Go debug!!" % ( rhs, self.term_files[lhs]['trie_fl'] )
                return [-1, -1]
            if i<0: 
                print "KeyError in get_freq1:", lhs, rhs
                return -1, -1
            return [self.term_files[lhs]['arr'][i], TERMINAL]
        try:
            i = self.G[lhs][0].index(rhs)
            return self.G[lhs][1][i]
        except ValueError: 
            print "ValueError in get_freq -- %s is not in %s:" % \
                (rhs,self.G[lhs][0])
            return -1, -1
    
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


def Encode( m, scanner, dte ):
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
