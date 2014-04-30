#!/usr/bin/python
"""
This is a pcfg of almost the following grammar:
W -> <english-word>L | <name>L
D -> <date> | <phone-no> | [0-9]+
Y -> [^\W]+  # symbol
K -> <keyboard-sequence>
R -> repeat
S -> sequence # 123456, abcdef, ABCDEFG
L -> Capitalize | ALL-UPPER | all-lower | l33t
G -> <some-combination-of-those-NonTs>
"""

import os, sys, string
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG, DAWG
import marisa_trie
import struct, json, bz2, re
from lexer_helper import Date, KeyBoard, RuleSet, ParseTree
from helper.helper import open_, getIndex
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from honeyvault_config import MEMLIMMIT, GRAMMAR_DIR
from collections import OrderedDict, defaultdict
from pprint import pprint
import resource  # For checking memory usage
from lexer import NonT_L

grammar_file = GRAMMAR_DIR + '/grammar.cfg.bz2'

class prod_rule(object):
    def __init__(self, l, r, p):
        pass

class TrainedGrammar(object):

    l33t_replaces = DAWG.compile_replaces({
            '3':'e', '4':'a', '@':'a',
            '$':'s', '0':'o', '1':'i',
            'z':'s'
            })

    def __init__(self, g_file=grammar_file):
        self.load(g_file)
        self.NonT_set = filter(lambda x: x.find('_') < 0,  
                               self.G.keys()) + ['T']

    def load(self, filename):
        self.G = json.load(open_(filename),
                           object_pairs_hook=OrderedDict)
        for k,v in self.G.items():
            v['__total__'] = sum(v.values())

        self.Wdawg = IntDAWG(self.G['W'].items())

    def get_prob(self, l, r):
        f = self.G.get(l, {}).get(r, 0)
        if f>0:
            return float(f)/self.G[l]['__total__']

    def get_W_rule(self, word):
        w = unicode(word.lower())
        k = self.Wdawg.similar_keys(w, self.l33t_replaces)
        if k:
            k = k[0]
            L = NonT_L(w, word).parse_tree()
            return ('W', [(w, L)], self.get_prob('W', k))

    def get_T_rule(self, word):
        T = Date(word).parse_tree()
        if T:
            p = 10**(len(word)-8)
            # for r in T.tree:
            #     p *= self.get_prob(*r)
            # p *= self.get_prob(*(T.get_rule()))
            return ('T', [(word, T)], p)

    def get_all_matches(self, word):
        rules = []
        for nt in self.NonT_set:
            if nt == 'W':
                l = self.get_W_rule(word)
                if l: rules.append(l)
            elif nt == 'T':
                l = self.get_T_rule(word)
                if l: rules.append(l)
            else:
                f = self.G[nt].get(word, 0)
                if f>0:
                    rules.append((nt, [(word)], float(f)/self.G[nt]['__total__']))
        rules = filter(lambda x: x and x[-1], rules)
        if rules:
            return max(rules, key=lambda x: x[-1])

    def join(self, r, s):
        if (r and s and
            not r[0].startswith('L_') and
            not s[0].startswith('L_') and
            not r[0].startswith('T_') and
            not s[0].startswith('T_') ):
            k = r[0] + s[0]
            p = r[-1] * s[-1]
            a = r[1] + s[1]
            return (k, a, p)

    def parse(self, word):
        A = {}
        for j in range(len(word)):
            for i in range(len(word)-j):
                A[(i, i+j)] = self.get_all_matches(word[i:j+i+1])
                t = [A[(i, i+j)]]
                t.extend([self.join(A[(i,k)], A[(k+1, i+j)])
                          for k in range(i, i+j)])
                if t:
                    A[(i, i+j)] = \
                        max(t, key = lambda x: x[-1] if x else 0)
                else:
                    A[(i, i+j)] = ()
                    # print "Not sure why it reached here. But it did!"
                    # print i, j, word[i: i+j+1]
        return A[(0, len(word)-1)]


class SubGrammar(object):
    def __init__(self, base_pcfg):
        pass

if __name__=='__main__':
    tg = TrainedGrammar()
    print tg.parse(sys.argv[1])
