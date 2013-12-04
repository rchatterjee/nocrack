from honey_enc import *
from buildPCFG import *
from Crypto.Cipher import DES3
from Crypto.Hash import SHA256
isModified = False;

grammar = None
trie = None
def loadAndModifyGrammar( mp ):
    global isModified, grammar, trie
    if isModified: return grammar, trie
    grammar, trie_t = loadDicAndTrie ( 'data/grammar_combined-withcout.hny.bz2',  'data/trie_combined-withcout.hny.bz2' )
    #grammar, trie = loadDicAndTrie ( 'data/grammar_hotmail-withcount.hny.bz2',  'data/trie_hotmail-withcount.hny.bz2' )    
    isModified = True;
    # convertToPDF(grammar)
    # pushWordIntoGrammar(grammar, mp, 10);
    # convertToCDF(grammar)
    # P,W,T = findPattern(mp)
    # trie_t = marisa_trie.Trie(trie.keys() + W)
    return grammar, trie

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp);
    return h.hexdigest()[:16]

def VaultEncrypt( v_plaintexts, mp ):
    iv = '01234567'
    v_plaintexts = VaultEncode(v_plaintexts, mp)
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    ret = []
    for plaintext in v_plaintexts:
        plaintext = struct.pack("%sI" % len(plaintext), *plaintext)
        c = des3.encrypt(plaintext) 
        ret.append(c)
    return ret

def VaultDecrypt( v_ciphertexts, mp, grammar=None):
    iv = '01234567'
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    return  VaultDecode([des3.decrypt(ciphertext) for ciphertext in v_ciphertexts ], mp, grammar)

def VaultEncode(vault, mp, grammar=None, trie=None):
    if not isModified or not grammar or not trie: grammar, trie = loadAndModifyGrammar(mp)
    return [ Encode(v, trie, grammar) for v in vault ]

def VaultDecode(cipher, mp, grammar=None):
    grammar, trie = loadAndModifyGrammar(mp)
    return [ Decode(c, grammar) for c in cipher]

def testRandomDecoding( vault_cipher ):
    print "Trying to randomly decrypt:"
    grammar, trie = loadDicAndTrie ( 'data/grammar_combined-withcout.hny.bz2',  'data/trie_combined-withcout.hny.bz2' )
    with bz2.BZ2File('../PasswordDictionary/passwords/elitehacker-withcount.txt.bz2') as f:
        count = 100;
        for line in f[:100]:
            mp = line.strip().split()[1]
            # grammar, trie = loadAndModifyGrammar ( mp );
            print mp, '-->', VaultDecrypt( vault_cipher, mp, grammar )
            
def main():
    Vault = """
google.com <> querty
fb.com <> monkey@123
uwcu.com <> sensible@123
"""
    vault = [x.split('<>')[1].strip() for x in Vault.split('\n') if x]
    vault = 'abc123 iloveyou password tree@123 (NH4)2Cr2O7' .split()
    mp = "random"
    print vault
    # grammar, trie = loadAndModifyGrammar (mp)
    cipher = VaultEncrypt(vault, mp);
    print [c.encode('hex') for c in cipher]
    print VaultDecrypt( cipher, mp )
    # testRandomDecoding( cipher )

if __name__ == "__main__":
    main();

