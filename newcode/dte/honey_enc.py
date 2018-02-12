#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import os, sys, struct, resource
from pathlib import Path
p = Path(__name__).resolve()
parent, root = p.parent, p.parents[1]
BASE_DIR = os.getcwd()
sys.path.append(str(root))

import string
import honeyvault_config as hny_config
from helper import getIndex, convert2group, random

MAX_INT = hny_config.MAX_INT


# IDEA:  every genrule could be kept in a Trie.
# DRAWBACK: it is unlikely that those words will share
# much prefix of each other...:p

class DTE(object):
    def __init__(self, grammar=None):
        self.G = grammar
        if not self.G:
            raise "NoSubgrammar"
            # self.G.load(hny_config.GRAMMAR_DIR+'/grammar.cfg')

    def encode(self, lhs, rhs):
        """
        Encode one rule. lhs --> rhs
        """
        assert lhs in self.G, "lhs={} not in self.G".format(lhs)
        a = self.G.encode_rule(lhs, rhs)
        assert a, "NonT ERROR lhs={}, rhs={}, a={}".format(lhs, rhs, a)
        return a

    def decode(self, lhs, pt):
        """
        Decode one rule given a random number pt, and lhs.
        """
        return self.G.decode_rule(lhs, pt)

    def encode_pw(self, pw):
        """
        Encode a password under a the grammar associated with the DTE.
        """
        return self.G.encode_pw(pw)

    def decode_pw(self, P):
        """Given a list of random numbers decode a password under the
        associated grammar with this DTE.
        """
        return self.G.decode_pw(P)

    def __eq__(self, o_dte):
        return self.G == o_dte.G

    def __bool__(self):
        return self.G.is_grammar()


