#!/usr/bin/python

import bz2
import os
import sys
from dawg import DAWG, IntDAWG
from os.path import expanduser
import struct
# opens file checking whether it is bz2 compressed or not.
import gzip
import string
import random as orig_random
BASE_DIR = os.getcwd()
from honeyvault_config import MAX_INT, DEBUG, PRODUCTION, MEMLIMMIT
import resource  # For checking memory usage

home = expanduser("~")
pwd = os.path.dirname(os.path.abspath(__file__))
regex = r'([A-Za-z_]+)|([0-9]+)|(\W+)'
char_group = string.printable


class random:
    @staticmethod
    def randints(s, e, n=1):
        """
        returns n uniform random numbers from [s, e] (including both ends)
        """
        if e == s:
            return [s]*n
        assert e > s, "Wrong range: [{}, {}]".format(s, e)
        n = max(1, n)
        if not DEBUG:
            arr = [s + a % (e - s) for a in struct.unpack('<%dL' % n, os.urandom(4 * n))]
        else:
            orig_random.seed(0)
            arr = [orig_random.randint(s, e) for _ in range(n)]
        return arr

    @staticmethod
    def randint(s, e):
        """
        returns one random integer between s and e. Try using @randints in case you need
        multiple random integer. @randints is more efficient
        """
        return random.randints(s, e, 1)[0]

    @staticmethod
    def choice(arr):
        i = random.randint(0, len(arr) - 1)
        assert i < len(arr), "Length exceeded by somehow! Should be < {}, but it is {}" \
            .format(len(arr), i)
        return arr[i]

    @staticmethod
    def sample(arr, n):
        return [arr[i] for i in random.randints(0, len(arr) - 1, n)]


class Token:
    def __init__(self, v_=None, n_=None, o_=None):
        self.value = v_
        self.name = n_
        self.orig = o_

    @property
    def __str__(self):
        return "%s,%s,%s" % (self.value, self.name, self.orig)


# returns the type of file.
def file_type(filename, param='rb'):
    magic_dict = {
        b"\x1f\x8b\x08": "gz",
        b"\x42\x5a\x68": "bz2",
        b"\x50\x4b\x03\x04": "zip"
    }
    if param.startswith('w'):
        return filename.split('.')[-1]
    max_len = max(len(x) for x in magic_dict)
    with open(filename, 'rb') as f:
        file_start = f.read(max_len)
    for magic, filetype in list(magic_dict.items()):
        if file_start.startswith(magic):
            return filetype
    return "no match"


def check_resource(n=0):
    mem_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    r = MEMLIMMIT * 1024 - mem_used
    print("Memory Usage: {} MB, Lineno: {}".format(mem_used, n))
    if r < 0:
        print("Hitting the memory limit of 1 GB. \nPlease increase the"
              "limit or use smaller data set.  Lines processed, {0:d}"
              .format(n))
        return -1
    return r


def load_dawg(f, t=IntDAWG):
    T = t()
    T.read(open_(f))
    return T


def save_dawg(T, fname):
    if not fname.endswith('gz'):
        fname = fname + '.gz'
    with gzip.open(fname, 'w') as f:
        T.write(f)


def open_(filename, mode='r'):
    type_ = file_type(filename, mode)
    if type_ == "bz2":
        f = bz2.open(filename, mode)
    elif type_ == "gz":
        f = gzip.open(filename, mode)
    else:
        f = open(filename, mode);
    return f

def chunks(l, n):
    """Break the array l in n chunks, the size of each chunk is determined as
    len(l)/n. The last chunk might be of smaller length
    """
    t = len(l)//n
    return (l[i:i+t] for i in range(0, len(l), t))


def print_err(*args):
    if DEBUG:
        sys.stderr.write(' '.join([str(a) for a in args]) + '\n')


def print_production(*args):
    if PRODUCTION:
        sys.stderr.write(' '.join([str(a) for a in args]) + '\n')


printed_once_dict = {}


def print_once(*args):
    h = hash(args)
    if h not in printed_once_dict:
        printed_once_dict[h] = True
        print(args)


def whatchar(c):
    if c.isalpha(): return 'W';
    if c.isdigit():
        return 'D';
    else:
        return 'Y'


from math import sqrt


# A = [('asdf',12), ('swer', 213)..]
# p = 15 --> res swer
def bin_search(A, p, s, e):
    """Search p in A
    """
    mid = (s + e) / 2
    if (mid == 0 or A[mid - 1][1] <= p) \
            and A[mid][1] > p:
        return A[mid][0]
    elif A[mid][1] <= p:
        return bin_search(A, p, mid, e)
    else:
        return bin_search(A, p, s, mid)


def bin_search_bisect(A, p):
    pass

def mean_sd(arr):
    s = sum(arr)
    s2 = sum((x * x for x in arr))
    n = len(arr)
    m = s / float(n)
    try:
        sd = sqrt(abs(s2 * n - s * s)) / n
    except ValueError:
        print("In mean_sd:", arr, (s2 * n - s * s))
        raise ValueError
    return m, sd


def convert2group(t, totalC, n=1):
    if n==1:
        return t + random.randint(0, (MAX_INT - t) // totalC) * totalC
    else:
        return [
            t + c * totalC
            for c in random.randints(0, (MAX_INT-t) // totalC, n=n)
        ]


def isascii(w):
    """Is all characters in w are ascii characters"""
    try:
        w.encode('ascii')
        return True
    except UnicodeError:
        return False

# assumes last element in the array(A) is the sum of all elements
def getIndex(p, A):
    p %= A[-1]
    i = 0;
    for i, v in enumerate(A):
        p -= v;
        if p < 0: break
    return i


from multiprocessing import Pool
import itertools


def wrap_func(args):
    func, data = args
    D = [func(d) for d in data]
    print_err('done', len(D))
    return D


def process_parallel(func, data, func_load=10):
    """
    its a wrapper over multiprocess.Pool
    """
    m = len(data) // func_load  # 10 is the magic number
    # print "Total:", len(data), m
    if m > 10:
        split_data = [(func, data[i * m:(i + 1) * m]) for i in range(10)]
        if DEBUG:
            p = list(map(wrap_func, split_data))
        else:
            pool = Pool()
            p = pool.map(func=wrap_func, iterable=split_data)
        return list(itertools.chain(*p))
    else:
        return wrap_func((func, data))


def diff(oldG, newG):
    """
    returns the difference of the two dicts. oldG-newG
    """
    if not (isinstance(oldG, dict) and isinstance(newG, dict)):
        yield (oldG, newG)
    else:
        for k in oldG.keys():
            if k not in newG:
                yield k
            else:
                vold, vnew = oldG[k], newG[k]
                if vold != vnew:
                    print("Not equal for", k, flush=True)
                    diff(vold, vnew)
