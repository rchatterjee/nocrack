from honey_enc import *
from buildPCFG import *
from Crypto.Cipher import DES3
from Crypto.Hash import SHA256
isModified = False;

def loadAndModifyGrammar( mp ):
    grammar, trie = loadDicAndTrie ( 'data/grammar_yahoo-withcount.hny.bz2', 'data/trie_yahoo-withcount.hny.bz2');
    isModified = True;
    convertToPDF(grammar)
    pushWordIntoGrammar(grammar, mp, 100);
    convertToCDF(grammar)
    P,W,T = findPattern(mp)
    trie_t = marisa_trie.Trie(trie.keys() + W)
    return grammar, trie_t

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
        plaintext = struct.pack("%sf" % len(plaintext), *plaintext)
        c = des3.encrypt(plaintext) 
        ret.append(c)
    return ret

def VaultDecrypt( v_ciphertexts, mp):
    iv = '01234567'
    des3 = DES3.new(hash_mp(mp), DES3.MODE_CFB, iv)
    return  VaultDecode([des3.decrypt(ciphertext) for ciphertext in v_ciphertexts ], mp)

def VaultEncode(vault, mp, grammar=None, trie=None):
    if not isModified or not grammar or not trie: grammar, trie = loadAndModifyGrammar(mp)
    return [ Encode(v, trie, grammar) for v in vault ]

def VaultDecode(cipher, mp, grammar=None):
    if not isModified: grammar, trie = loadAndModifyGrammar(mp)
    return [ Decode(c, grammar) for c in cipher]

def testRandomDecoding(grammar):
    mp = "rahulc"
    grammar, trie = loadAndModifyGrammar ( mp);
    
    return None;


def main():
    Vault = """
google.com <> querty
fb.com <> monkey@123
uwcu.com <> sensible@123
"""
    vault = [x.split('<>')[1].strip() for x in Vault.split('\n') if x]
    mp = "rahulc12"
    print vault
    # grammar, trie = loadAndModifyGrammar (mp)
    cipher = VaultEncrypt(vault, mp);
    print [c.encode('hex') for c in cipher]
    print VaultDecrypt(cipher,'123!@#')


if __name__ == "__main__":
    main();

