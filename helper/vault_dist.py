from helper import convert2group, getIndex
from Crypto.Random import random 

class VaultDistribution:
    def __init__(self):
        self.vs2f = [1, 6, 10, 13, 8, 9, 
                     12, 15, 12, 3, 2, 1]
        self.vs2f.extend([1]*50)
        for i, a in enumerate(self.vs2f):
            self.vs2f[i] = a*5
            
        self.total = sum(self.vs2f)
        self.vs2f.append(self.total)

    def encode_vault_size(self, n ):
        # n = min(len(self.VAULT_SIZE_TO_FREQ)-1, n)
        x = sum(self.vs2f[:n])
        y = x + self.vs2f[n]
        # print __name__, 'encoding:', x, y
        return convert2group(random.randint(x, y-1),
                             self.total)

    def decode_vault_size(self, cf):
        i = getIndex(cf, self.vs2f)
        # print __name__, 'decoding:', cf % self.total, i
        return i%50


if __name__ == '__main__':
    vd = VaultDistribution()
    assert vd.decode_vault_size(vd.encode_vault_size(0)) == 0
    for i in range(25):
        k = random.randint(0,len(vd.vs2f))
        print i, k
        assert vd.decode_vault_size(vd.encode_vault_size(k)) == k
        
