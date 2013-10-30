import os, sys
#from pytrie import SortedStringTrie as trie
from marisa_trie import Trie
import bz2

dir_path = '/home/rahul/Desktop/Acads/AdvanceComputerSecurity/downloads.skullsecurity.org/passwords/'

if len(sys.argv)<2: 
    print "%s <filename>" % sys.argv[0]
    exit();

fname = sys.argv[1].split('.')[0]
trie = Trie( );

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

def break_into_words( w ):
    n = len(w);
    Wlist = []
    while(n>0):
        prefix = trie.prefixes( unicode(w) );
        x = max (prefix); 
        Wlist.append( x )
        if ( not Wlist[-1] ): break; 
        t = len(Wlist[-1])
        n-=t
        w = w[t:]
    return Wlist;

loadTrie(fname)
print break_into_words(u'iloveu');
# trie.save ( "%s_trie.hny" % fname )

