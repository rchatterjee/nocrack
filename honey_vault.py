from honey_enc import *
from buildPCFG import *
from Crypto.Cipher import DES3
from Crypto.Hash import SHA256

FREQ = 0
grammar = None
trie = None

def loadAndModifyGrammar( mp ):
    # grammar, trie_t = loadDicAndTrie ( 'data/grammar_combined-withcout.hny.bz2',  'data/trie_combined-withcout.hny.bz2' )
    global grammar, trie
    if not grammar or not trie:
        grammar, trie = loadDicAndTrie ( 'data/grammar_rockyou-withcount.hny.bz2',  'data/trie_rockyou-withcount.hny.bz2' )    
    if not FREQ:
        ModifyGrammar(grammar, mp, FREQ);
        P,W,T = findPattern(mp)
        trie_t = marisa_trie.Trie(trie.keys() + W)
    return grammar, trie

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp);
    return h.hexdigest()[:16]

def VaultEncrypt( v_plaintexts, mp ):
    iv = '01234567'
    v_plaintexts = VaultEncode(v_plaintexts, mp, grammar, trie)
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    ret = []
    for plaintext in v_plaintexts:
        plaintext = struct.pack("%sI" % len(plaintext), *plaintext)
        c = des3.encrypt(plaintext) 
        ret.append(c)
    return ret

def VaultDecrypt( v_ciphertexts, mp, grammar):
    iv = '01234567'
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    return  VaultDecode([des3.decrypt(ciphertext) for ciphertext in v_ciphertexts ], mp, grammar)

def VaultEncode(vault, mp, grammar, trie):
    return [ Encode(v, trie, grammar) for v in vault ]

def VaultDecode(cipher, mp, grammar):
    return [ Decode(c, grammar) for c in cipher]

def testRandomDecoding( vault_cipher ):
    print "Trying to randomly decrypt:"
    #grammar, trie = loadDicAndTrie ( 'data/grammar_combined-withcout.hny.bz2',  'data/trie_combined-withcout.hny.bz2' )
    with bz2.BZ2File('../PasswordDictionary/passwords/500-worst-passwords.txt.bz2') as f:
        count = 500;
        # for mp in ['rahul', 'abc123', 'password@123', 'thisismypassword', 'whatdFuck'] :
        #     # mp = line.strip().split()[1]
        #     ModifyGrammar(grammar, mp, FREQ);
        #     # grammar, trie = loadAndModifyGrammar ( mp );
        #     print mp, '-->', VaultDecrypt( vault_cipher, mp, grammar )
        #     ModifyGrammar(grammar, mp, -FREQ)

        for i,line in enumerate(f):
            if random.random()<0.8: continue;
            if i>count: break;
            mp = line.strip().split()[0]
            ModifyGrammar(grammar, mp, FREQ);
            # grammar, trie = loadAndModifyGrammar ( mp );
            print mp, '-->', ', '.join( ['%s' % x for x in VaultDecrypt( vault_cipher, mp, grammar) ] )
            ModifyGrammar(grammar, mp, -FREQ)

def main():
    global grammar, trie
    Vault = """
google.com <> querty
fb.com <> monkey@123
uwcu.com <> sensible@123
"""
    vault = [x.split('<>')[1].strip() for x in Vault.split('\n') if x]
    #vault = 'abc123 iloveyou password tree@123 (NH4)2Cr2O7' .split()
    vault = [ x.strip() for x in bz2.BZ2File('../PasswordDictionary/passwords/500-worst-passwords.txt.bz2').readlines()[:25] ]

    mp = "random"
    # print vault
    grammar, trie = loadAndModifyGrammar (mp)
    #cipher1 = VaultEncrypt(vault, mp);
    # cipher2 = VaultEncrypt(vault, mp);
    #print [len(c.encode('hex')) for c in cipher1]
    # VaultDecrypt( cipher1, mp, grammar )
    #ModifyGrammar( grammar, mp, -FREQ);
    # testRandomDecoding( cipher )
    
if __name__ == "__main__":
    main();

