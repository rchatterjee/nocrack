#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.
"""

import sys, os, math
from io import BytesIO
import struct
from buildPCFG import whatchar, readPCFG, getfilenames, findPattern
from buildPCFG import EPSILON, GRAMMAR_R
from honey_enc import loadDicAndTrie
#from loadDic import break_into_words
import random, marisa_trie
import bz2 

Tmax = 17663097; 
#a,b = getfilenames('rockyou-withcount')
#grammar, trie = loadDicAndTrie( a, b )
f = bz2.BZ2File('rockYouPasswords/rockyou-withcount.txt.bz2')
G = {}
totC, N = 0, 0
for n,line in enumerate(f):
    if n>1e6: break
    line = line.strip().split()
    w,c = ' '.join(line[1:]), int(line[0])
    totC += c*(n+1)
    N += c
    if N>Tmax/4: print n+1; Tmax *= 2
    P,W,T = findPattern( w )
    key = ','.join(["%s" %x for x in P]);
    try:
        G[key][0].append((w,c));
        G[key][1] += c
    except KeyError:
        G[key] = [[(w,c)], c]

print 'Normal Approach:', N, totC, float(totC)/N

totCp, totN = 0, 0;
totBroken = 0
for p in G:
    G[p][0].sort(key=lambda x: x[1], reverse=True)
    Cp, N = 0, 0;
    s = sum([x[1] for x in G[p][0][:150]])
    totBroken += s;
    for i,c in enumerate(G[p][0]):
        Cp += c[1]*(i+1)
        totN  += c[1]
    G[p].append(float(Cp)/G[p][1])
    totCp += Cp

print 'TotalBroken in 10 tries:', totBroken, float(totBroken)/totN
print 'Kamouflage Flaws:', totN,  totCp, float(totCp)/totN 
#writePCFG(G, "Kamouflage_analysis.txt.bz2")
print "Prob:", float(totCp)/totN



