#!/usr/bin/python
"""
This is a general grammar file that assumes the following grammar:
W -> <english-word>L | <name>L
D -> <date> | <phone-no> | [0-9]+
Y -> [^\W]+  # symbol
K -> <keyboard-sequence>
R -> repeat
S -> sequence # 123456, abcdef, ABCDEFG
L -> Capitalize | ALL-UPPER | all-lower | l33t
G -> <some-combination-of-those-NonTs>
"""

import os, sys
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG, DAWG
import marisa_trie
import struct, json, bz2, re
from lexer_helper import Date, KeyBoard
from helper.helper import open_, getIndex
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from collections import OrderedDict, defaultdict
from pprint import pprint

# Dictionaries:
# English_30000.dawg
# facebook-firstnames-withcount.dawg
# facebook-lastnames-withcount.dawg

WORD_DAWG  = IntDAWG().load('data/English_30000.dawg')
FNAME_DAWG = IntDAWG().load('data/facebook-firstnames-withcount.dawg')
LNAME_DAWG = IntDAWG().load('data/facebook-lastnames-withcount.dawg')

total_f = WORD_DAWG[u'__total__'] + \
    FNAME_DAWG[u'__total__'] + \
    LNAME_DAWG[u'__total__']

l33t_replaces = DAWG.compile_replaces({
        '3':'e', '4':'a', '@':'a',
        '$':'s', '0':'o', '1':'i',
        'z':'s'
        })

def l33t(word):
    pass
                                      

def NonT_L(w):
    if not w.isalpha():
        return None
    if w.istitle():
        return 'Capitalize'
    elif w.islower():
        return 'lower'
    elif w.isupper():
        return 'UPPER'

def NonT_W(word):
    w = unicode(word.lower())
    dawg = []
    for d in [WORD_DAWG, FNAME_DAWG, LNAME_DAWG]:
        k = WORD_DAWG.similar_keys(unicode(w), l33t_replaces)
        if k:
            dawg.append((d,k[0]))
    if dawg:
        f = sum([d[0].get_value(unicode(d[1])) for d in dawg])
        L = NonT_L(word)
        if not L:
            L = 'l33t'
        return 'W', [(word, L)], float(f)/total_f

def NonT_D(word):
    d = Date().IsDate(word)
    if d:
        return 'T', [d], len(word)/8.0
    else:
        if word.isdigit():
            return 'D', [word], 0.01


def NonT_Y(word):
    regex = r'^\W+$'
    if re.match(regex, word):
        return 'Y', [word], 0.01

def get_all_gen_rules(word):
    if not word: return None
    NonT_set = [NonT_W, NonT_D,
                NonT_Y]
    rules = filter(lambda x: x, [f(word) for f in NonT_set])
    if rules:
        return max(rules, key=lambda x: x[-1])

def prod(args):
    p = 1.0
    for i in args:
        p = p*i
    return p

def join_rules( *args ):
    for a in args:
        if not a: return None
    k = ''.join([a[0] for a in args])
    v1 = []
    for a in args:
        v1.extend(a[1])
    v2 = prod([a[2] for a in args])
    return k, v1, v2

def parse(word):
    A = {}
    for j in range(len(word)):
        for i in range(len(word)-j+1):
            A[(i, i+j)] = get_all_gen_rules(word[i:j+i+1])
            t = [A[(i, i+j)]]
            t.extend([join_rules(A[(i,k)], A[(k+1, i+j)])
                          for k in range(i, i+j)])
            t = filter(lambda x: x, t)
            if t:
                A[(i, i+j)] = max(t,
                                  key = lambda x: x[-1] if x else 0.0)
            else:
                A[(i, i+j)] = None
            
    return A[(0, len(word)-1)]





if __name__ == "__main__":
    print parse(sys.argv[1])
