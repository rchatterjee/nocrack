#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import sys, os, math
from io import BytesIO
import struct
from mingle import *
#from loadDic import break_into_words
import random, marisa_trie
import bz2 

PASSWORD_LENGTH = 50
DEBUG = 1 # 1 S --> we are not getting combined rule like L3,D4 
NONTERMINAL = 1
# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

# m is any passwrd

# def break_into_words( w, trie ):
#     n = len(w);
#     if n==1 : return [w];
#     if n==0 : return [];
#     Wlist = []
#     try: prefix = trie.prefixes( unicode(w) );
#     except: return []
#     # print prefix
#     prefix.reverse()
#     if not prefix: return [];
#     if prefix[0] == w: return [w];
#     for p in prefix:
#         if not p or len(p) == 0:
#             print p; return [];
#         W = break_into_words( w[len(p):], trie )
#         if W:
#             Wlist.append(p)
#             Wlist.extend(W);
#             break;
#     return Wlist;

def loadDicAndTrie(dFile, tFile) :
    grammar = readPCFG( dFile );
    trie    = marisa_trie.Trie().load( tFile )
    if grammar['S'][0][-1][1] == grammar['S'][1]:
        convertToPDF(grammar)
    return grammar, trie


def getVal( arr, val ):
    # print val, '---\n', [str(s) for s in arr[0]];
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
        return t + random.randint(0, (4294967295-t)/totalC) * totalC
    return t

def getIndex( arr, s, e, x ):
    # print arr[s:e+1], s, e, x
    if arr[s] > x: return s
    if arr[e] < x: return e;
    if arr[(s+e)/2] > x: return getIndex( arr, s, (s+e)/2, x )
    else: return getIndex( arr, (s+e)/2+1, e, x);


# TODO: every array in grammar rule should have start with a dummy entry('',0,0) and prob zero!!
def getGenerationAtRule( rule, prob, grammar):
    # returns: ('IloveYou',0,420)
    d = [0]
    d.extend([x[2] for x in grammar[rule]])
    for i in xrange(1, len(d)):
        d[i] += d[i-1];
    prob = prob % d[-1]
    t = getIndex ( d, 0, len(d)-1, prob ) - 1;
    return grammar[rule][t]

def Encode_spcl( m, grammar ):
    print "Special Encoding::::", m
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
        E.extend( [ random.randint(0, 4294967295) for x in range(extra) ] )
    return E;


def Encode( m, tokenizer, grammar ):
    P, W, U = tokenizer.tokenize(m, True)
    E = []    
    print P, W, U;
    # Grammar is of the form: S -> L3D2Y1 | L3Y2D5 | L5D2
    t = getVal( grammar['S'], ','.join([ str(x) for x in P]) )
    print 't:', t; 
    if t==-1: # use the default .* parsing rule..:P 
        return Encode_spcl( m, grammar );
    else: E.append( t );

    for i,p in enumerate(P):
        t=getVal(grammar[p], W[i])
        if t==-1: 
            print "here1", p, W[i]
            return Encode_spcl(m, grammar)
        E.append( t )
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
    # print "Actual:", E;
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend( [ random.randint(0, 4294967295) for x in range(extra) ] )
    return E

# c is of the form set of numbers... 
# probabilities, CDF
from collections import deque
def Decode ( c, grammar ):
    # c is io.BytesIO
    t = len( c );
    P = struct.unpack('%sI'%(t/4), c)
    #if ( len(P) != PASSWORD_LENGTH ):
        # print "Encryptino is not of correct length"
        
    plaintext = '';
    #queue = deque(['S']);
    stack = ['S']
    for p in P:
        #print stack, p
        try:
            g = getGenerationAtRule( stack.pop(), p, grammar )
        except: 
            #print plaintext, g
            #print "empty queue"
            break;
        if g[1] == NONTERMINAL: 
            arr = g[0].split(',')
            arr.reverse()
            stack.extend(arr)
        elif g[1] == NONTERMINAL+1:
            arr = list(g[0])
            arr.reverse()
            stack.extend(arr)
        else: # zero, terminal add 
            plaintext += g[0]
    return plaintext

    
        
import resource
def main():
    base_dictionary, tweak_fl, passwd_dictionary, out_grmmar_fl, out_trie_fl = readConfigFile(sys.argv[1])
    
    _trie    = marisa_trie.Trie().load( out_trie_fl )
    _tweaker = Tweaker(tweak_fl)
    T = Tokenizer(tweaker=_tweaker, trie=_trie)
    #print T.tokenize('P@$$w0rd', True)
    #exit(0)
    G = Grammar(tokenizer=T)
    G.load(out_grmmar_fl)
    print "Resource:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
    #p='(NH4)2Cr2O7' # sys.stdin.readline().strip()
    p=u'iloveyou69'
    c = Encode(p, T, G.G);
    print "Encoding:", c
    c_struct = struct.pack('%sI' % len(c), *c )
    m = Decode(c_struct, G.G);
    print "After Decoding:", m
    #     if PASSWORD_LENGTH>0:
    for s in range(10000):
        E = []
        E.extend( [ random.randint(0, 4294967295) for x in range(PASSWORD_LENGTH) ] )
        c_struct = struct.pack('%sI' % len(E), *E )
        m = Decode(c_struct, G.G);
        print s, ":", m



if __name__ == "__main__":
    main();
