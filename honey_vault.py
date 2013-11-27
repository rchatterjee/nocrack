from honey_enc import *
from buildPCFG import *

def modifyGrammar( mp, grammar, trie ):
    convertToPDF(grammar)
    pushWordIntoGrammar(grammar, mp, 100);
    convertToCDF(grammar)

def vaultEncode(vault, mp, grammar, trie):
    return [ Encode(v, trie, grammar) for v in vault ]

def vaultDecode(cipher, mp, grammar, trie):
    
    return [ Decode(struct.pack("%sf" % len(c), *c), grammar) for c in  in cipher]

def main():
    vault = """
google.com <> rahulc12
fb.com <> monkey@123
uwcu.com <> sensible@123
"""
    mp = "rahulc12"

    grammar, trie = loadDicAndTrie ( 'data/grammar_yahoo-withcount.hny.bz2', 'data/trie_yahoo-withcount.hny.bz2');   
    print vaultEncode(vault, mp, grammar, trie);
    print vaultDecode(vault, grammar)
if __name__ == "__main__":
    main();

