from helper.helper import (open_, convert2group, 
                           getIndex, print_err)
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
        for k,v in self.G.items():
            v['__total__'] = sum(v.values())

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
        cf %= self.G[lhs]['__total__']
        if cf == 0 and lhs == 'G':
            print_err("Grammar of size 0!!!!", lhs, cf)
            return cf
        i = getIndex(cf, self.G[lhs].values())
        return i+1


if __name__ == '__main__':
    vd = VaultDistribution()
    assert vd.decode_vault_size('D', vd.encode_vault_size('D', 0)) == 0
    for i in range(25):
        k = random.randint(0,MAX_ALLOWED)
        lhs = random.choice(vd.G.keys())
        e = vd.encode_vault_size(lhs, k)
        assert vd.decode_vault_size(lhs, e) == k
        
