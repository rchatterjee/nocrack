#!/usr/bin/python
import sys, marisa_trie, random, json
from array import array
import re, os

N = 1E6
def create_trie():
    """
This is a helper function to create a file containing the key_id
of every Word in the trie word list.
    """
    if len(sys.argv)<2:
        print "USAGE: %s dictionary_fl trie_fl [out_fl]"
        exit(0)
    dictionary_fl = sys.argv[1]
    D = {}
    for i, line in enumerate(open(dictionary_fl)):
        if i>N: break;
        l = line.strip().split()
        c, w = int(l[0]), ' '.join(l[1:])
        try: w.decode('ascii')
        except UnicodeDecodeError: continue
        D[w] = c
    T = marisa_trie.Trie(D.keys())
    T.save('g_dict.tri')
    n = len(D.keys())+1
    A = [0 for i in xrange(n)]
    s = 0
    for w,c in D.items():
        i = T.key_id(unicode(w))
        try: 
            A[i] =  c
            s += c
        except IndexError: 
            print i, w
    A[-1] = s
    with open('g_dict.py', 'w') as f:
        f.write('A = [')
        f.write(',\n'.join(['%d' % x for x in A]))
        f.write(']\n')

def build_dawg( file_name, out_fl = None ):
    """
    takes a file name as input and converts that into a dawg.DAWG
    """
    from helper import open_
    import dawg
    with open_(file_name) as f:
        L = ( l.strip() for l in f )
        D = dawg.DAWG(L)
        if not out_fl:
            f, e = os.path.splitext(file_name)
            out_fl = f + ".dawg"
        D.save(out_fl)



from g_dict import A
T = marisa_trie.Trie().load('g_dict.tri')

def word2prob( w ):       
    i = T.key_id(unicode(w))
    if i<0:
        print "Could not find {w} in the trie.".format(**locals())
    else:
        S = sum( A[:i] )
        t = random.randint( S, S+A[i] )
        totalC = A[-1]
        return t + random.randint(0, (4294967295-t)/totalC) * totalC


def prob2word( p ):
    p %= A[-1]
    i = 0;
    for i, v in enumerate(A):
        p -= v;
        if p<0: break
    print i
    w = T.restore_key(i)
    return w




if __name__ == '__main__':
    if len(sys.argv) <2: 
        print "Not enough argument!"
    if sys.argv[1] == '--dawg':
        if len(sys.argv)==3:
            build_dawg(sys.argv[2])
        if len(sys.argv)==4:
            build_dawg(sys.argv[2], sys.argv[3])
            
    elif sys.argv[1] == '--grammarstructure':
        g = GrammarStructure()
        print g.to_json()
    # create_trie()
    # p = 'password'
    # n = word2prob(p)
    # print 'word2prob:', p, '-->', n
    # p1 = prob2word(n)
    # print 'prob2word:', n, '-->', p1
    
    
