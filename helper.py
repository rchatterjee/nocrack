#!/usr/bin/python

import sys, os
import bz2, re
import marisa_trie, json

# For checking memory usage
import resource

EPSILON = '|_|'
GRAMMAR_R=0
NONTERMINAL = 1
MEMLIMMIT = 1024 # 1024 MB, 1GB
MIN_COUNT = 3

from os.path import (expanduser, basename)
home = expanduser("~");

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

# opens file checking whether it is bz2 compressed or not.
def open_(filename, mode='r'):
    if file_type(filename) == "bz2":
        f=bz2.BZ2File(filename, mode)
    else:
        f = open(filename, mode);
    return f;

regex = r'([A-Za-z_]+)|([0-9]+)|(\W+)'
def whatchar( c ):
    if c.isalpha(): return 'L';
    if c.isdigit(): return 'D';
    else: return 'Y'
