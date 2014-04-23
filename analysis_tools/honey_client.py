import os, sys
import urllib, urllib2
import binascii
from Crypto.Hash import SHA256
from urlparse import urlparse
from publicsuffix import PublicSuffixList
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault.honey_vault import HoneyVault

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


# ---------------- Client command line functions ------------------
def get_pass( *args ):
    if len(args)<2:
        return h_string
    mp = args[0]
    hv = HoneyVault(VAULT_FILE, mp)
    return hv.get_password([get_exact_domain(args[1])])


def histogram_generate( numsamples ):
    rnd_source = Random.new()
    mp = rnd_source.read(256)
    hv = HoneyVault(VAULT_FILE, mp)
    return hv.get_password([get_exact_domain('test')])

if __name__ == "__main__":
    if len(sys.argv)>1:
        histogram_generate( sys.argv[1] ) 
    else:
        print "Please indicate the number of samples to perform"
