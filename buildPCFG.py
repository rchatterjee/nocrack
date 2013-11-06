#!/usr/bin/python

import sys, os
import bz2, re
from mangle import *
import marisa_trie
EPSILON = '|_|'


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

def insertInGrammar ( grammar, pRule, w ):
    try:
        for x in grammar[pRule][0]:
            if x.add(w): grammar[pRule][1] += 1; return;
        grammar[pRule][0].append( NonTerminal(w) )
        grammar[pRule][1] += 1;
    # print pRule, w
    except:
        grammar[pRule] = [[NonTerminal(w)], 1]
        
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
    for p in P:
        insertInGrammar( grammar, 'S', str(p)+',S')
    insertInGrammar ( grammar, 'S', EPSILON );
    for p,w in zip(P,W):
        insertInGrammar(grammar, str(p), w);
    
    for t in T:
        insertInGrammar ( grammar, 'T', t )
    if isMangling : pushWordIntoGrammar ( w, True )

def getNT ( w ):
    return [','.join([str(x) for x in findPattern( w, False )]),
            ','.join([str(x) for x in findPattern( w, True  )])]


# P = [ NonTerminal(p[0], int(p[1]) ) for p in x.split(',')]
# for p in P:
#     print p;

def convertToCDF(grammar):
    for rule in grammar:
        c = 0;
        # print rule,
        for nt in grammar[rule][0]:
            nt.add(nt.type_is, c);
            c = nt.length

def buildGrammar(password_dict):
    grammar  = dict()
    grammar['S'] = ([],0) 
    # start node ( [(w1,n1),(w2,n2),(w3,n3)..], n )
    f=bz2.BZ2File(password_dict)
    for line in f.readlines():
        line = line.strip()
        pushWordIntoGrammar( grammar, line ) 
    f.close();
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
    pickle.dump( grammar, open('data/grammar.hny', 'wb'))
    TrieSets.save( 'data/trie.hny');

if __name__ == "__main__":
    main();
    
