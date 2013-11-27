from honey_enc import *
from buildPCFG import *

def vaultEncode(vault, mp, grammar, trie):
    pushWordIntoGrammar(grammar, mp, 100);
    return [ Encode(v, trie, grammar) for v in vault ]

def vaultDecode(cipher, mp, grammar, trie):
    
def main():
    vault = """
google.com <> rahulc12
fb.com <> monkey@123
uwcu.com <> sensible@123
"""
    mp = "rahulc12"

    grammar, trie = loadDicAndTrie ( 'data/grammar_yahoo-withcount.hny.bz2', 'data/trie_yahoo-withcount.hny.bz2');   
    print vaultEncrypt(vault, mp, grammar, trie);

if __name__ == "__main__":
    main();

