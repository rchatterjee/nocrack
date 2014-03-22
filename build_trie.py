#!/usr/bin/python
import sys, marisa_trie
from array import array
import re


def create_trie():
    """
This is a helper function to create a file containing the key_id
of every Word in the trie word list.
    """

    if len(sys.argv)<2:
        print "USAGE: %s dictionary_fl trie_fl [out_fl]"
        exit(0)

    trie_fl = sys.argv[1]
    dictionary_fl = sys.argv[2]
    out_fl = sys.stdout

    if len(sys.argv) > 2:
        out_fl = sys.argv[3]

    T = marisa_trie.Trie().load(trie_fl)
    N = 8460018
    A = [0]*N

    for line in open(dictionary_fl):
        l = line.strip().split()
        k = T.key_id(unicode(l[1]))
        if k > 0:
            A[k] = int(l[0])
        else:
            print l

    with open(out_fl, 'wb') as f:
        for s in A:
            f.write('%d\n' % s)


class GrammarStructure:
    g_reg = r'^(?P<lhs>[A-Z]+)\s+->(?P<rhs>.*)$'
    G = {}

    def __init__(self, g_file='sample_grammarstructure.cfg'):
        for l in open(g_file):
            l = l.strip()
            m = re.match(self.g_reg, l)
            rhs = filter(lambda y: 'xx' if re.match(r'None', y) else y.strip(), m.group('rhs').split('|'))
            try:
                self.G[m.group('lhs')].extend(rhs)
            except KeyError:
                self.G[m.group('lhs')] = rhs

    def __str__(self):
        return '\n'.join(['%s -> %s' % (lhs, ' | '.join(rhs)) for lhs, rhs in self.G.items()])


class Token:
    def __init__(self, val=None, type_=0, meta=None):
        self.value = val    # string/Token
        self.type_ = type_  # 0(NonT), 1(Terminal), 2(others)
        self.meta  = meta   # Mangles

    def __str__(self):
        return str([self.value, self.type_])

    def show(self):
        return str

        
    def getval(self):
        return self.value

    def __init__(self, strng):
        m = re.match(r"'(.*)'")
        if m:
            self.value = m.group(1)
            self.type_ = 1   # Terminal
            self.meta = ''
        else:
            self.value = strng
            self.type_ = 0
            self.meta  = strng

    def __eq__(self, other):
        return self.value == other.value and self.type_ == other.type_


class Rule:
    def __init__(self, rhs, freq=0):
        if type([]) == type(rhs):
            self.rhs = rhs    # list of Tokens
        else:
            self.rhs = [Token(x) for x in rhs.split(' ')]
        self.freq= freq

    def __eq__(self, other):
        if len(self.rhs) != len(other.rhs):
            return False
        for x, y in zip(self.rhs, other.rhs):
            if x != y: return False
        return True


class ParseTree:
    def __init__(self):
        self.tree = dict('S', [])

    def example(self):
        self.tree = {'S': [
            {'F': [{'B': ['']}, {'P': ['1']}, {'W': ['computer']}, {'S': ['']}]},
            {'I': ['']},
            {'F': [{'B': ['']}, {'P': ['']}, {'W': ['secret']}, {'S': ['23']}]},
        ]}


class Grammar:
    def __init__(self):
        g_structure = GrammarStructure()
        self.g = dict(('R', []))   # list of rules, R start symbol
        for lhs, rhs in g_structure.G.items():
            self.g[lhs] = [Rule(r) for r in rhs]


if __name__ == '__main__':
    G = GrammarStructure()
    print G
