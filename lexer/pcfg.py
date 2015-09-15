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

import os, sys, string
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG, DAWG
import marisa_trie
import struct, json, bz2, re
from lexer_helper import Date, KeyBoard, RuleSet, ParseTree
from helper.helper import open_, getIndex, convert2group, bin_search, print_once, random
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from honeyvault_config import MEMLIMMIT, GRAMMAR_DIR
from collections import OrderedDict, defaultdict
from pprint import pprint
import resource  # For checking memory usage
from lexer import NonT_L, get_nont_class
import operator

grammar_file = GRAMMAR_DIR + '/grammar.cfg.bz2'


class TrainedGrammar(object):
    l33t_replaces = DAWG.compile_replaces({
            '3':'e', '4':'a', '@':'a',
            '$':'s', '0':'o', '1':'i',
            'z':'s'
            })

    def __init__(self, g_file=grammar_file, cal_cdf=False):
        self.cal_cdf = cal_cdf
        self.load(g_file)
        self.NonT_set = filter(lambda x: x.find('_') < 0,  
                               self.G.keys())

    def load(self, filename):
        self.G = json.load(open_(filename),
                           object_pairs_hook=OrderedDict)

        """
        An effort to update the grammar structure. Will fix the original
        grammar later. 
        Grammar shouldlook like:
          G -> W,G | D,G | Y,G | R,G | K,G | .. | W | D | Y | R | K
          W -> W1 | W2 | W3 ..
          D -> D1 | D2 .. 
        """
        new_start = defaultdict(int)
        new_g = defaultdict(dict)
        for ntkey,v in self.G['G'].items():
            ntkey = ntkey.split(',')
            for i,k in enumerate(ntkey):
                if len(k)>1:
                    new_g[k[0]][k] = new_g[k[0]].get(k, 0) + v
                if i==len(ntkey)-1:
                    new_non_t = ntkey[-1][0]
                else:
                    new_non_t = k[0]+',G'                    
                new_start[new_non_t] += v

        for k in new_g.keys():
            v = new_g[k]
            new_g[k] = OrderedDict(sorted(v.items(), key=operator.itemgetter(0)))

        self.G.update(new_g)
        self.G['G'] = OrderedDict(sorted(new_start.items(), key=operator.itemgetter(0)))
        
        # Calculate CDF for faster processing
        for k,v in self.G.items():
            if self.cal_cdf:
                print_err("Calculating CDF!")
                lf = 0
                for l,f in v.items():
                    v[l] += lf
                    lf += f
                v['__total__'] = lf
            else:
                v['__total__'] = sum(v.values())

        # Create dawg/trie of the Wlist items for fast retrieval
        Wlist = [x 
                 for k,v in self.G.items()
                 for x in v
                 if k.startswith('W')]
        self.date = Date()
        self.Wdawg = IntDAWG(Wlist)

    def get_prob(self, l, r):
        f = self.G.get(l, {}).get(r, 0)
        return max(float(f)/self.G[l]['__total__'], 0.0)

    def isNonTerm(self, lhs): # this means given lhs, rhs will be in NonT 
        return lhs in self.NonT_set
        
    def get_actual_NonTlist(self, lhs, rhs):
        if lhs == 'G':
            return rhs.split(',')
        elif lhs == 'T':
            return ['%s_%s' % (lhs,c)
                    for c in (rhs.split(',') if ',' in rhs
                              else rhs)]
        elif lhs == 'L':
            return ['%s_%s' % (lhs,c)
                    for c in rhs]
        elif lhs in ['W', 'D', 'Y', 'R', 'K']:
            return [rhs]
        else:
            return []

    def get_freq(self, l, r):
        return self.G.get(l, {}).get(r, 0)

    def get_W_rule(self, word):
        w = unicode(word.lower())
        k = self.Wdawg.similar_keys(w, self.l33t_replaces)
        if k:
            k = k[0]
            L = NonT_L(k, word)
            sym = 'W%s' % get_nont_class('W', k)
            return (sym, [(k, L)], self.get_prob(sym, k))

    def get_T_rule(self, word):
        T = self.date.IsDate(word)
        if T:
            p = 10**(len(word)-8)
            for r in T.tree:
                p *= self.get_prob(*r)
            p *= self.get_prob(*(T.get_rule()))
            return ('T', [(word, T)], p)

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
                if f>0:
                    rules.append((nt, [(word)], float(f)/self.G[nt]['__total__']))
        rules = filter(lambda x: x and x[-1], rules)
        if rules:
            return max(rules, key=lambda x: x[-1])

    def join(self, r, s):
        not_startswith_L_T = lambda x: x and \
            not (x[0].startswith('L_') or x[0].startswith('T_'))
        if not_startswith_L_T(s) and not_startswith_L_T(r):
            k = ','.join([r[0],s[0]])
            p = r[-1] * s[-1]
            a = r[1] + s[1]
            return (k, a, p)

    def random_parse(self, word, try_num=3):
        """
        Returns a random parse of the word following the grammar.
        """
        # First- rejection sampling, most inefficient version
        # break the word into random parts and then see if that parse exist
        print "\n^^^^^^^^^^^_______________^^^^^^^^^^^^^^"
        if try_num<0:
            print "I am very sorry. I could not parse this :(!!"
            return None
        # NO IDEA HOW TO randomly pick a parse tree!! @@TODO

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
        
    def l_parse_tree(self, word): # leftmost parse-tree
        pt = ParseTree()
        p = self.parse(word)
        if not p:
            print "Failing at ", word.encode('utf-8')
            return pt
        #pt.add_rule(('G', p[0]))  --- OLD ONE, adding new rules
        for i, elem in enumerate(zip(p[0].split(','), p[1])):
            l, each_r = elem
            # G -> WG | DG | W | D.. etc; W -> W2 | W3; D -> D3 | D5..
            new_non_t = l[0] if i==len(p[1])-1 else l[0]+',G'
            new_t = l if len(l)>1 else None
            pt.add_rule(('G', new_non_t))
            if new_t:
                pt.add_rule((l[0], new_t))

            if isinstance(each_r, basestring):
                pt.add_rule((l, each_r))
            elif l.startswith('W'):
                pt.add_rule((l, each_r[0]))
                L_parse_tree = each_r[1].parse_tree()
                pt.add_rule(L_parse_tree[0])
                if len(L_parse_tree.tree)>1:
                    pt.tree.extend(L_parse_tree[1][1])
            elif l == 'T':
                p = each_r[1]
                rule_name = ','.join([r[0].replace('T_','')
                                     for r in p])
                pt.add_rule((l, rule_name))
                pt.extend_rule(p)
            else:
                print "Something is severly wrong"
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
            i = rhs_dict.keys().index(r)
        except ValueError:
            print "{} not in the rhs_dict (l: '{}', rhs_dict: {})".format(r, l, self.G[l])
            raise ValueError
        l_pt = sum(rhs_dict.values()[:i])
        r_pt = l_pt + rhs_dict[r]
        return convert2group(random.randint(l_pt,r_pt),
                             rhs_dict['__total__'])

    def encode_pw(self, pw):
        pt = self.l_parse_tree(pw)
        try:
            code_g = [self.encode_rule(*p)
                  for p in pt]
        except ValueError:
            print "Error in encoding: \"{}\"".format(pw)
            return []
        extra = hny_config.PASSWORD_LENGTH - len(code_g);
        code_g.extend([convert2group(0,1) for x in range(extra)])
        return code_g

    def decode_rule(self, l, p):
        rhs_dict = self.G[l]
        p %= rhs_dict['__total__']
        if self.cal_cdf:
            if len(rhs_dict)>1000: print_once(l, len(rhs_dict))
            return bin_search(rhs_dict.items(), p, 0, len(rhs_dict))
        for k,v in rhs_dict.items():
            if p<v:
                return k
            else:
                p -= v
        print "Allas could not find.", l, p

    def decode_l33t(self, w, iterp):
        l = self.decode_rule('L', iterp.next())
        if l == 'Caps': return w.capitalize()
        elif l == 'lower': return w.lower()
        elif l == 'UPPER': return w.upper()
        else: 
            nw = ''.join([self.decode_rule('L_%s'%c, iterp.next())
                   for c in w])
            return nw
                
    def decode_pw(self, P):
        assert len(P) == hny_config.PASSWORD_LENGTH, \
            "Not correct length to decode, Expecting {}, got {}"\
            .format(hny_config.PASSWORD_LENGTH, len(P))
        
        iterp = iter(P)
        plaintext = '';
        stack = ['G']
        while stack:
            lhs = stack.pop()
            rhs = self.decode_rule(lhs, iterp.next())
            if lhs in ['G', 'T', 'W', 'R', 'Y', 'D']:
                arr = rhs.split(',') if lhs != 'T' \
                    else ['T_%s'% c for c in rhs.split(',')]
                arr.reverse()
                stack.extend(arr)
            elif lhs.startswith('W'):
                rhs = self.decode_l33t(rhs, iterp)
                plaintext += rhs
            else:
                plaintext += rhs
        return plaintext

    def __getitem__(self, l):
        return self.G[l]

    def __contains__(self, k):
        return k in self.G

    def is_grammar(self):
        return bool(self.G['G'])
    def __str__(self):
        return json.dumps(self.G['G'], indent=2)

    # def __nonzero__(self):
    #     return bool(self.G['G'])
    # __bool__ = __nonzero__

