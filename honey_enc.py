#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.

"""

import sys, os
from io import BytesIO
import struct
from buildPCFG import whatchar, readPCFG, getfilenames
from buildPCFG import EPSILON, GRAMMAR_R
#from loadDic import break_into_words
import random, marisa_trie
import bz2 

PASSWORD_LENGTH = 16
DEBUG = 1 # 1 S --> we are not getting combined rule like L3,D4 
NONTERMINAL = 1
# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

# m is any passwrd

def break_into_words( w, trie ):
    n = len(w);
    if n==1 : return [w];
    if n==0 : return [];
    Wlist = []
    try: prefix = trie.prefixes( unicode(w) );
    except: return []
    # print prefix
    prefix.reverse()
    if not prefix: return [];
    if prefix[0] == w: return [w];
    for p in prefix:
        if not p or len(p) == 0:
            print p; return [];
        W = break_into_words( w[len(p):], trie )
        if W:
            Wlist.append(p)
            Wlist.extend(W);
            break;
    return Wlist;

def loadDicAndTrie(dFile, tFile) :
    #grammar = pickle.load(open(dFile, 'rb'))
    grammar = readPCFG( dFile );
    trie    = marisa_trie.Trie().load( tFile )
    return grammar, trie


def getVal( arr, val ):
    # print val, '---\n', [str(s) for s in arr[0]];
    for i,x in enumerate(arr[0]):
        if x[0] == val:
            if i==0: a = 0;
            else: a = arr[0][i-1][1];
            t = random.randint( a, x[1]-1 )
            return t;
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
    d = [0]
    d.extend([x[1] for x in grammar[rule][0]])
    #print [str(x) for x in grammar[rule][0]], round(prob*grammar[rule][1])
    t = getIndex ( d, 0, len(d)-1, round(prob*grammar[rule][1])) - 1;
    return grammar[rule][0][t]

def Encode_spcl( m, trie, grammar ):
    print "Special Encoding::::"
    W = m # break_into_words(m, trie)
    P = ['%s%d' % (whatchar(w), len(w)) for w in W ]
    E = [];
    for w,p in zip(W[:-1], P[:-1]):
        E.append( float(getVal( grammar['S'], p+',S'))/
                  grammar['S'][1] )
        E.append( float(getVal( grammar[ p ], w ))/
                  grammar[ p ][1]);
    E.append( float(getVal( grammar[ 'S' ], P[-1]))/
              grammar['S'][1])
    E.append( float(getVal( grammar[P[-1]], W[-1]))/
              grammar[P[-1]][1]);
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend( [ random.random() for x in range(extra) ] )
    return E;

def Encode( m, trie, grammar ):
    W = break_into_words(m, trie)
    P = ['%s%d' % (whatchar(w), len(w)) for w in W ]
    E = []
    if GRAMMAR_R:
        W.append( EPSILON )
        for p in P:
            t = getVal(grammar['S'], p+',S');
            if t==-1: print "Not found", p; raise
            # TODO: it should never occur.. but will check
            else: E.append( float(t)/grammar['S'][1] );
    else: # Grammar is of the form: S -> L3D2Y1 | L3Y2D5 | L5D2
        t = getVal( grammar['S'], ','.join([ str(x) for x in P]) )
        if t==-1: # use the default .* parsing rule..:P 
            return ''; 
            # return Encode_spcl( m, trie, grammar );
        else: E.append( float(t)/grammar['S'][1] );
        
    # print P
    for p,w in zip(P,W):
        t=getVal(grammar[p], w)
        E.append( float(t)/grammar[p][1] )
    if GRAMMAR_R:
        E.append( float(getVal(grammar['S'], EPSILON ))/grammar['S'][1] )
    
    # print "Actual:", E;
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend( [ random.random() for x in range(extra) ] )
    return E

# c is of the form set of numbers... 
# probabilities, CDF
from collections import deque
def Decode ( c, grammar ):
    # c is io.BytesIO
    t = len( c );
    P = struct.unpack('%sf'%(t/4), c)
    if ( len(P) != PASSWORD_LENGTH ):
        print "Encryptino is not of correct length"

    plaintext = '';
    queue = deque(['S']);
    for p in P:
        try:
            g = getGenerationAtRule( queue.popleft(), p, grammar )
        except: 
            # print "empty queue"
            break;
        if g[2] == NONTERMINAL: 
            queue.extend(g[0].split(','))
            # TODO
        #elif g[1] == 2: # mangling rule;
        #    print " I don't know"
        else: # zero, terminal add 
            if GRAMMAR_R and g[0] == EPSILON: break
            plaintext += g[0]
            #print "Decode:", g, '<%s>'%plaintext; # break;
    #print queue, p, '<=>', plaintext
    return plaintext

def writePasswords ( p ):
    # writes the encoded passwords.. 
    f = open("password_vault.hny", 'w')
    
        
import resource
def main():
    grammar_flname, trie_flname = "data/grammar.hny.bz2", "data/trie.hny"
    if len (sys.argv) > 1 : 
            grammar_flname, trie_flname = getfilenames(sys.argv[1])
    else:
        print 'Command: %s <password_dict_name>' % sys.argv[0]
        print 'Taking defaults,', grammar_flname, trie_flname
        
    if GRAMMAR_R:
        grammar, trie = loadDicAndTrie( 'data/grammar_r.hny', 'data/trie.hny');
    else:
        grammar, trie = loadDicAndTrie( grammar_flname, trie_flname );   
    print "Resource:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
    # testEncoding(grammar, trie); return;
    p='rahulc12' # sys.stdin.readline().strip()
    c = Encode(p, trie, grammar);
    print "Encoding:", c
    c_struct = struct.pack('%sf' % len(c), *c )
    m = Decode(c_struct, grammar);
    print "After Decoding:", m

if __name__ == "__main__":
    main();
