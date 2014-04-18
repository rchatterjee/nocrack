#!/afs/cs.wisc.edu/u/r/c/rchat/honeyencryption/honeyvenv/bin/python


import os, sys
import string
from Crypto.Random import random
A = string.ascii_uppercase

fact_map = [1, 2, 6, 24, 120, 720, 
          # 1, 2, 3, 4,  5,   6,
            5040, 40320, 362880, 3628800, 39916800,
          # 7,    8,     9,      10,      11
            479001600
          # 12
            ]

def encode2number( s ):
    sorted_s = sorted(s)
    n = len(s)
    code = 0
    for i, ch in enumerate(s):
        l = sorted_s.index(ch)
        code += l*fact_map[n-i-2]
        del sorted_s[l]
    return code

def decode2string(num, s):
    sorted_s = sorted(s)
    n = len(s)
    st = ['' for i in range(n)]
    for i in range(n):
        x = num/fact_map[n-i-2]
        num -= x*fact_map[n-i-2]
        st[i] = sorted_s[x]
        del sorted_s[x]
    return ''.join(st)

class DTE_random:
    punct = "!@#%&*_+=~"
    All = string.ascii_letters + string.digits + punct
    must_set = [punct, string.digits, string.ascii_uppercase, string.ascii_lowercase]
    
    def generate_and_encode_password(self, size=10):
        N = [random.randint(0,4294967295) for i in range(size)]
        P = [s[N[i]%len(s)] for i, s in enumerate(self.must_set)]
        P.extend(self.All[n%len(self.All)] for n in N[len(self.must_set):])
        n = random.randint(0, fact_map[size-1])
        password = decode2string(n, P)
        N.append(n)
        return password, N

    def decode_password(self, N):
        P = [s[N[i]%len(s)] for i, s in enumerate(self.must_set)]
        P.extend(self.All[n%len(self.All)] for n in N[len(self.must_set):-1])
        n = N[-1]
        password = decode2string(n, P)
        return password
        
        
    def generate_random_password(self, size=10 ):
        """
        Generates random password of given size
        it ensures -
        1 uppercase
        1 lowercase
        1 digit
        1 punc
        """
        get_rand = lambda L, c: [random.choice(L) for i in range(c)]
        P = get_rand(punct, 1)
        P.extend( get_rand(string.digits, 1))
        P.extend( get_rand(string.ascii_uppercase, 1))
        P.extend( get_rand(string.ascii_lowercase, 1))
        P.extend([random.choice(self.All) for i in range(size - len(P))])
        n = random.randint(0, fact_map[size-1])
        return n, decode2string(n, P)

def permute(n):
    return ''.join([random.choice(A) for i in range(n)])



if __name__=="__main__":
    d = DTE_random()
    p, encoding = d.generate_and_encode_password(size=12)
    #print p, encoding
    print d.decode_password(encoding)