class SubGrammar(TrainedGrammar):
    def __init__(self, base_pcfg):
        self.cal_cdf = False
        R = RuleSet()
        self.base_pcfg = base_pcfg
        R.update_set(RuleSet(d={'L': self.base_pcfg['L']}))
        for c in string.ascii_lowercase:
            x = 'L_%s' % c
            R.update_set(RuleSet(d={x: self.base_pcfg[x]}))
        self.R = R
        self.G = R.G
        self.date = Date()
        self.freeze = False

    def add_rule(self, l, r):
        if self.freeze:
            print "Warning! Please defreeze the grammar before adding"
        self.R.add_rule(l,r)

    def finalize(self):
        self.fix_freq()
        self.NonT_set = filter(lambda x: x.find('_') < 0,  
                               self.G.keys()) #+ list('Yymd')
        self.G = self.R.G
        Wlist = [x 
                 for k,v in self.G.items()
                 for x in v
                 if k.startswith('W')]
        self.Wdawg = IntDAWG(Wlist)
        if 'T' in self.G:
            self.date = Date(T_rules=[x 
                                      for x in self.G['T'].keys()
                                      if x != '__total__'])
        self.freeze = True

    def reset(self):
        for k,v in self.G.items():
            if '__total__' in v:
                del v['__total__']
        self.freeze = False
        
    def add_some_extra_rules(self):
        for k,v in self.R.items():
            pass
            
    def update_grammar(self, *args):
        self.reset()
        for pw in args:
            pw = pw.replace('\\', '')
            self.R.update_set(self.base_pcfg.rule_set(pw))
        self.finalize()

    def fix_freq(self):
        for l,v in self.R.items():
            s = 0
            for r in v:
                if r != '__total__':
                    v[r] = self.base_pcfg.get_freq(l,r)
                    s += v[r]
            v['__total__'] = s
    
    def __str__(self):
        return str(self.R)
    
    def __eq__(self, newG):
        return self.G == newG.G

if __name__=='__main__':
    tg = TrainedGrammar()
    if sys.argv[1] == '-pw':
        code_g =  tg.encode_pw(sys.argv[2])
        print code_g
        print tg.decode_pw(code_g)
    elif sys.argv[1] == '-vault':
        g = SubGrammar(tg, sys.argv[2:])
        print g
    elif sys.argv[1] == '-parse':
        print 'Parse',  tg.parse(sys.argv[2])
    elif sys.argv[1] == '-ptree':
        print 'Parse',  tg.l_parse_tree(sys.argv[2])
