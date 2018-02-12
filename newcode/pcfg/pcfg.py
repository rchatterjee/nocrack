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
G -> DG | YG | WG | RG | SG | KG | D | Y | W | R | S | K
"""

import os
import string
import sys

BASE_DIR = os.getcwd()
from dawg import IntDAWG, DAWG
import json
from .lexer_helper import Date, RuleSet, ParseTree
from .lexer import NonT_L, get_nont_class
from helper import (
    open_, getIndex, convert2group, print_err,
    bin_search, print_once, random, whatchar, DEBUG
)
import honeyvault_config as hny_config
from collections import OrderedDict
import sys

GRAMMAR_FILE = hny_config.GRAMMAR_DIR + '/grammar.cfg.bz2'


class TrainedGrammar(object):
    l33t_replaces = DAWG.compile_replaces(hny_config.L33T)

    def __init__(self, g_file=GRAMMAR_FILE, cal_cdf=False):
        self.cal_cdf = cal_cdf
        self.load(g_file)
        self.NonT_set = [x for x in list(self.G.keys()) if x.find('_') < 0]

    def load(self, filename):
        self.G = json.load(open_(filename),
                           object_pairs_hook=OrderedDict)
        for k, v in list(self.G.items()):
            if self.cal_cdf:
                print_err("Calculating CDF!")
                lf = 0
                for l, f in list(v.items()):
                    v[l] += lf
                    lf += f
                v['__total__'] = lf
            else:
                v['__total__'] = sum(v.values())

        # Create dawg/trie of the Wlist items for fast retrieval
        Wlist = [x
                 for k, v in list(self.G.items())
                 for x in v
                 if k.startswith('W')]
        self.date = Date()
        self.Wdawg = IntDAWG(Wlist)

    def get_prob(self, l, r):
        f = self.G.get(l, {}).get(r, 0)
        tot = self.G.get(l, {}).get('__total__', 1e-3)
        return max(float(f) / tot, 0.0)

    def isNonTerm(self, lhs):  # this means given lhs, rhs will be in NonT
        return lhs in self.NonT_set

    def get_actual_NonTlist(self, lhs, rhs):
        if lhs == 'G':
            # Don't include, "W1,G", "D1,G" etc.
            if rhs.endswith(',G'):
                return []
            return rhs.split(',')
        elif lhs == 'T':
            return ['%s_%s' % (lhs, c)
                    for c in (rhs.split(',') if ',' in rhs
                              else rhs)]
        elif lhs == 'L':
            return ['%s_%s' % (lhs, c)
                    for c in rhs]
        elif lhs in ['W', 'D', 'Y', 'R', 'K']:
            return []
        else:
            return []

    def get_freq(self, l, r):
        return self.G.get(l, {}).get(r, 0)

    def get_W_rule(self, word):
        w = str(word.lower())
        k = self.Wdawg.similar_keys(w, self.l33t_replaces)
        if k:
            k = k[0]
            L = NonT_L(k, word)
            sym = 'W%s' % get_nont_class('W', k)
            try:
                p = self.get_prob(sym, k)
            except KeyError as ex:
                print(k, sym, ex)
                raise KeyError(ex)
            return sym, [(k, L)], p

    def get_T_rule(self, word):
        T = self.date.IsDate(word)
        if T:
            p = 10 ** (len(word) - 8)
            for r in T.tree:
                p *= self.get_prob(*r)
            p *= self.get_prob(*(T.get_rule()))
            return 'T', [(word, T)], p

    def get_all_matches(self, word):
        rules = []
        for nt in self.NonT_set:
            if nt.startswith('W'):
                l = self.get_W_rule(word)
                if l: rules.append(l)
            elif nt == 'T':
                l = self.get_T_rule(word)
                if l: rules.append(l)
            else:
                f = self.G[nt].get(word, 0)
                if f > 0:
                    rules.append((nt, [word], float(f) / self.G[nt]['__total__']))
        rules = [x for x in rules if x and x[-1]]
        if rules:
            return max(rules, key=lambda x: x[-1])

    def join(self, r, s):
        not_startswith_L_T = lambda x: x and \
                                       not (x[0].startswith('L_') or x[0].startswith('T_'))
        if not_startswith_L_T(s) and not_startswith_L_T(r):
            k = ','.join([r[0], s[0]])
            p = r[-1] * s[-1]
            a = r[1] + s[1]
            return (k, a, p)

    def random_parse(self, word, try_num=3):
        """
        Returns a random parse of the word following the grammar.
        """
        # First- rejection sampling, most inefficient version
        # break the word into random parts and then see if that parse exist
        print("\n^^^^^^^^^^^_______________^^^^^^^^^^^^^^")
        if try_num < 0:
            print("I am very sorry. I could not parse this :(!!")
            return None
            # NO IDEA HOW TO randomly pick a parse tree!! @@TODO

    def parse(self, word):
        A = {}
        if not word:
            return ()
        for j in range(len(word)):
            for i in range(len(word) - j):
                A[(i, i + j)] = self.get_all_matches(word[i:j + i + 1])
                t = [A[(i, i + j)]]
                t.extend([self.join(A[(i, k)], A[(k + 1, i + j)])
                          for k in range(i, i + j)])
                if t:
                    A[(i, i + j)] = \
                        max(t, key=lambda x: x[-1] if x else 0)
                else:
                    A[(i, i + j)] = ()
                    # print "Not sure why it reached here. But it did!"
                    # print i, j, word[i: i+j+1]
        return A[(0, len(word) - 1)]

    @staticmethod
    def default_parse_tree(word):
        """
        Returns the default parse of a word. Default parse is
        G -> W1,G | D1,G | Y1,G | W1 | D1 | Y1
        This parses any string over the allowed alphabet
        returns a l-o-r traversed parse tree
        """
        pt = ParseTree()
        n = len(word)
        for i, c in enumerate(word):
            r = whatchar(c) + '1'
            if i < n - 1:
                r = r + ',G'
            pt.add_rule(('G', r))
            pt.add_rule((r[:2], c.lower()))
            if r.startswith('W'):
                nont_l = NonT_L(c, c)
                pt.extend_rules(nont_l.parse_tree())

        return pt

    def l_parse_tree(self, word):  # leftmost parse-tree
        pt = ParseTree()
        p = self.parse(word)
        if not p:
            print("Failing at {!r}".format(word))
            return pt
        # assert p[0] in self.G['G'], "Wrong rule: {} --> {}".format('G', p[0])
        if p[0] not in self.G['G']:
            return self.default_parse_tree(word)

        pt.add_rule(('G', p[0]))
        for l, each_r in zip(p[0].split(','), p[1]):
            if isinstance(each_r, str):
                pt.add_rule((l, each_r))
            elif l.startswith('W'):
                pt.add_rule((l, each_r[0]))
                L_parse_tree = each_r[1].parse_tree()
                pt.add_rule(L_parse_tree[0])
                if len(L_parse_tree.tree) > 1:
                    pt.tree.extend(L_parse_tree[1][1])
            elif l == 'T':
                p = each_r[1]
                rule_name = ','.join([r[0].replace('T_', '')
                                      for r in p])
                pt.add_rule((l, rule_name))
                pt.extend_rules(p)
            else:
                print("Something is severely wrong")
        return pt

    def rule_set(self, word):
        rs = RuleSet()
        pt = self.l_parse_tree(word)
        for p in pt.tree:
            rs.add_rule(*p)
        return rs

    def encode_rule(self, l, r):
        rhs_dict = self.G[l]
        try:
            i = list(rhs_dict.keys()).index(r)
            if DEBUG:
                c = list(rhs_dict.keys())[i]
                assert c == r, "The index is wrong"
        except ValueError:
            print("'{}' not in the rhs_dict (l: '{}', rhs_dict: {})".format(r, l, self.G[l]))
            raise ValueError
        l_pt = sum(list(rhs_dict.values())[:i])
        r_pt = l_pt + rhs_dict[r] - 1
        return convert2group(random.randint(l_pt, r_pt),
                             rhs_dict['__total__'])

    def encode_pw(self, pw):
        pt = self.l_parse_tree(pw)
        # print("L_parse_tree", pw, pt)
        try:
            code_g = [self.encode_rule(*p)
                      for p in pt]
        except ValueError as ex:
            print("Error in encoding: {!r}".format(pw))
            raise ValueError(ex)
        extra = hny_config.PASSWORD_LENGTH - len(code_g)
        code_g.extend(convert2group(0, 1, extra))
        return code_g

    def decode_rule(self, l, p):
        rhs_dict = self.G[l]
        if not rhs_dict:
            return ''
        assert '__total__' in rhs_dict, "__total__ not in {!r}, l={!r}" \
            .format(rhs_dict, l)
        p %= rhs_dict['__total__']

        if self.cal_cdf:
            if len(rhs_dict) > 1000:
                print_once(l, len(rhs_dict))
            return bin_search(list(rhs_dict.items()), p, 0, len(rhs_dict))
        for k, v in list(rhs_dict.items()):
            if p < v:
                return k
            else:
                p -= v
        print("Allas could not find.", l, p)

    def decode_l33t(self, w, iterp):
        # print("L33t:::", w, iterp)
        l = self.decode_rule('L', next(iterp))
        if l == 'Caps':
            return w.capitalize()
        elif l == 'lower':
            return w.lower()
        elif l == 'UPPER':
            return w.upper()
        else:
            nw = ''.join([self.decode_rule('L_%s' % c, next(iterp))
                          for c in w])
            return nw

    def decode_pw(self, P):
        assert len(P) == hny_config.PASSWORD_LENGTH, \
            "Not correct length to decode, Expecting {}, got {}" \
                .format(hny_config.PASSWORD_LENGTH, len(P))

        iterp = iter(P)
        plaintext = ''
        stack = ['G']
        while stack:
            lhs = stack.pop()
            rhs = self.decode_rule(lhs, next(iterp))
            if lhs in ['G', 'T', 'W', 'R', 'Y', 'D']:
                arr = rhs.split(',') if lhs != 'T' \
                    else ['T_%s' % c for c in rhs.split(',')]
                arr.reverse()
                stack.extend(arr)
            elif lhs.startswith('W'):
                rhs = self.decode_l33t(rhs, iterp)
                plaintext += rhs
            else:
                plaintext += rhs
        return plaintext

    def encode_grammar(self, G):
        """
        Encodes a sub-grammar @G under the current grammar.
        Note: Does not record the frequencies.
        G->[
        """

        vd = VaultDistPCFG()
        stack = ['G']
        code_g = []
        done = list(G.default_keys())

        while stack:
            head = stack.pop()
            assert head not in done, "head={} already in done={}".format(head, done)
            done.append(head)
            rule_dict = G[head]
            t_set = []
            for rhs in rule_dict.keys():
                if rhs != '__total__':
                    r = [x for x in self.get_actual_NonTlist(head, rhs) if x not in done + stack]
                    for x in r:
                        if x not in t_set:
                            t_set.append(x)
            t_set.reverse()
            stack.extend(t_set)
            n = len(list(rule_dict.keys())) - 1
            code_g.append(vd.encode_vault_size(head, n))

            if n < 0:
                print("Sorry I cannot encode your password ({!r})! \nPlease choose"
                      " something different, like password12!! (Just kidding.)".format((head, list(rule_dict.keys()))))
                exit(0)
            assert n == vd.decode_vault_size(head, code_g[-1]), \
                "Vault size encoding mismatch.\nhead: {!r}, code_g: {}, n: {}, decoded_vault_size: {}"\
                .format(head, code_g[-1], n, vd.decode_vault_size(head, code_g[-1]))
            code_g.extend([self.encode_rule(head, r)
                           for r in rule_dict.keys()
                           if r != '__total__'])

            # i = 0
            # for r in rule_dict.keys():
            #     if r == '__total__': continue
            #     nr = self.decode_rule(head, code_g[-n+i])
            #     print("Decoding:", code_g[-n+i], head, nr)
            #     i += 1
            #     if nr != r:
            #         print(">>> Mismatch: nr={}, r={}, code_g={}".format(nr, r, code_g[-n+i]))

        extra = hny_config.HONEY_VAULT_GRAMMAR_SIZE - len(code_g)
        code_g.extend(convert2group(0, 1, extra))
        return code_g

    def decode_grammar(self, P):
        """
        Decodes a subgrammar under self.G using the random numbers from P.
        """
        g = SubGrammar(self)
        vd = VaultDistPCFG()
        iterp = iter(P)
        stack = ['G']
        done = list(g.default_keys())
        while stack:
            head = stack.pop()
            assert head not in done, "@Head ({}) in @done. It should not!".format(head)
            done.append(head)
            p = next(iterp)
            # print "RuleSizeDecoding:", head, done
            n = vd.decode_vault_size(head, p)
            t_set = []

            for _ in range(n):
                p = next(iterp)
                rhs = self.decode_rule(head, p)
                if rhs != '__totoal__':
                    r = [y for y in self.get_actual_NonTlist(head, rhs) if y not in done + stack]
                    for y in r:
                        if y not in t_set:
                            t_set.append(y)
                else:
                    print(">>>>> __total__ should not be in the encoded grammar. Something is wrong!")
                g.add_rule(head, rhs)
            t_set.reverse()
            stack.extend(t_set)
        g.finalize()  # fixes the freq and some other book keepings
        return g

    def __getitem__(self, l):
        return self.G[l]

    def __contains__(self, k):
        return k in self.G

    def is_grammar(self):
        return bool(self.G['G'])

    def __str__(self):
        return json.dumps(self.G['G'], indent=2)

    def nonterminals(self):
        return list(self.G.keys())

        # def __nonzero__(self):
        #     return bool(self.G['G'])
        # __bool__ = __nonzero__


######################### END of TrainedGrammar class ################
######################################################################
######################### BEGIN SubGrammar class #####################


class SubGrammar(TrainedGrammar):
    def __init__(self, base_pcfg):
        self.cal_cdf = False
        R = RuleSet()
        self.base_pcfg = base_pcfg
        default_keys = []
        # default keys
        R.update_set(RuleSet(d={'L': self.base_pcfg['L']}))  # L
        default_keys.append('L')
        for c in string.ascii_lowercase:  # L_*
            x = 'L_%s' % c
            default_keys.append(x)
            R.update_set(RuleSet(d={x: self.base_pcfg[x]}))
        for k, v in list(self.base_pcfg['G'].items()):
            if k.endswith(',G'):  # W1, D1, Y1
                R.G['G'][k] = v  # W1 <-- W1,G
                R.G['G'][k[:-2]] = self.base_pcfg['G'][k[:-2]]
                default_keys.extend([k, k[:-2]])
                R.update_set(RuleSet(d={k[:-2]: self.base_pcfg[k[:-2]]}))

        self._default_keys = set(default_keys)
        self.R = R
        self.G = R.G
        self.date = Date()
        self.freeze = False

    def add_rule(self, l, r):
        if self.freeze:
            print("Warning! Please defreeze the grammar before adding")
        self.R.add_rule(l, r)

    def finalize(self):
        self.fix_freq()
        self.NonT_set = [x for x in list(self.G.keys()) if x.find('_') < 0]  # + list('Yymd')
        self.G = self.R.G
        Wlist = [x
                 for k, v in list(self.G.items())
                 for x in v
                 if k.startswith('W')]
        self.Wdawg = IntDAWG(Wlist)
        for k, v in list(self.G.items()):
            if '__total__' not in v:
                print('__total__ should be there in the keys!!. I am adding one.')
                v['__total__'] = sum(v.values())

        if 'T' in self.G:
            self.date = Date(T_rules=[x
                                      for x in list(self.G['T'].keys())
                                      if x != '__total__'])
        self.freeze = True

    def reset(self):
        for k, v in list(self.G.items()):
            if '__total__' in v:
                del v['__total__']
        self.freeze = False

    def add_some_extra_rules(self):
        for k, v in list(self.R.items()):
            pass

    def update_grammar(self, *args):
        self.reset()
        for pw in args:
            pw = pw.replace('\\', '')
            self.R.update_set(self.base_pcfg.rule_set(pw))
        self.finalize()

    def fix_freq(self):
        for l, v in list(self.R.items()):
            s = 0
            for r in v:
                if r != '__total__':
                    v[r] = self.base_pcfg.get_freq(l, r)
                    s += v[r]
            v['__total__'] = s

    def default_keys(self):
        return self._default_keys

    def __str__(self):
        return str(self.R)

    def __eq__(self, newG):
        return self.G == newG.G


################################################################################
## VaultDist PCFG
################################################################################

MAX_ALLOWED = 20  # per rule
VAULT_DIST_FILE = hny_config.GRAMMAR_DIR + 'vault_dist.cfg'


class VaultDistPCFG:
    def __init__(self):
        self.G = json.load(open_(VAULT_DIST_FILE),
                           object_pairs_hook=OrderedDict)
        # Add dummy entries for new non-terminals now
        # TODO: Learn them by vault analysis. 
        # uniformly distribute these values between 1 and 30
        use_ful = 5
        for k in ['W', 'D', 'Y', 'R', 'T']:
            self.G[k] = OrderedDict(zip(
                (str(x+1) for x in range(MAX_ALLOWED + 1)),
                [100] * use_ful + [5] * (MAX_ALLOWED - use_ful))
            )

        for k, v in list(self.G.items()):
            v['__total__'] = sum(v.values())

            # print json.dumps(self.G, indent=2)

    def encode_vault_size(self, lhs, n):
        v = self.G.get(lhs, {})
        n = str(n)
        try:
            i = list(v.keys()).index(n)
            t_v = list(v.values())
            x = sum(t_v[:i])
            y = x + t_v[i]
            return convert2group(random.randint(x, y - 1),
                                 v['__total__'])
        except ValueError:
            return convert2group(0, v['__total__'])

    def decode_vault_size(self, lhs, cf):
        assert not lhs.startswith('L')
        assert lhs in self.G, "lhs={} must be in G. I cannot find it in\nG.keys()={}" \
            .format(lhs, list(self.G.keys()))
        cf %= self.G[lhs]['__total__']
        if cf == 0:
            print_err("Grammar of size 0!!!!\nI don't think the decryption will "
                      "be right after this. I am sorry. Argument: (lhs: {}, cf: {})".format(lhs, cf))
        i = getIndex(cf, list(self.G[lhs].values()))
        return i + 1


if __name__ == '__main__':
    tg = TrainedGrammar()
    if sys.argv[1] == '-encode':
        code_g = tg.encode_pw(sys.argv[2])
        print(code_g)
        print(tg.decode_pw(code_g))
    elif sys.argv[1] == '-vault':
        g = SubGrammar(tg, sys.argv[2:])
        print(g)
    elif sys.argv[1] == '-parse':
        print('Parse', tg.parse(sys.argv[2]))
    elif sys.argv[1] == '-ptree':
        pw = sys.argv[2]
        pt = tg.l_parse_tree(pw)
        print('Parse Tree for {}\n{}\nSize: {}'.format(pw, pt, len(pt)))
        print('Get_all_matches: ', tg.get_all_matches(pw))