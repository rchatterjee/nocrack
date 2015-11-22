#!/usr/bin/python

import sys, os
import bz2, re
import marisa_trie
import json
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault_config import MAX_INT, DEBUG, PRODUCTION
from os.path import (expanduser, basename)
import struct
# opens file checking whether it is bz2 compressed or not.
import tarfile

DEBUG = True
home = expanduser("~")
pwd = os.path.dirname(os.path.abspath(__file__))
regex = r'([A-Za-z_]+)|([0-9]+)|(\W+)'

class random:
    @staticmethod
    def randints(s, e, n=1):
        """
        returns n uniform random numbers from [s, e] (including both ends)
        """
        assert e>=s, "Wrong range: [{}, {}]".format(s, e)
        n = max(1, n)
        if DEBUG:
            arr = [s + a%(e-s) for a in struct.unpack('<%dL'%n, os.urandom(4*n))]
        else:
            random.seed(0)
            arr = [s + a%(e-s) for a in random.random()*n]
        return arr

    @staticmethod
    def randint(s,e):
        """
        returns one random integer between s and e. Try using @randints in case you need
        multiple random integer. @randints is more efficient
        """
        return random.randints(s,e,1)[0]
    
    @staticmethod
    def choice(arr):
        i = random.randint(0, len(arr)-1)
        assert i<len(arr), "Length exceeded by somehow! Should be < {}, but it is {}"\
            .format(len(arr), i)
        return arr[i]
    
    @staticmethod
    def sample(arr, n):
        return [arr[i] for i in random.randints(0, len(arr)-1, n)]

class Token:
    def __init__(self, v_=None, n_=None, o_=None):
        self.value = v_
        self.name = n_
        self.orig = o_

    @property
    def __str__(self):
        return "%s,%s,%s" % (self.value, self.name, self.orig)


# returns the type of file.
def file_type(filename, param='r'):
    magic_dict = {
        "\x1f\x8b\x08": "gz",
        "\x42\x5a\x68": "bz2",
        "\x50\x4b\x03\x04": "zip"
    }
    if param.startswith('w'):
        return filename.split('.')[-1]
    max_len = max(len(x) for x in magic_dict)
    with open(filename, param) as f:
        file_start = f.read(max_len)
    for magic, filetype in magic_dict.items():
        if file_start.startswith(magic):
            return filetype
    return "no match"


def open_(filename, mode='r'):
    type_ = file_type(filename, mode)
    if type_ == "bz2":
        f = bz2.BZ2File(filename, mode)
    elif type_ == "gz":
        f = tarfile.open(filename, mode)
    else:
        f = open(filename, mode);
    return f;


def get_line(file_object, lim=-1):
    for i,l in enumerate(file_object):
        if lim>0 and lim<i: 
            break
        try:
            l.decode('ascii')
            words = l.strip().split()
            c, w = int(words[0]), ' '.join(words[1:])
            if w and c>0:
                yield w,c
        except:
            continue
        

def print_err( *args ):
    if DEBUG == True:
        sys.stderr.write(' '.join([str(a) for a in args])+'\n')

def print_production( *args ):
    if PRODUCTION == True:
        sys.stderr.write(' '.join([str(a) for a in args])+'\n')

printed_once_dict={}
def print_once( *args ):
    h = hash(args)
    if h not in printed_once_dict:
        printed_once_dict[h] = True
        print args
    
def whatchar(c):
    if c.isalpha(): return 'W';
    if c.isdigit():
        return 'D';
    else:
        return 'Y'


from math import sqrt

#A = [('asdf',12), ('swer', 213)..]
#p = 15 --> res swer
def bin_search(A, p, s, e):
    """Search p in A
    """
    mid = (s+e)/2
    if (mid == 0 or A[mid-1][1]<=p)\
        and A[mid][1] > p:
        return A[mid][0]
    elif A[mid][1]<=p:
        return bin_search(A, p, mid, e)
    else:
        return bin_search(A, p, s, mid )

def mean_sd(arr):
    s = sum(arr)
    s2 = sum((x * x for x in arr))
    n = len(arr)
    m = s / float(n)
    try:
        sd = sqrt(abs(s2*n - s * s))/n
    except ValueError:
        print "In mean_sd:", arr, (s2*n-s*s)
        raise ValueError
    return m, sd


def convert2group(t, totalC):
    return t + random.randint(0, (MAX_INT-t)/totalC) * totalC
    

# assumes last element in the array(A) is the sum of all elements
def getIndex(p, A):
    p %= A[-1]
    i = 0;
    for i, v in enumerate(A):
        p -= v;
        if p<0: break
    return i


from multiprocessing import Pool
import itertools
def wrap_func(args):
    func, data = args
    D = [func(d) for d in data]
    print_err('done', len(D))
    return D

def ProcessParallel(func, data, func_load=10):
    """
    its a wrapper over multiprocess.Pool
    """    
    m = len(data)/func_load # 10 is the magic number
    #print "Total:", len(data), m
    if m>10:
        split_data = [(func, data[i*m:(i+1)*m]) for i in range(10)]
        if DEBUG:
            p = map(wrap_func, split_data)
        else:
            pool = Pool()
            p = pool.map(func=wrap_func, iterable=split_data)
        return list(itertools.chain(*p))
    else:
        return wrap_func((func, data))
    

def diff(oldG, newG):
    """
    returns the difference of the two grammars.
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
                    diff(oldG[k], newG[k])
    
