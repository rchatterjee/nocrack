from honey_enc import *

def testEncoding ( grammar, trie ):
    logF = open('logfile.txt', 'w')    
    logF.write(
"""
# Dictionary: "<%s>"
# File List : testdiclist.txt
# top 1000 and randomly chosen 1000 from the rest and last 1000.
""" % sys.argv[1]
        )
    files = ['../PasswordDictionary/passwords/' + s.strip() 
             for s in open('testdiclist.txt').readlines() if not s[0]=='#']
    for fname in files:
        logF.write( "\n--------- %s ---------- :\n" % fname)
        state, failed_count, total_tested, c = 0, 0, 0, 0
        with bz2.BZ2File(fname) as f:
            for l in f:
                l = l.strip().split();
                if len(l) > 1 and l[0].isdigit:
                    l = ' '.join(l[1:]);
                else:
                    l = ' '.join(l);
                if not l: continue;
                if c>1000:
                    if state == 2 : break
                    else: state += 1;
                    c=0;
                if state is 0 or state is 2 or random.randint(0,1000)>90:
                    c += 1;
                    total_tested += 1
                    if not Encode(l, trie, grammar): 
                        failed_count += 1; 
                        logF.write( l + "\n" )
        logF.write( ">>>>>Total: %d\n>>>>>Failed: %d\n" % ( total_tested, failed_count) )
    logF.close();


def testRandomDecoding(grammar):
 #   print "Testing....:"
    x = [ random.random() for x in range(PASSWORD_LENGTH) ]
    c = struct.pack('%sf' % len(x), *x)
    print Decode(c, grammar)

def comp( x, y ):
    return x[1] < y[1]

def convertToPDF( grammar ):
    for rule in grammar:
        c = 0;
        for nt in grammar[rule][0]:
            c, nt[1] = nt[1], nt[1] - c;
        sorted( grammar[rule][0], comp, reverse=True )

word_arr = [0]*20
prob_lim = 1e-4;
def dfs(grammar, r, i, prob):
    global word_arr
    word_arr[i] = r
    for x in grammar[r][0]:
        if r=='S': print x
        tprob = float(x[1]) * prob / grammar[r][1]
        if tprob < prob_lim: break;
        if x[2] == 1:
            for j in range(i,20): word_arr[j]=False;
            for j,y in enumerate(x[0].split(',')): word_arr[i+j] = y;
            j = i;
            for y in word_arr[i:]:
                if y: dfs(grammar, y, j, tprob)
                j += 1
        else:
            word_arr[i] = x[0]
            if word_arr[i+1] == 0: print '~~>', ''.join(word_arr[:i+1]), " ==> ", prob

def testGenerate( grammar ):
    convertToPDF( grammar )
    print dfs(grammar, 'S', 0, 1);

    

if __name__ == "__main__":
    grammar_flname, trie_flname = "data/grammar.hny.bz2", "data/trie.hny"
    if len (sys.argv) > 1 : 
            grammar_flname, trie_flname = getfilenames(sys.argv[1])
    else:
        print 'Command: %s <password_dict_name>' % sys.argv[0]
        print 'Taking defaults,', grammar_flname, trie_flname
    grammar, trie = loadDicAndTrie( grammar_flname, trie_flname );   
    print "Resource:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    testGenerate(grammar);
