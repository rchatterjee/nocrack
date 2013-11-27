#!/usr/bin/python

import sys, os
import bz2, re
import marisa_trie, json

# For checking memory usage
import resource

EPSILON = '|_|'
GRAMMAR_R=0
NONTERMINAL = 1
MEMLIMMIT = 1024 # 1024 MB, 1GB

from os.path import (expanduser, basename)
home = expanduser("~");

def file_type(filename):
    magic_dict = {
        "\x1f\x8b\x08": "gz",
        "\x42\x5a\x68": "bz2",
        "\x50\x4b\x03\x04": "zip"
        }
    max_len = max(len(x) for x in magic_dict)
    
    with open(filename) as f:
        file_start = f.read(max_len)
    for magic, filetype in magic_dict.items():
        if file_start.startswith(magic):
            return filetype
    return "no match"

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
regex = r'([A-Za-z]+)|([0-9]+)|(\W+)'
def whatchar( c ):
    if c.isalpha(): return 'L';
    if c.isdigit(): return 'D';
    else: return 'Y'

inversemap=dict();
def insertInGrammar ( grammar, pRule, w, count=1, isNonT=0 ):
    if not w.strip(): return;
    # if ( w == "L1,S" ): print pRule, w, count, isNonT
    try:
        s = grammar[pRule][0][inversemap[w]]
        assert s[0]==w and s[2] == isNonT;
        s[1] += count
        grammar[pRule][1] += count; 
        return;
    except:
        try:
            grammar[pRule][0].append( [w, count, isNonT] )
            inversemap[w] = len(grammar[pRule][0])-1
            grammar[pRule][1] += count;
        except:
            grammar[pRule] = [[[w, count, isNonT]], 1]
            inversemap[w] = 0;
        
