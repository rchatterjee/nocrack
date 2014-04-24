import os, sys
import urllib, urllib2
import binascii
from Crypto.Hash import SHA256
from Crypto import Random
from urlparse import urlparse
from publicsuffix import PublicSuffixList
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault.honey_vault import HoneyVault
from scanner.scanner import Scanner, Grammar, TrainedGrammar
from honeyvault_config import GRAMMAR_DIR, MIN_COUNT
from helper.helper import open_

HONEY_SERVER_URL = "http://localhost:5000/"
VAULT_FILE  = 'static/vault.db'
STATIC_DOMAIN_HASH_LIST = 'static_domain_hashes.txt'
b2a_base64 = lambda x: binascii.b2a_base64(x)[:-1]

MIN_COUNT = 20
MIN_CUTOFF_FREQ_PRECENT = 1e-6

def create_request(sub_url, data):
    return urllib2.Request(HONEY_SERVER_URL+sub_url,
                           urllib.urlencode(data))

def err_write( *args ):
    sys.stderr.write(' '.join([str(a) for a in args]))
    sys.stderr.write('\n')


def get_exact_domain( url ):
    u = urlparse(url)
    h = u.hostname
    if not h:
        h = url
    psl = PublicSuffixList()
    return psl.get_public_suffix(h)

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]

def get_prob( grammar, lhs, rhs ):
    try:
        x1, x2 = grammar.get_freq_range(lhs, rhs)
    except ValueError:
        return 0
    t = x2-x1
    if t>0:
        return float(t)/grammar.total_freq(lhs)
    else:
        return 0
    
prod = lambda arr: arr[0] if len(arr)==1 else arr[0] * prod(arr[1:])

def get_pw_prob( pw, G=None, prnt = False):
    if not G:
        prnt = True
        G = TrainedGrammar()
        G.load(GRAMMAR_DIR+'/grammar.cfg')
    T, W, U = G.parse_pw(pw)
    if prnt: print T, W, U
    rule = ','.join(T)
    code_g = [get_prob(G, 'G', rule)]
    for i,p in enumerate(T):
        code_g.append( get_prob(G, p, W[i]) )
        if W[i] != U[i]:
            for c,d in zip(W[i], U[i]):
                code_g.append(get_prob(G, c, d))
    return prod(code_g)
    return  '%s,%d' % (p, prod(code_g))

# ---------------- Client command line functions ------------------
def get_pass( *args ):
    if len(args)<2:
        return h_string
    mp = args[0]
    hv = HoneyVault(VAULT_FILE, mp)
    return hv.get_password([get_exact_domain(args[1])])

def histogram_generate_rc( pw_file ):
    from scipy import stats
    G = TrainedGrammar()
    G.load(GRAMMAR_DIR+'/grammar.cfg')
    S = {}
    tF, tG = 0, 0
    for line in open_(pw_file):
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w, c = ' '.join(line[1:]), int(line[0])
        else:
            continue
        try:
            w.decode('ascii')
        except UnicodeDecodeError:
            continue    # not ascii hence return
        if len(w)>11: continue
        #if c < MIN_COUNT : break
        if (c / float(tF+1.0)) < MIN_CUTOFF_FREQ_PRECENT: 
            break
        # print w
        S[w] = [c, get_pw_prob(w, G)]
        tF += S[w][0]
        tG += S[w][1]
    for k,x in S.items():
        x[0] = float(x[0])/tF
        x[1] = float(x[1])/tG
        print "%s,%g,%g" %(k, x[0], x[1])
    from math import sqrt
    err_write(tF, tG, sqrt(2.0/len(S)))

def plot_hist( file_name ):
    o, e = [0.0], [0.0]
    for l in open_(file_name):
        l = l.strip().split(',')
        if len(l)>3:
            l = ','.join(l[:-2]), l[-2], l[-1]
        o.append(float(l[1]))
        e.append(float(l[2]))
    t = sorted(zip(o,e), key=lambda x: x[0], reverse=True)
    o, e = [0.0], [0.0]
    m = 0.0
    for x in t:
        o.append(o[-1]+x[0])
        e.append(e[-1]+x[1])
        if abs(o[-1]-e[-1])>m:
            m = abs(o[-1]-e[-1])
    import numpy, pylab
    pylab.plot(o)
    pylab.plot(e)
    img_file = ''.join(file_name.split('.')[:-1]) + '.png'
    pylab.savefig(img_file)
    print m

def histogram_generate( numsamples ):
    rnd_source = Random.new()
    histogram = {}
    for i in range(0,int(numsamples)-1):
        mp = rnd_source.read(256)
        hv = HoneyVault(VAULT_FILE, mp)
        pw = hv.get_password([get_exact_domain('test')])['test']
        #print pw
        histogram[pw] = histogram.get(pw, 0) + 1
    return histogram
    
if __name__ == "__main__":
    if len(sys.argv)>1:
        if sys.argv[1] == '-plot':
            plot_hist( sys.argv[2] )
        elif sys.argv[1] == '-hist':
            histogram_generate_rc( sys.argv[2] )
        elif sys.argv[1] == '-prob':
            print get_pw_prob(sys.argv[2])
        else:
            print """
commands: -plot, -hist, -prob
"""
        #print histogram_generate( sys.argv[1] ) 
    else:
        print "Please indicate the number of samples to perform"
