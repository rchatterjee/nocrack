#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.

"""

import sys, os
from io import BytesIO
import struct
from buildPCFG import whatchar, EPSILON
#from loadDic import break_into_words
import random, marisa_trie
import pickle
# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

# m is any passwrd

def break_into_words( w, trie ):
    n = len(w);
    if n==1 : return [w];
    if n==0 : return [];
    Wlist = []
    prefix = trie.prefixes( unicode(w) );
    # print prefix
    prefix.reverse()
    if not prefix: return [];
    if prefix[0] == w: return [w];
    for p in prefix:
        W = break_into_words( w[len(p):] )
        if W:
            Wlist.append(p)
            Wlist.extend(W);
            break;
    return Wlist;

def loadDicAndTrie(dFile, tFile) :
    grammar = pickle.load(open(dFile, 'rb'))
    trie    = marisa_trie.Trie().load( tFile )
    return grammar, trie

def Encode( m, trie, grammar ):
    W = break_into_words(m, trie)
    W.append( EPSILON )
    # print W
    P = ['%s%d' % (whatchar(w), len(w)) for w in W[:-1]]
    E = []
    for p in P:
        t = getVal(grammar['S'], p+',S');
        if t==-1:
            print "Not found", p
            raise
            # TODO: it should never occur.. but will check
        else:
            E.append(float(t)/grammar['S'][1]);
    for p,w in zip(P,W):
        t=getVal(grammar[p], w)
        E.append( float(t)/grammar[p][1] )
    E.append( float(getVal(grammar['S'], EPSILON ))/grammar['S'][1] )
    return E

def getVal( arr, val ):
    #print val, '---\n', [str(s) for s in arr[0]];
    for i,x in enumerate(arr[0]):
        if x.type_is == val:
            if i==0: a = 0;
            else: a = arr[0][i-1].length;
            return random.randint( a, x.length )
    return -1

def getIndex( arr, s, e, x ):
    # print arr[s:e+1], s, e, x
    if arr[s] > x: return s
    if arr[e] < x: return e;
    if arr[(s+e)/2] > x: return getIndex( arr, s, (s+e)/2, x )
    else: return getIndex( arr, (s+e)/2+1, e, x);
# TODO: every array in grammar rule should have start with a dummy entry('',0,0) and prob zero!!


def getGenerationAtRule( rule, prob, grammar):
    # returns: ('IloveYou',0,420)
    print rule, prob
    d = [0]
    d.extend([x.length for x in grammar[rule][0]])
    t = getIndex ( d, 0, len(d)-1, prob*grammar[rule][1]) - 1;
    return grammar[rule][0][t]

def isNonT( rule ):
    return rule.isupper() 
# c is of the form set of numbers... 
# probabilities, CDF
from collections import deque
def Decode ( c, grammar ):
    # c is io.BytesIO
    t = len( c );
    P = struct.unpack('%sf'%(t/4), c)
    plaintext = '';
    queue = deque(['S']);
    for p in P:
        g = getGenerationAtRule( queue.popleft(), p, grammar ).type_is
        print g
        if isNonT(g):
            queue.extend(g.split(','))
        # TODO
        #elif g[1] == 2: # mangling rule;
        #    print " I don't know"
        else: # zero, terminal add 
            if g == EPSILON: break
            plaintext += g
    print queue, '<>', plaintext
    return plaintext

def writePasswords ( p ):
    # writes the encoded passwords.. 
    f = open("password_vault.hny", 'w')

def testRandomDecoding(grammar):
    print "Testing....:"
    x = [ random.random() for x in range(10) ]
    c = struct.pack('%sf' % len(x), *x)
    print Decode(c, grammar)

    
def main():
    grammar, trie = loadDicAndTrie( 'data/grammar.hny', 'data/trie.hny' );
    p = 'iloveyou' # sys.stdin.readline().strip()
    c = Encode(p, trie, grammar);
    c_struct = struct.pack('%sf' % len(c), *c )
    m = Decode(c_struct, grammar);
    print "Encoding:", c
    print "After Decoding:", m
    testRandomDecoding( grammar );
if __name__ == "__main__":
    main();
