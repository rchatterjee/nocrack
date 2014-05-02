import os, sys, json, math
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault.honey_enc import DTE, DTE_large, DTE_random
import honeyvault_config as hny_config
from lexer.pcfg import TrainedGrammar 
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random
import copy, struct
from helper.helper import convert2group, open_, getIndex, print_err
from vaultanalysis.vault_dist import VaultDistribution
from collections import OrderedDict, defaultdict
import pylab

rnd_source = Random.new()
MAX_INT = hny_config.MAX_INT

#--------------------------------------------------------------------------------
def decoy_vault(pw_encodings=None, s=6, n=100):
    pcfg = DTE_large()
    g_s = hny_config.HONEY_VAULT_GRAMMAR_SIZE
    pw_s = hny_config.PASSWORD_LENGTH
    db = []
    if pw_encodings:
        s = len(pw_encodings)
    else:
        buf = struct.unpack('!%sI' % (pw_s*s), rnd_source.read(pw_s * s * 4))
        pw_encodings = [buf[i:i+pw_s] 
                        for i in range(0,pw_s*s, pw_s)]
    assert len(pw_encodings) == s

    for i in range(n):
        H = struct.unpack('!%sI' % g_s, rnd_source.read(g_s*4))
        dte = pcfg.decode_grammar(H)
        pw_set = [dte.decode_pw(p)
                  for p in pw_encodings]
        db.append((len(db)+1, pw_set))
        if i%10==0:
            print_err( i )
    return dict(db)

def decoy_pw(n=100):
    pass

def pcfg_analysis(nt):
    G = TrainedGrammar()
    A = defaultdict(int)
    #print json.dumps(G[nt], indent=2)
    for w,f in G[nt].items():
        if w != '__total__':
            A[len(w)] += f
    print json.dumps(A, indent=2)
    cut = G[nt]['__total__']/len(A.values())
    #B = sorted(A.items(), key=lambda x: x[1])
    #print '\n'.join(str(x) for x in B)
    # X = [x[0] for x in B]
    # Y = [x[1] for x in B]
    # for i,x in enumerate(Y):
    #     Y[i] += Y[i-1] if i>0 \
    #         else 0
    cls = 1
    s = 0
    for k,y in A.items():
        print '(%6d, %2d, %2d)' %(y, k, cls)
        s += y
        if s> cut: 
            cls += 1
            s = 0
    #pylab.plot(A.keys(), A.values(), label='W')
    pylab.plot(A.values(), label='cdf')
    pylab.legend()
    pylab.savefig('plot.png')


if __name__=="__main__":
    if len(sys.argv)<2: 
        exit(0)
    if sys.argv[1]=='-decoy':
        n = int(sys.argv[2]) if len(sys.argv)>2 else 100
        print json.dumps(decoy_vault(n=n), indent=2)
    elif sys.argv[1]=='-grammar':
        pcfg_analysis(sys.argv[2])
