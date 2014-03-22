#!/usr/bin/python
import sys
import difflib
sys.path.append('../')
from mangle import *

base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(sys.argv[2])
T = Tokenizer(base_dictionary, tweak_fl)

p = {}
for l in open(sys.argv[1]).readlines():
    l = l.strip().split(',')
    if len(l) < 6 : continue
    try: 
        if not l[3].decode('ascii'): continue
    except: continue; # not ascii hence return
    try: p[l[5]].append(l[3])
    except: p[l[5]] = [l[3]]

for i,v in p.items():
    uniq_list = [T.tokenize(x) for x in set(v)]
    for u in uniq_list:
        for x in u: print x
    
