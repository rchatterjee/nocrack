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
from honeyvault_config import GRAMMAR_DIR
 
HONEY_SERVER_URL = "http://localhost:5000/"
VAULT_FILE  = 'static/vault.db'
STATIC_DOMAIN_HASH_LIST = 'static_domain_hashes.txt'
b2a_base64 = lambda x: binascii.b2a_base64(x)[:-1]

def create_request(sub_url, data):
    return urllib2.Request(HONEY_SERVER_URL+sub_url,
                           urllib.urlencode(data))

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
    x1, x2 = grammar.get_freq_range(lhs, rhs)
    t = x2-x1
    if t>0:
        return float(t)/grammar.total_freq(lhs)
    else:
        return 0
    
prod = lambda arr: arr[0] if len(arr)==1 else arr[0] * prod(arr[1:])

def get_pw_prob( pw ):
    G = TrainedGrammar()
    G.load(GRAMMAR_DIR+'/grammar.cfg')
    T, W, U = G.parse_pw(pw)
    rule = ','.join(T)
    code_g = [get_prob(G, 'G', rule)]
    for i,p in enumerate(T):
        code_g.append( get_prob(G, p, W[i]) )
        if W[i] != U[i]:
            for c,d in zip(W[i], U[i]):
                code_g.append(get_prob(G, c, d))
    print code_g
    return prod(code_g)

# ---------------- Client command line functions ------------------
def get_pass( *args ):
    if len(args)<2:
        return h_string
    mp = args[0]
    hv = HoneyVault(VAULT_FILE, mp)
    return hv.get_password([get_exact_domain(args[1])])


def histogram_generate( numsamples ):
    rnd_source = Random.new()
    histogram = {}
    for i in range(0,int(numsamples)-1):
        mp = rnd_source.read(256)
        hv = HoneyVault(VAULT_FILE, mp)
        pw = hv.get_password([get_exact_domain('test')])['test']
        print pw
        histogram[pw] = histogram.get(pw, 0) + 1
    return histogram
    
if __name__ == "__main__":
    if len(sys.argv)>1:
        print get_pw_prob( sys.argv[1] )
        #print histogram_generate( sys.argv[1] ) 
    else:
        print "Please indicate the number of samples to perform"
