import os, sys
#from pytrie import SortedStringTrie as trie
from marisa_trie import Trie
import bz2

dir_path = '/home/rahul/Desktop/Acads/AdvanceComputerSecurity/downloads.skullsecurity.org/passwords/'

def loadTrie( fname ):
    global trie
    try:
        fname = fname + "_trie.hny"
        trie.load( fname )
    except(IOError):
        f = bz2.BZ2File( dir_path + sys.argv[1]);
        words = [ w.strip() for w in f.readlines() ]
        trie = Trie(words);
        trie.save(fname);
#T = trie(zip(words, range(len(words))))

# input : c1c2c3....cn
# output: [w1 w2 w3] or []
def break_into_words( w, trie ):
    n = len(w);
    if n==1 : return [w];
    if n==0 : return [];
    Wlist = []
    prefix = trie.prefixes( unicode(w) );
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

def bSearch( arr, s, e, x ):
    print arr[s:e+1], s, e, x
    if arr[s] > x: print "ERROR: Zero"; return s
    if arr[e] < x: print "ERROR: End"; return e;
    if arr[(s+e)/2] > x: return bSearch( arr, s, (s+e)/2, x )
    else: return bSearch( arr, (s+e)/2+1, e, x);

if __name__ == "__main__":
    arr = [0, 8, 15, 10000, 12000, 12323, 13423]
    print bSearch( arr, 0, len(arr)-1, 00 );

    # if len(sys.argv)<2: 
    #     print "%s <filename>" % sys.argv[0]
    #     exit();
        
    #     fname = sys.argv[1].split('.')[0]
    #     trie = Trie( );
    #loadTrie(fname)
    #print break_into_words(u'iloveu', trie);
# trie.save ( "%s_trie.hny" % fname )
    
