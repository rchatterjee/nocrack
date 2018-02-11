#!/usr/bin/python
import os
import sys

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
import marisa_trie
import json
from helper import open_, getIndex
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from scanner_helper import GrammarStructure
from collections import OrderedDict, defaultdict


# -----------------------NOT USED! --------------------------------------------------
class Grammar(object):
    def __init__(self, config_fl=None, scanner=None, Empty=False):
        self.scanner = scanner if scanner else Scanner()
        self.grammar_structure = GrammarStructure().G
        self.G = defaultdict(OrderedDict)
        if Empty:
            "Returning For empty"
            return
        from string import ascii_lowercase, digits, punctuation
        for typ, characters in zip('LDY', [ascii_lowercase, digits, punctuation]):
            self.G[typ] = OrderedDict([(x, [MIN_COUNT - 1, TERMINAL])
                                       for x in characters])
            self.G['G']['%s,G' % typ] = [MIN_COUNT / 2 - 1, NONTERMINAL]
            self.G['G']['%s' % typ] = [MIN_COUNT - 1, NONTERMINAL]

    def addRule_lite(self, lhs, rhs, freq, typ,
                     ignore_addingfreq=False):  # typ is NONTERMINAL or NERMINAL
        if ignore_addingfreq:
            self.G[lhs].setdefault(rhs, [freq, typ])
        else:
            self.G[lhs].setdefault(rhs, [0, typ])
            self.G[lhs][rhs][0] += freq

    def update_total_freq(self):
        for lhs, rhs_dict in list(self.G.items()):
            rhs_dict['__total__'] = sum([x[0]
                                         for x in list(rhs_dict.values())
                                         if type(x) == type([])])

    def parse_pw(self, pw):
        return self.scanner.tokenize(pw, isMangling=True)

    def get_freq_range(self, lhs, rhs):
        try:
            rhs_dict = self.G[lhs]
        except KeyError:
            return -1, -1
        try:
            i = list(rhs_dict.keys()).index(rhs)
            l = 0;
            l += sum([rhs_dict[x][0]
                      for x in list(rhs_dict.keys())[:i]])
            r = l + rhs_dict[rhs][0]
            return l, r  # range is [l,r), r not included rember
        except ValueError:
            print("Could not find ", lhs, rhs, "in G!")
            print(rhs_dict)
            raise ValueError
            return -1, -1

    def get_rhs(self, lhs, pt):
        rhs_dict = self.G[lhs]
        t = 0
        pt %= rhs_dict['__total__']
        for r, v in list(rhs_dict.items()):
            t += v[0]
            if t > pt: break
        if t > rhs_dict['__total__']:
            print("Could not Find: ", lhs, pt)
            return None, 0, TERMINAL
        return r, v[0], v[1]

    def update_grammar(self, G1=None, pw=None):
        print("Updating with", pw)
        if not G1:
            G1 = self.scanner.get_parse_tree(pw)
        for lhs, rhs in list(G1.items()):
            self.G[lhs].update(rhs)
            if '__total__' in self.G[lhs]:
                del self.G[lhs]['__total__']
            self.G[lhs]['__total__'] = \
                sum([x[0] for x in list(self.G[lhs].values())])

    def fix_freq(self, pcfg):
        for l, r_dict in list(self.G.items()):
            for r, v in list(r_dict.items()):
                if r != '__total__':
                    v[0] = pcfg.get_freq(l, r)
        print("Fixing frequencies:", '*' * 20)
        self.update_total_freq()

    # Completely messed up now
    def insert(self, w, freq):
        P, W, U = self.scanner.tokenize(w, True)
        # TODO Add mangling
        # Improve the grammar
        rule = ','.join(P)
        self.addRule_lite('G', rule, freq, NONTERMINAL)
        for l, r in zip(W, U):
            if l != r:
                for c, d in zip(l, r):
                    self.addRule_lite(c, d, freq, TERMINAL)

    def save(self, out_file):
        json.dump(self.G, out_file)

    def load(self, in_file):
        self.G = json.load(open_(in_file),
                           object_pairs_hook=OrderedDict)

    def __eq__(self, o_g):
        return self.G == o_g.G

    def __iter__(self):
        return self.G.iterator

    def __getitem__(self, key):
        return self.G[key]

    def __contains__(self, x):
        return x in self.G

    def __str__(self):
        s = "Grammar: "
        s += '\n'.join('%s -> %s' % (k, str(v))
                       for k, v in list(self.G.items())
                       if k not in ['L', 'D', 'Y'])
        return s

    def total_freq(self, key):
        return self.G[key]['__total__']

    def findPath(self, w):
        # scanner cannont be null,
        P, W, U = self.scanner.tokenize(w)
        # start path
        try:
            pos = inversemap[','.join(P)]
        except KeyError:
            print("Falling back to all-match Rule!")
            return []  # Not implemented till now
        print(pos)


class TrainedGrammar(Grammar):
    def __init__(self):
        super(TrainedGrammar, self).__init__()
        self.term_files = {}
        self.g_struc = GrammarStructure()
        for k, f in list(self.g_struc.getTermFiles().items()):
            sys.path.append(hny_config.GRAMMAR_DIR)
            X = __import__('%s' % f)
            self.term_files[k] = {
                'trie': marisa_trie.Trie().load(hny_config.GRAMMAR_DIR + f + '.tri'),
                'arr': eval("X.%s" % k),
                'trie_fl': hny_config.GRAMMAR_DIR + f + '.tri'
            }

    def __getitem__(self, key):
        if key in self.term_files:
            return self.term_files[key]['arr']
        return self.G[key]

    def total_freq(self, key):
        if key in self.term_files:
            return self.term_files[key]['arr'][-1]
        return super(TrainedGrammar, self).total_freq(key)

    def get_rhs(self, lhs, pt):
        if lhs in self.term_files:
            w, f = self.freq2key(pt, self.term_files[lhs]['trie'],
                                 self.term_files[lhs]['arr'])
            return w, f, TERMINAL
        return super(TrainedGrammar, self).get_rhs(lhs, pt)

    @staticmethod
    def key2freq(w, T, A):
        try:
            i = T.key_id(str(w))
            if i < 0:
                print("Could not find {w} in the trie." \
                      .format(**locals()))
                raise KeyError
            S = sum(A[:i])
            return S, S + A[i]
        except KeyError:
            return 0.0, 0.0

    @staticmethod
    def freq2key(f, T, A):
        i = getIndex(f, A)
        w = T.restore_key(i)
        return w, A[i]

    def get_freq_range(self, lhs, rhs):
        if lhs in self.term_files:
            return TrainedGrammar.key2freq(rhs, self.term_files[lhs]['trie'],
                                           self.term_files[lhs]['arr'])
        return super(TrainedGrammar, self).get_freq_range(lhs, rhs)