class DTE_random(DTE):
    punct = "!@#%&*_+=~"
    All = string.ascii_letters + string.digits + punct
    must_set = [punct, string.digits, string.ascii_uppercase, string.ascii_lowercase]
    fact_map = [1, 2, 6, 24, 120, 720,
                # 1, 2, 3, 4,  5,   6,
                5040, 40320, 362880, 3628800, 39916800,
                # 7,    8,     9,      10,      11
                479001600, 6227020800, 87178291200, 1307674368000, 20922789888000,
                # 12,      13,         14,          15,            16,
                355687428096000, 6402373705728000, 121645100408832000, 2432902008176640000
                # 17,            18,               19,                 20
                ]
    MAX_ALLOWED = 14  # maximum pw length supported
    MIN_PW_LENGTH = 8  # 8 is the minimum length of the pass
    RANDOM_LEN_PART = MAX_ALLOWED - MIN_PW_LENGTH

    def __init__(self, size=10):
        self.pw, self.encoding = self.generate_and_encode_password(size)

    def generate_and_encode_password(self, size=10):
        """
        Generates and encodes a password of size @size.
        first choose size+1 random numbers, where first one is to encode the length,
        and the rest are to encode the passwords  
        """
        assert size < self.MAX_ALLOWED, "Size of asked password={}, which is bigger" \
                                        "than supported {}".format(size, self.MAX_ALLOWED)
        size = max(size, self.MIN_PW_LENGTH)

        N = random.randints(0, MAX_INT, size + 1)
        N[0] += (size - self.MIN_PW_LENGTH) - N[0] % (
            self.MAX_ALLOWED - self.MIN_PW_LENGTH)  # s.t., N[0] % MAX_ALLOWED = size

        P = [s[N[i + 1] % len(s)] for i, s in enumerate(self.must_set)]  # must set characters

        P.extend(self.All[n % len(self.All)] for n in N[len(self.must_set) + 1:])
        n = random.randint(0, MAX_INT)
        password = self.decode2string(n, P)
        N.append(n)
        extra = hny_config.PASSWORD_LENGTH - len(N);
        N.extend([convert2group(0, 1) for x in range(extra)])
        return password, N

    @staticmethod
    def get_char(s, char_grp):
        for i, c in enumerate(s):
            if c in char_group:
                return i, c
        return 0, s[0]

    @staticmethod
    def get_random_for_this(c, arr):
        i = arr.index(c)
        n = len(arr)
        return random.randint(0, MAX_INT / n) * n + t

    @staticmethod
    def encode2number(s):
        sorted_s = sorted(s)
        n = len(s)
        code = 0
        for i, ch in enumerate(s):
            l = sorted_s.index(ch)
            code += l * DTE_random.fact_map[n - i - 2]
            del sorted_s[l]
        p = random.randint(0, MAX_INT / DTE_random.fact_map[n - 1])
        return DTE_random.fact_mapp[n - 1] * p + code

    @staticmethod
    def decode2string(num, s):
        """
        permutes the whole string @s, by the numebr @num
        """
        sorted_s = sorted(s)
        n = len(s)
        assert n < DTE_random.MAX_ALLOWED, "The size asking too big, only decode first MAX_ALLOWED" \
                                           "s: {}".format(s)

        st = ['' for i in range(n)]
        num %= DTE_random.fact_map[n - 1]
        for i in range(n):
            x = num // DTE_random.fact_map[n - i - 2]
            num -= x * DTE_random.fact_map[n - i - 2]
            st[i] = sorted_s[x]
            del sorted_s[x]
        return ''.join(st)

    def encode_pw(self, pw):
        p = list(pw[:])
        must_4 = [DTE_random.get_char(p, m) for m in must_set]
        for x in must_4:
            del p[x[0]]
        pw_random_order = DTE_random.decode2string(
            random.randint(0, self.fact_map[len(p) - 1]),
            p)
        code_g = [random.randint(0, MAX_INT / self.MAX_ALLOWED) * \
                  self.MAX_ALLOWED + len(pw)]
        for i, x in enumerate(must_4):
            code_g.append(DTE_random.get_random_for_this(
                x[1], self.must_set[i]))
        for p in pw_random_order:
            code_g.append(DTE_random.get_random_for_this(
                p, self.All))
        code_g.append(self.encode2number(pw))
        extra = hny_config.PASSWORD_LENGTH - len(code_g);
        code_g.extend([convert2group(0, 1) for x in range(extra)])
        return code_g

    def decode_pw(self, N):
        assert len(N) == hny_config.PASSWORD_LENGTH, "Encoding length mismatch! Expecting" \
                                                     "{}, got {}".format(hny_config.PASSWORD_LENGTH, len(N))
        n = self.MIN_PW_LENGTH + N[0] % (self.MAX_ALLOWED - self.MIN_PW_LENGTH)
        N = N[1:n + 2]
        P = [s[N[i] % len(s)] for i, s in enumerate(self.must_set)]
        P.extend(self.All[n % len(self.All)] for n in N[len(self.must_set):-1])
        n = N[-1]
        password = self.decode2string(n, P)
        return password

    def generate_random_password(self, size=10):
        """
        Generates random password of given size
        it ensures -
        1 uppercase
        1 lowercase
        1 digit
        1 punc
        """
        P = [random.choice(s) for s in self.must_set]
        P.extend([random.choice(self.All)
                  for n in range(size - len(self.must_set))])
        n = random.randint(0, MAX_INT)
        password = self.decode2string(n, P)
        return password


# class DTE_large(DTE):
#     """
#     encodes a rule
#     """
#     def __init__(self, grammar=None, cal_cdf=False):
#         self.G = grammar
#         if not self.G:
#             self.G = TrainedGrammar(cal_cdf=cal_cdf)
#             # self.G.load(hny_config.GRAMMAR_DIR+'/grammar.cfg')

#     # def encode(self, lhs, rhs):
#     #     return self.G.encode_rule(lhs,rhs)

#     # def decode(self, lhs, pt):
#     #     return self.G.decode_rule(lhs, pt)

