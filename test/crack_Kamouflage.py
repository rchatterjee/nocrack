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


def testRandomDecoding(vault_cipher, n):
    print "Trying to randomly decrypt:"
    #grammar, trie = loadDicAndTrie ( 'data/grammar_combined-withcout.hny.bz2',  'data/trie_combined-withcout.hny.bz2' )
    f = open_('/u/r/c/rchat/Acads/AdvanceComputerSecurity/PasswordDictionary/passwords/500-worst-passwords.txt.bz2')
    count = 1000;
    # for mp in ['rahul', 'abc123', 'password@123', 'thisismypassword', 'whatdFuck'] :
    #     # mp = line.strip().split()[1]
    #     ModifyGrammar(grammar, mp, FREQ);
    #     # grammar, trie = loadandmodifygrammar ( mp );
    #     print mp, '-->', VaultDecrypt( vault_cipher, mp, grammar )
    #     ModifyGrammar(grammar, mp, -FREQ)
    
    for i, line in enumerate(f):
        if random.random() < 0.8: continue;
        if i > count: break;
        mp = line.strip().split()[0]
        # ModifyGrammar(grammar, mp, FREQ);
# grammar, trie = loadandmodifygrammar ( mp );
        #print "\\textbf{%s} ~$\\rightarrow$ & \\texttt{\{%s\}} \\\\" % (
        #    mp, ', '.join(['%s' % x for x in vault_decrypt(vault_cipher, mp, n)]))
        print mp, vault_decrypt(vault_cipher, mp, n)
        #ModifyGrammar(grammar, mp, -FREQ)


def test1():
    global grammar, trie
    Vault = """
fb.com <> 123456
bebo.com <> cutiepie
youtube.com <> kevin
uwcu.com <> princess
google.com <> rockyou
yahoo.com <> password12
"""
    vault = [x.split('<>')[1].strip() for x in Vault.split('\n') if x]
    #vault = 'abc123 iloveyou password tree@123 (NH4)2Cr2O7' .split()
    # vault = [ x.strip() for x in bz2.BZ2File('../PasswordDictionary/passwords/500-worst-passwords.txt.bz2').readlines()[:25] ]

    mp = "random"
    n = len(vault)
    # print vault
    #  grammar, trie = loadandmodifygrammar(mp)
    cipher = vault_encrypt(vault, mp);
    # cipher2 = vaultencrypt(vault, mp);
    # print [len(c.encode('hex')) for c in cipher]
    print vault_decrypt( cipher, mp, n )
    #ModifyGrammar( grammar, mp, -FREQ);
    testRandomDecoding(cipher, n)

print 'TotalBroken in 10 tries:', totBroken, float(totBroken)/totN
print 'Kamouflage Flaws:', totN,  totCp, float(totCp)/totN 
#writePCFG(G, "Kamouflage_analysis.txt.bz2")
print "Prob:", float(totCp)/totN



