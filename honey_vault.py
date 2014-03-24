from honey_enc import *
from buildPCFG import *
from Crypto.Cipher import DES3
from Crypto.Hash import SHA256
import random
FREQ = 0
grammar = None
trie = None


def loadandmodifygrammar(mp):
    #grammar, trie_t = loadDicAndTrie('data/grammar_combined-withcout.hny.bz2',
    #                  'data/trie_combined-withcout.hny.bz2')
    global grammar, trie
    if not grammar or not trie:
        grammar, trie = loadDicAndTrie('data/grammar_rockyou-withcount.hny.bz2', 'data/trie_rockyou-withcount.hny.bz2')
    if not FREQ:
        ModifyGrammar(grammar, mp, FREQ);
        P, W, T = findPattern(mp)
        trie_t = marisa_trie.Trie(trie.keys() + W)
    return grammar, trie

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]


def vault_encrypt(v_plaintexts, mp):
    iv = '01234567'
    vault_code = vault_encode(v_plaintexts, mp)
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    # plaintext= staruct.pack("%sI" % len(vault_code), *vault_code)
    c = des3.encrypt(vault_code)
    return c


def vault_decrypt(v_ciphertexts, mp, vault_size):
    iv = '01234567'
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    return vault_decode(des3.decrypt(v_ciphertexts), mp, vault_size)


def vault_encode(vault, mp):
    #print vault
    S = Scanner()
    dte = DTE()
    G = Grammar()
    G.G = {}
    for v in set(vault): # bring in Vault distribution
        T, W, U = S.tokenize(v, True)
        rule = ','.join(T)
        f = dte.get_freq('G', rule)
        G.addRule_lite('G', rule, f[0], f[1], True )
        for (l,r) in zip(T,W):
            f = dte.get_freq(l, r)
            G.addRule_lite(l, r, f[0], f[1], True )
    #print "SUB_GRAMMAR", G.G
    #print "-"*30
    stack = ['G']
    code_g = []
    while stack:
        head = stack.pop()
        rule = G[head][0]
        t_set = []
        t_set = list(set([ x for i,r in enumerate(rule) for x in r.split(',') if G[head][1][i][1] is NONTERMINAL ]))
        t_set.reverse()
        stack.extend(t_set)
        n = len(rule)
        code_g.append(convert2group(sum(VAULT_SIZE_TO_FREQ[:n]), VAULT_SIZE_TO_FREQ[-1]))
        code_g.extend([dte.encode(head, r) for r in rule])
        
    #print code_g

    dte.update_dte_for_vault(G)
    # n = len(vault)
    # code_g.append(convert2group(n, MAX_VAULT_SIZE)) # this is public info
    for v in vault: # bring in Vault distribution
        T, W, U = S.tokenize(v, True)
        rule = ','.join(T)
        code_g.append(dte.encode('G', rule))
        for i,p in enumerate(T):
            t=dte.encode(p, W[i])
            if t==-1: 
                print "Sorry boss! iQuit!"
                exit(0)
                # return Encode_spcl(m, grammar)
            code_g.append( t )
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(code_g);
        code_g.extend( [ convert2group(0,1) for x in range(extra) ] )
    c_struct = struct.pack('%sI' % len(code_g), *code_g )
    return c_struct
#    return [ Encode(v, trie, grammar) for v in vault ]


def vault_decode(cipher, mp, vault_size):
    dte = DTE()
    t = len( cipher );
    P = struct.unpack('%sI'%(t/4), cipher )
    # first decode the grammar part
    G=Grammar()
    G.G = {}
    iterp = iter(P)
    stack = ['G']
    while stack:
        head = stack.pop()
        p = iterp.next()
        n = getIndex(p, VAULT_SIZE_TO_FREQ)
        #print p, p%VAULT_SIZE_TO_FREQ[-1], VAULT_SIZE_TO_FREQ
        NonTlist = []
        for x in range(n):
            r = dte.decode(head, iterp.next(), freq_also=True)
            G.addRule_lite(head, r[0], r[1], r[2], True)
            if r[2]==NONTERMINAL: NonTlist.extend(r[0].split(','))
            # print 'Grammar:', G
        t_set = list(set(NonTlist))
        t_set.reverse()
        stack.extend(t_set)
    #print "DecodedGrammar", G
    dte.update_dte_for_vault(G)
    pass_vault = []
    for i in range(vault_size):
        plaintext = '';
        stack = ['G']
        while stack:
            head = stack.pop()
            g = dte.decode(head, iterp.next())
            if g[1]==NONTERMINAL:
                arr = g[0].split(',')
                arr.reverse()
                stack.extend(arr)
            else:
                plaintext += g[0]
        pass_vault.append(plaintext)
    return pass_vault;

                           


#    return [Decode(c, grammar) for c in cipher]


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


def main():
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


if __name__ == "__main__":
    main();