#     def get_freq(self, lhs, rhs):
#         return self.G.get_freq(lhs, rhs)
#         try:
#             s, e = self.G.get_freq_range(lhs, rhs)
#             return e-s
#         except ValueError: 
#             print "ValueError in get_freq -- %s is not in %s:" % \
#                 (rhs,self.G[lhs][0])
#             return -1



def getVal(arr, val):
    """
    arr -> is a list of values of type same as 'val' and also has a frequency
    e.g. arr: [['a',0,123], ['asd', 1, 31], ['ADR', 1, 345]]
    val -> is a value of same type of values in arr, e.g. 'asd'
    returns: a random number between, cumulative probability of 'asd' and
    the element just before it, i.e. 'a'.
    """
    c = 0
    found = False
    totalC = 0;
    t = -1;
    for i, x in enumerate(arr):
        # print x
        c += x[2]
        totalC += x[2]
        if not found and x[0] == val:
            if i == 0:
                a = 0;
            else:
                a = c - x[2]
            t = random.randint(a, c - 1)
            found = True
            print(x, t)
    if t > -1:
        # to deal with floating this is used, basically converted the numebrs in (mod totalC)
        # ASSUMPTION: max value of sum of frequency is 4,294,967,295, i.e. ~ 4.29 billion!!
        return convert2group(t, totalC)
    return t


# def getIndex( arr, s, e, x ):
#     """
#     Binary searches for 'x' in 'arr' between indices 's' and 'e'.
#     :return `integer` index of x in arr s.t. arr[index-1] <= x < arr[index] 
#     """
#     if arr[s] > x: return s
#     if arr[e] < x: return e;
#     if arr[(s+e)/2] > x: return getIndex( arr, s, (s+e)/2, x )
#     else: return getIndex( arr, (s+e)/2+1, e, x);


def getGenerationAtRule(lhs, prob, grammar):
    """
    given a left hand side of a rule and the grammar it finds the exact rhs
    which has CP(cumulative Probability) in the ruleset just more than the given 
    `prob`
    :returns `('IloveYou',0,420)`
    """
    # REMEMBER: every array in grammar rule should have start with a
    # dummy entry('',0,0) and prob zero!!
    d = [0]

    d.extend([x[2] for x in grammar[lhs]])
    for i in range(1, len(d)):
        d[i] += d[i - 1];
    prob = prob % d[-1]
    t = getIndex(d, 0, len(d) - 1, prob) - 1;
    return grammar[lhs][t]


def Encode_spcl(m, grammar):
    print("Special Encoding::::", m)
    return None  # TODO
    W = m  # break_into_words(m, trie)
    P = ['%s%d' % (whatchar(w), len(w)) for w in W]
    E = [];
    for w, p in zip(W[:-1], P[:-1]):
        E.append(getVal(grammar['S'], p + ',S'))
        E.append(getVal(grammar[p], w));
    E.append(getVal(grammar['S'], P[-1]))
    E.append(getVal(grammar[P[-1]], W[-1]));
    if PASSWORD_LENGTH > 0:
        extra = PASSWORD_LENGTH - len(E);
        E.extend([convert2group(0, 1) for x in range(extra)])
    return E;


def main():
    dte = DTE()
    scanner = Scanner()
    print("Resource:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);
    # p='(NH4)2Cr2O7' # sys.stdin.readline().strip()
    p = 'iloveyou69'
    c = Encode(p, scanner, dte);
    # print "Encoding:", c
    m = Decode(c, dte);
    # print "After Decoding:", m
    # return
    #     if PASSWORD_LENGTH>0:
    for s in range(0000):
        E = []
        E.extend([convert2group(0, 1) for x in range(PASSWORD_LENGTH)])
        c_struct = struct.pack('%sI' % len(E), *E)
        m = Decode(c_struct, dte);
        print(s, ":", m)


if __name__ == "__main__":
    main()
