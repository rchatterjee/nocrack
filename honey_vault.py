from honey_enc import *
from buildPCFG import *
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random

# def loadandmodifygrammar(mp):
#     #grammar, trie_t = loadDicAndTrie('data/grammar_combined-withcout.hny.bz2',
#     #                  'data/trie_combined-withcout.hny.bz2')
#     global grammar, trie
#     if not grammar or not trie:
#         grammar, trie = loadDicAndTrie('data/grammar_rockyou-withcount.hny.bz2', 'data/trie_rockyou-withcount.hny.bz2')
#     if not FREQ:
#         ModifyGrammar(grammar, mp, FREQ);
#         P, W, T = findPattern(mp)
#         trie_t = marisa_trie.Trie(trie.keys() + W)
#     return grammar, trie

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]

def do_crypto_setup(mp):
    salt = b'asombhob'
    key = PBKDF1(mp, salt, 16, 100, SHA256)
    ctr = Counter.new(128, initial_value=long(254))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes 


def vault_encrypt(v_plaintexts, mp):
    aes = do_crypto_setup(mp)
    return aes.encrypt(vault_encode(v_plaintexts, mp))


def vault_decrypt(v_ciphertexts, mp, vault_size):
    aes = do_crypto_setup(mp)
    return vault_decode(aes.decrypt(v_ciphertexts), mp, vault_size)


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


def main():
        if len(sys.argv)<5 or sys.argv[0] in ['-h', '--help']:
            print '''Taste the HoneyVault1.1 - a New Password Encrypting paradigm! 
|| Encrypt with confidence ||
--encode vault_plain.txt masterpassword vault_cipher.txt
--decode vault_cipher.txt masterpassword stdout
        '''
        else:
            f1 = sys.argv[2]
            mp = sys.argv[3]
            f2 = sys.argv[4]
            if sys.argv[1] == '--encode': 
                vault = [ l.strip().split(',')[2] for l in open(f1) if l[0] != '#']
                cipher = vault_encrypt( vault, mp)
                with open(f2,'wb') as outf: 
                    n = len(vault)
                    outf.write(struct.pack('<I', n))
                    outf.write(cipher)
                print "Your Vault is encrypted! Now you can delte the plaintext vault text."
            elif sys.argv[1] == '--decode':
                dt = open(f1, 'rb').read()
                n = struct.unpack('<I', dt[:4])[0]
                vault = vault_decrypt( dt[4:], mp, n )
                print vault
            else: print "Sorry Anthofila! Command not recognised."
            
if __name__ == "__main__":
    main();

