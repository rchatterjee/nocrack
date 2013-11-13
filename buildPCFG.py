#!/usr/bin/python

import sys, os
import bz2, re
from mangle import *
import marisa_trie
EPSILON = '|_|'
GRAMMAR_R=0

#
# ['S']  -> [('S2,S',1,20), ('L4,S',1,34),.... (EPSILON, 12332]
# ['S2'] -> [('!!',0,12),('$%',0,23), .. 12312]
# ['L1'] -> [('o',0,13),('a',0,67),....235]
# ['D3'] -> [('132',0,32),('123',0,23)....3567]
#
#          ||
#          ||
#         \  /
#          \/
#
# After the preprocessing is done this grammar is to converted,s.t.
# Every rule, will contain the the CDF instead of probability
#

"""
gives what type of character it is.
Letter: L, Capitalized: C
Digit: D, Symbol: S
ManglingRule: M
"""
regex = r'([a-z]+)|([0-9]+)|(\W+)'
def whatchar( c ):
    if c.isalpha(): return 'L';
    if c.isdigit(): return 'D';
    else: return 'Y'

inversemap=dict();
def insertInGrammar ( grammar, pRule, w ):
#        for x in grammar[pRule][0]:
#            if x.add(w): grammar[pRule][1] += 1; return;
    if not w.strip(): return;
    try:
        if grammar[pRule][0][inversemap[w]].add(w):
            grammar[pRule][1] += 1; return;
    except:
        try:
            grammar[pRule][0].append( NonTerminal(w) )
            inversemap[w] = len(grammar[pRule][0])-1
            grammar[pRule][1] += 1;
    # print pRule, w
        except:
            grammar[pRule] = [[NonTerminal(w)], 1]
            inversemap[w] = 0;
        
mangler = Mangle(); # Not used still
def findPattern( w, withMangling=False ):
    P,W,T = [],[],[]
    i,j = 0, 0
    W = [ sym for list_match in re.findall(regex, w.lower()) 
          for sym in list_match if sym ]
    P = [ "%s%d" % ( whatchar(x[0]), len(x)) for x in W ]
    # TODO - HOWWWWWW?????!!!! Confused
    # Mstr = '';
    # Cinfo = getCapitalizeInfo ( w );
    # if withMangling: 
    #     M,w = mangler.mangle(w);
    #     if not M : return P
    #     Mstr = 'M' + '-'.join([str(x) for x in M])

    # if Cinfo>0 : 
    #     CinfoStr = 'C%d' % Cinfo;
    #     T.append( NonTerminal(CinfoStr) );
    # if withMangling: T.append( NonTerminal(Mstr) )

    return P,W,T;

def pushWordIntoGrammar( grammar, w, isMangling=False ) :
    P,W,T = findPattern ( w, isMangling )
    # print ','.join([str(x) for x in P]),'~~', W,'~~', 
    # print  ','.join([str(x) for x in T])
    # insertInGrammar ( 'S', ','.join([str(x) for x in P]) )
    if GRAMMAR_R: # grammar is of the form S -> L1S | L2S | D3S .. etc | EPSILON
        for p in P:
            insertInGrammar( grammar, 'S', str(p)+',S')
        insertInGrammar ( grammar, 'S', EPSILON );
    else:
        insertInGrammar ( grammar, 'S', ','.join([ str(x) for x in P ]) )
        
    for p,w in zip(P,W):
        insertInGrammar(grammar, str(p), w);
    
    for t in T:
        insertInGrammar ( grammar, 'T', t )
    if isMangling : pushWordIntoGrammar ( w, True )


# P = [ NonTerminal(p[0], int(p[1]) ) for p in x.split(',')]
# for p in P:
#     print p;

def convertToCDF(grammar):
    for rule in grammar:
        c = 0;
        # print rule,
        for nt in grammar[rule][0]:
            nt.add(nt.type_is, c+nt.length);
            c = nt.length
        grammar[rule][1] = c

def pushRandomCombinationIntoGrammar( grammar ) :
    """
    This is to support parsing all possible passwords. 
    Artifical rules like, S -> L,S | D,S | Y,S
    and L -> a|b|c|d..
    D -> 1|3|4 etc
    """
    insertInGrammar( grammar, 'S', 'L1,S');
    insertInGrammar( grammar, 'S', 'D1,S');
    insertInGrammar( grammar, 'S', 'Y1,S');

    for c in 'abcdefghijklmnopqrstuvwxyz':     
        insertInGrammar( grammar, 'L1', c )
    for d in '0123456789' :                    
        insertInGrammar( grammar, 'D1', d )
    for s in '!@#$%^&*()_-+=[{}]|\'";:<,.>?/': 
        insertInGrammar( grammar, 'Y1', s )

                         
    
def buildGrammar(password_dict):
    grammar  = dict()
    grammar['S'] = ([],0) 
    # start node ( [(w1,n1),(w2,n2),(w3,n3)..], n )
    f=bz2.BZ2File(password_dict)
    for line in f.readlines():
        line = line.strip()
        pushWordIntoGrammar( grammar, line ) 
    f.close();
    pushRandomCombinationIntoGrammar( grammar );
    return grammar

def writePCFG( grammar, filename ):
    with open(filename, 'w') as f:
        for rule in grammar:
            # S:L1,D3|123:L3,Y3|2134:65635
            # L1:a|2:b|4:...
            f.write( '%s:%s:%d\n' % 
                     ( rule, 
                       ':'.join(['%s|%d' %(x.type_is, x.length) 
                                 for x in grammar[rule][0]]), 
                       grammar[rule][1]) )


def NonT( s ):
    # type_is | length
    if s.count('|') > 1:
        x = s.split('|');
        try:
            return NonTerminal(''.join(x[-1]), x[-1])
        except:
            print "~~~><%s>" % s; 
    x = s.split('|')
    try:
        return NonTerminal(x[0], int(x[1]));
    except:
        print "~~><%s>" % s; 

def readPCFG( filename ):
    grammar = dict()
    with open(filename, 'r') as f:
        for l in f.readlines():
            x = l.strip().split(':')
            grammar[x[0]] = [[NonT(y) for y in x[1:-1] if y], int(x[-1])]
    return grammar
def main():
    if len (sys.argv) < 2 : 
        print 'Command: %s <password_dict>' % sys.argv[0]
        exit(-1)
        
    password_dict = sys.argv[1];
    grammar = buildGrammar(password_dict)
    # print [ str(w) for w in grammar['S'][0]]
    Words = [ w.type_is for rule in grammar for w in grammar[rule][0] if rule != 'S']
    TrieSets = marisa_trie.Trie(Words);
    convertToCDF(grammar);
    #for g in grammar:
    #    print g, ':', str(' '.join([str(x) for x in grammar[g][0]])), grammar[g][1]
    import pickle
    if GRAMMAR_R:
        pickle.dump( grammar, open('data/grammar_r.hny', 'wb'))
    else:
        #pickle.dump( grammar, open('data/grammar.hny', 'wb'))
        writePCFG( grammar, 'data/grammar.hny' )

    TrieSets.save( 'data/trie.hny');

if __name__ == "__main__":
    main();
    
