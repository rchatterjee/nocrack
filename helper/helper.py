#!/usr/bin/python

import sys, os
import bz2, re
import marisa_trie
import json
from Crypto.Random import random
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault_config import MAX_INT

from os.path import (expanduser, basename)
# opens file checking whether it is bz2 compressed or not.
import tarfile

home = expanduser("~")
pwd = os.path.dirname(os.path.abspath(__file__))


class Token:
    def __init__(self, v_=None, n_=None, o_=None):
        self.value = v_
        self.name = n_
        self.orig = o_

    @property
    def __str__(self):
        return "%s,%s,%s" % (self.value, self.name, self.orig)


# returns the type of file.
def file_type(filename):
    magic_dict = {
        "\x1f\x8b\x08": "gz",
        "\x42\x5a\x68": "bz2",
        "\x50\x4b\x03\x04": "zip"
    }
    max_len = max(len(x) for x in magic_dict)
    with open(filename) as f:
        file_start = f.read(max_len)
    for magic, filetype in magic_dict.items():
        if file_start.startswith(magic):
            return filetype
    return "no match"


def open_(filename, mode='r'):
    type_ = file_type(filename)
    if type_ == "bz2":
        f = bz2.BZ2File(filename, mode)
    elif type_ == "gz":
        f = tarfile.open(filename, mode)
    else:
        f = open(filename, mode);
    return f;


regex = r'([A-Za-z_]+)|([0-9]+)|(\W+)'


def whatchar(c):
    if c.isalpha(): return 'L';
    if c.isdigit():
        return 'D';
    else:
        return 'Y'


from math import sqrt


def mean_sd(arr):
    s = sum(arr)
    s2 = sum([x * x for x in arr])
    n = len(arr)
    m = s / float(n)
    sd = sqrt(float(s2) / n - m * m)
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
