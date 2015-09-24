from helper import open_, convert2group, getIndex, print_err
from Crypto.Random import random 
import os, sys, json
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault_config import GRAMMAR_DIR
from collections import OrderedDict

MAX_ALLOWED = 20 # per rule
VAULT_DIST_FILE = GRAMMAR_DIR+'vault_dist.cfg'

class VaultDistribution:
    def __init__(self):
        self.G = json.load(open_(VAULT_DIST_FILE),
                           object_pairs_hook=OrderedDict)
        # Add dummy entries for new non-terminals now
        # TODO: Learn them by vault analysis. 
        # uniformly distribute these values between 1 and 30
        use_ful = 5
        for k in ['W', 'D', 'Y', 'R', 'T']:
            self.G[k] = OrderedDict(zip((str(x) for x in range(MAX_ALLOWED+1)[1:]), 
                                 [100]*use_ful + [5]*(MAX_ALLOWED-use_ful)))

        for k,v in self.G.items():
            v['__total__'] = sum(v.values())

        #print json.dumps(self.G, indent=2)

    def encode_vault_size(self, lhs, n):
        v = self.G.get(lhs, {})
        n = str(n)
        try:
            i = v.keys().index(n)
            x = sum(v.values()[:i])
            y = x + v.values()[i]
        except ValueError:
            return convert2group(0, v['__total__'])
        return convert2group(random.randint(x, y-1),
                             v['__total__'])

    def decode_vault_size(self, lhs, cf):
        assert not lhs.startswith('L')
        cf %= self.G.get(lhs, {'__total__': 0})['__total__']
        if cf == 0:
            print_err("Grammar of size 0!!!!\nI don't think the decryption will "
                      "be right after this. I am sorry.", lhs, cf)
        i = getIndex(cf, self.G[lhs].values())
        return i+1


if __name__ == '__main__':
    vd = VaultDistribution()
    #t = vd.decode_vault_size('D', vd.encode_vault_size('D', 0))
    X = vd.encode_vault_size('D', 3)
    t = vd.decode_vault_size('D', X)
    assert t == 3, str((X, t))
    #assert t == 0, "'D' with size 0, decoded to Wrong value {}".format(t)
    
    for i in range(25):
        k = random.randint(1,MAX_ALLOWED)
        lhs = random.choice(vd.G.keys())
        e = vd.encode_vault_size(lhs, k)
        assert vd.decode_vault_size(lhs, e) == k, "VaultSizeDecodingError:"\
            " Expecting: {} for (lhs: {}, e:{}), but decoded to: {}".format(k, lhs, e, vd.decode_vault_size(lhs, e))
        
