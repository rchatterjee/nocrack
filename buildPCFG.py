#!/usr/bin/python

import sys, os
import bz2

if len (sys.argv) < 1 : 
    print 'Command: %s <password_dict>' % sys.argv[0]
    exit(0)


password_dict = sys.argv[1];
grammar=dict()



"""
gives what type of character it is.
Letter: L, Capitalized: C
Digit: D, Symbol: S
ManglingRule: M
"""
def whatChar( c ):
    if c.isalpha(): return 'L';
    if c.isdigit(): return 'D';
    else: return 'S'

grammar['S'] = ([],0) # start node ( [(w1,n1),(w2,n2),(w3,n3)..], n )
def insertInGrammar ( pRule, w ):
    try: 
        found = False;
        for x in grammar[pRule][0]:
            if x.add(w): grammar[pRule][1] += 1; return;
        grammar[pRule][0].append( NonTerminal(w) )
        grammar[pRule][1] += 1;         
    except:
        grammar[pRule] = ([NonTerminal(w)], 1)
        
mangler = Mangle();
def findPattern( w, withMangling=False ):
    P,W,T = [],[],[]
    i,j = 0, 0
    Mstr = '';
    Cinfo = getCapitalizeInfo ( w );
    if withMangling: 
        M,w = mangler.mangle(w);
        if not M : return P
        Mstr = 'M' + '-'.join([str(x) for x in M])
    for c in w:
        t = whatChar(c)
        j+=1;
        if not P: 
            P.append( NonTerminal(t) );
        else:
            if not P[-1].add(t):
                W.append( w[i:j].lower() );
                i=j;
                # if  #TODO
                P.append( NonTerminal(t) )
    if Cinfo>0 : 
        CinfoStr = 'C%d' % Cinfo;
        T.append( NonTerminal(CinfoStr) );
    if withMangling: T.append( NonTerminal(Mstr) )

    return P,W,T;

def pushWordIntoGrammar( w, isMangling=False ) :
    P,W,T = findPattern ( w, isMangling )
    insertInGrammar ( 'S', ','.join([str(x) for x in P]) )
    for p,w in zip(P,W):
        insertInGrammar(p, w);
    for t in T:
        insertInGrammar ( 'T', t )
    if !isMangling : pushWordIntoGrammar ( w, True )
        
def getNT ( w ):
    return [','.join([str(x) for x in findPattern( w, False )]),
            ','.join([str(x) for x in findPattern( w, True  )])]


# P = [ NonTerminal(p[0], int(p[1]) ) for p in x.split(',')]
# for p in P:
#     print p;
    
f=bz2.BZ2File(password_dict)
for line in f.readlines():
    line = line.strip()
    #if len(line)>1 : #dictionary with count
    #    print "currently not supported..:P"
    # else:
    x = getNT( line )
    try:
        grammar[x].append(line)
    except: 
        grammar[x] = [line];
f.close();

for g in grammar:
    print g, ':', grammar[g]

