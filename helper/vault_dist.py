from helper import convert2group, getIndex
from Crypto.Random import random 

class VaultDistribution:
    VAULT_SIZE_TO_FREQ = [ 1, 6, 10, 13, 8, 9, 
                           12, 15, 12, 3, 2, 1] + \
                           [1, 1, 1, 1, 1] * 10
    def __init__(self):
        for i, a in enumerate(self.VAULT_SIZE_TO_FREQ):
            self.VAULT_SIZE_TO_FREQ[i] = a*5
            
        self.total = sum(self.VAULT_SIZE_TO_FREQ)
        self.VAULT_SIZE_TO_FREQ.append(self.total)

    def encode_vault_size(self, n ):
        # n = min(len(self.VAULT_SIZE_TO_FREQ)-1, n)
        x = sum(self.VAULT_SIZE_TO_FREQ[:n])
        y = x + self.VAULT_SIZE_TO_FREQ[n]
        return convert2group(random.randint(x, y-1),
                             self.total)

    def decode_vault_size(self, cf):
        i = getIndex(cf, self.VAULT_SIZE_TO_FREQ)
        return i%30


if __name__ == '__main__':
    vd = VaultDistribution()
    assert vd.decode_vault_size(vd.encode_vault_size(0)) == 0
    for i in range(25):
        k = random.randint(0,len(vd.VAULT_SIZE_TO_FREQ))
        print i, k
        assert vd.decode_vault_size(vd.encode_vault_size(k)) == k
        