#mangler = Mangle(); # Not used still
def findPattern( w, withMangling=False ):
    P,W,T = [],[],[]
    i,j = 0, 0
    W = [ sym for list_match in re.findall(regex, w) 
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
    #     T.append( [CinfoStr) );
    # if withMangling: T.append( [Mstr) )

    return P,W,T;

def pushWordIntoGrammar( grammar, w, count = 1, isMangling=False ) :
    P,W,T = findPattern ( w, isMangling )
    if GRAMMAR_R: # grammar is of the form S -> L1S | L2S | D3S .. etc | EPSILON
        for p in P:
            insertInGrammar( grammar, 'S', str(p)+',S', count, NONTERMINAL ) # NonTerminal
        insertInGrammar ( grammar, 'S', EPSILON );
    else:
        insertInGrammar ( grammar, 'S', ','.join([ str(x) for x in P ]), count, NONTERMINAL ) # NonTerminal
        
    for p,w in zip(P,W):
        insertInGrammar(grammar, str(p), w, count, 1-NONTERMINAL ); # Terminal
        
    # same like, iloveyou -> 0 | IloveU | ILoveYou etc..
    # 0 => iloveyou
    #if w.islower(): insertInGrammar( grammar, w, 0 )
    #else: insertInGrammar ( grammar, w.lower(), w )
    for t in T:
        insertInGrammar ( grammar, 'T', t )
    if isMangling : pushWordIntoGrammar ( w, True )


# P = [ [p[0], int(p[1]) ) for p in x.split(',')]
# for p in P:
#     print p;
def convertToPDF(grammar):
    for rule in grammar:
        c = 0;
        # print rule,
        for nt in grammar[rule][0]:
            c, nt[1] = nt[1], nt[1]-c;


def convertToCDF(grammar):
    for rule in grammar:
        c = 0;
        # print rule,
        for nt in grammar[rule][0]:
            nt[1] += c;
            c = nt[1]
        grammar[rule][1] = c

def push_DotStar_IntoGrammar( grammar ) :
    """
    This is to support parsing all possible passwords. 
    Artifical rules like, S -> L,S | D,S | Y,S
    and L -> a|b|c|d..
    D -> 1|3|4 etc
    """
    insertInGrammar( grammar, 'S', 'L1,S', 1, NONTERMINAL);
    insertInGrammar( grammar, 'S', 'D1,S', 1, NONTERMINAL);
    insertInGrammar( grammar, 'S', 'Y1,S', 1, NONTERMINAL);

    for c in 'abcdefghijklmnopqrstuvwxyz':     
        insertInGrammar( grammar, 'L1', c, 1, 1-NONTERMINAL )
    for d in '0123456789' :                    
        insertInGrammar( grammar, 'D1', d, 1, 1-NONTERMINAL )
    for s in '!@#$%^&*()_-+=[{}]|\'";:<,.>?/': 
        insertInGrammar( grammar, 'Y1', s, 1, 1-NONTERMINAL )
    # mangling_rule={'a':'@', 's':'$', 'o':'0', 'i':'!'}
    
                   
def buildGrammar(password_dict):
    grammar  = dict()
    grammar['S'] = ([],0) 
    # start node ( [(w1,n1),(w2,n2),(w3,n3)..], n )
    if file_type(password_dict) == "bz2":
        f=bz2.BZ2File(password_dict)
    else:
        f = open(password_dict);
    reinsert_words = []
    # resource track
    resource_tracker = 10240;
    for n,line in enumerate(f):
        if n>resource_tracker:
            r = MEMLIMMIT*1024 - resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
            print "Memory Usage:", (MEMLIMMIT - r/1024.0), "Lineno:", n;
            if (r < 0 ):
                print """
Hitting the memory limmit of 1GB,
please increase the limit or use smaller data set.
Lines processed, %d
""" % n
                break;
            resource_tracker += r/10+100;
        # if n%1000==0: print n;
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w,c = ' '.join(line[1:]), int(line[0])
        else:
            w,c = ' '.join(line), 1
        try: w.decode('ascii')
        except: continue; # not ascii hence return

        if w.islower() :
            pushWordIntoGrammar( grammar, w, c )
        else:
            reinsert_words.append( w+'<>'+str(c) )
    f.close();
    push_DotStar_IntoGrammar( grammar );
    if reinsert_words:
        for w in reinsert_words:
            w = w.split('<>')
            c = int(w[-1])
            w = '<>'.join(w[:-1])
            pushWordIntoGrammar ( grammar, w, c);            
    return grammar

def writePCFG( grammar, filename ):
    with bz2.BZ2File(filename, 'wb') as f:
        print "Num grammar keys:", len(grammar.keys())
        json.dump(grammar, f, indent=2, separators=(',',':'))

def readPCFG( filename ):
    with bz2.BZ2File(filename, 'rb') as f:
        return json.load(f);

def getfilenames( fname_origin ):
    fname_origin = basename(fname_origin);
    fname_origin = fname_origin.replace(".txt.bz2", '')
    return "data/grammar_%s.hny.bz2" % fname_origin, "data/trie_%s.hny.bz2" % fname_origin, 

def main():
    if len (sys.argv) < 2 : 
        print 'Command: %s <password_dict>' % sys.argv[0]
        exit(-1)
    grammar_flname, trie_flname = getfilenames( sys.argv[1] )
    if os.path.exists(grammar_flname) and os.path.exists(trie_flname):
        sys.stderr.write( "---->'%s' and '%s' already exists!\nIf you want to force, remove those files first.\nExisting!!\n" % (grammar_flname, trie_flname) )
        return;
    password_dict = sys.argv[1];
    grammar = buildGrammar(password_dict)
    convertToCDF(grammar);
    if GRAMMAR_R:
        import pickle
        pickle.dump( grammar, open(grammar_flname, 'wb'))
    else:
        #pickle.dump( grammar, open('data/grammar.hny', 'wb'))
        writePCFG( grammar, grammar_flname )
    marisa_trie.Trie(inversemap.keys()).save( trie_flname );
    
def main_modify() :
    g = readPCFG('data/grammar_json.hny.bz2');
    with bz2.BZ2File('data/grammar_json.hny.bz2', 'wb') as f:
        f.write("#!/usr/bin/python\n\ngrammar=");
        json.dump(g, f, indent=2, separators=(',',':'))
    
if __name__ == "__main__":
    main();
    
