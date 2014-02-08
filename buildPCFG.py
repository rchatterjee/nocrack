from mingle  import *

#
# ['S']  -> [('S2,S',1,20), ('L4,S',1,34),...]
# ['S2'] -> [('!!',0,12),('$%',0,23), .. ]
# ['L1'] -> [('o',0,13),('a',0,67),....]
# ['D3'] -> [('132',0,32),('123',0,23)....]
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
###################### --NEW VERSION-- ###################################

def buildPCFG(config_fl):
    base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(config_fl)
    if os.path.exists(out_trie_fl) and os.path.exists(out_grammar_fl):
        print "The grammar(%s) and trie(%s) already exist! Not recreating. remove to force." % ( out_grammar_fl, out_trie_fl)
        return;
    T = Tokenizer(base_dictionary, tweak_fl)
    G = Grammar(tokenizer=T)
    # resource track
    resource_tracker = 5240;
    for n, line in enumerate(open_(passwd_dictionary)):
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
            continue;
            w,c = ' '.join(line), 1
        try: w.decode('ascii')
        except: continue; # not ascii hence return
        if ( c < MIN_COUNT ): print "Word frequency dropped to %d for %s" % (c, w), n;  break; # Carefull!!!
        G.insert(w, c )
    # TODO
    #push_DotStar_IntoGrammar( grammar );
    G.save(bz2.BZ2File(out_grammar_fl, 'w'))
    marisa_trie.Trie(Grammar.inversemap.keys()).save(out_trie_fl)
    return G

if __name__ == "__main__":
    G = buildPCFG(sys.argv[1])
    print G
#print T.unmangleWord(u'mike@1302')
#print T.tokenize(u'Comput3rS3cret@1302', True)

################## --OLD VERSION-- ###############################
def insertInGrammar_modify( grammar, pRule, w, count, isNonT=NONTERMINAL):
    cnt = 0;
    if pRule not in grammar: return;
    s = grammar[pRule][0]
    for j,i in enumerate(s):
        if i[0] == w and i[2] == isNonT:
            i[1] += count
            if i[1]<=0: s.remove(i);
            cnt = i[1]
            # print grammar[pRule][0][j], cnt
            grammar[pRule][1] += count;
            if grammar[pRule][1] <= 0:
                # print "Removing Rule:", pRule;
                del grammar[pRule]
            break;
    # print "Removing:", pRule, w, count, cnt
    return cnt;

inversemap=dict();
def ModifyGrammar( grammar, w, count ):
    P, W, T = findPattern( w )
    insertInGrammar_modify ( grammar, 'S', ','.join([ str(x) for x in P ]), count, NONTERMINAL ) # NonTerminal
    
    for p,w in zip(P,W):
        if len(w) > 30: return;
        insertInGrammar_modify(grammar, str(p), w, count, 1-NONTERMINAL ); # Terminal

def insertInGrammar ( grammar, pRule, w, count=1, isNonT=0, isCDF=False ):
    if not w.strip(): return;
    if len(w)>30: return;
    try:
        s = grammar[pRule][0][inversemap[w]]
        assert s[0]==w and s[2] == isNonT;
        s[1] += count
        grammar[pRule][1] += count;
        #if __name__ != "__main__": 
         #   print ">> Inserted:", pRule, w, count, s[1]-count
        return s[1]-count;
    except:
        try:
            grammar[pRule][0].append( [w, count, isNonT] )
            inversemap[w] = len(grammar[pRule][0])-1
            grammar[pRule][1] += count;
        except:
            grammar[pRule] = [[[w, count, isNonT]], count]
            inversemap[w] = 0;
    #if __name__ != "__main__":
        # print "Inserted:", pRule, w, count, 0
    return 0;

def pushWordIntoGrammar( grammar, w, count = 1, isMangling=False ) :
    if len(w) > 50: return

    P,W,T = findPattern ( w, isMangling )
    insertInGrammar ( grammar, 'S', ','.join([ str(x) for x in P ]), count, NONTERMINAL ) # NonTerminal
    
    for p,w in zip(P,W):
        if len(w) > 30: return;
        insertInGrammar(grammar, str(p), w, count, 1-NONTERMINAL ); # Terminal
        
    for t in T:
        insertInGrammar ( grammar, 'T', t )
    if isMangling : pushWordIntoGrammar ( w, True )

# def convertToPDF(grammar):
#     for rule in grammar:
#         c = 0;
#         # print rule,
#         for nt in grammar[rule][0]:
#             c, nt[1] = nt[1], nt[1]-c;

def pruneGrammar(grammar, cnt=3):
    for rule in grammar:
        if grammar[rule][1] < cnt:
            del grammar[rule];

# def convertToCDF(grammar):
#     for rule in grammar:
#         c = 0;
#         # print rule,
#         for nt in grammar[rule][0]:
#             nt[1] += c;
#             c = nt[1]
#         grammar[rule][1] = c

def push_DotStar_IntoGrammar( grammar ) :
    """
    This is to support parsing all possible passwords. 
    Artifical rules like, S -> L,S | D,S | Y,S
    and L -> a|b|c|d..
    D -> 1|3|4 etc
    """
    insertInGrammar( grammar, 'S', 'L1,S', MIN_COUNT-1, NONTERMINAL);
    insertInGrammar( grammar, 'S', 'D1,S', MIN_COUNT-1, NONTERMINAL);
    insertInGrammar( grammar, 'S', 'Y1,S', MIN_COUNT-1, NONTERMINAL);

    for c in 'abcdefghijklmnopqrstuvwxyz':     
        insertInGrammar( grammar, 'L1', c, MIN_COUNT-1, 1-NONTERMINAL )
    for d in '0123456789' :                    
        insertInGrammar( grammar, 'D1', d, MIN_COUNT-1, 1-NONTERMINAL )
    for s in '!@#$%^&*()_-+=[{}]|\'";:<,.>?/': 
        insertInGrammar( grammar, 'Y1', s, MIN_COUNT-1, 1-NONTERMINAL )
    # mangling_rule={'a':'@', 's':'$', 'o':'0', 'i':'!'}
    
                   
def buildGrammar(password_dict):
    grammar  = dict()
    grammar['S'] = ([],0) 
    # start node ( [(w1,n1),(w2,n2),(w3,n3)..], n )
    f=open_(password_dict)

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
            continue;
            w,c = ' '.join(line), 1
        try: w.decode('ascii')
        except: continue; # not ascii hence return
        if ( c < MIN_COUNT ): print "Word frequency dropped to %d for %s" % (c, w), n;  break; # Carefull!!!
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
        # json.dump(grammar, f, indent=2, separators=(',',':'))
        json.dump(grammar,f);

def readPCFG( filename, prune=False ):
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
        # return;
    password_dict = sys.argv[1];
    grammar = buildGrammar(password_dict)
    # convertToCDF(grammar);
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

    
# if __name__ == "__main__":
#     main();
    
