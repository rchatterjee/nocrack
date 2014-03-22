# The following dictionaries should be provided to buildcfg.py
# 1: base dictionary //only character words will be considered
# 2: tweak set file
# 3: dictionary with count // PCFG will be built over this
# 4: output PCFG file name/path
# 5: output Trie file name/path

# empty lines and line beginning with '#' will be discarded
# exact dicionary path should be given.


DICTIONARY_SOURCE_FILE = "../PasswordDictionary/passwords/combined-withcout.txt.bz2"
PASSWORD_LEAK   = "../PasswordDictionary/passwords/rockyou-withcount.txt.bz2"


#DIC_TRIE_FILE = 'data/english.tri'
DIC_TRIE_FILE = 'Dictionary_Store/dictionary.tri'
STANDARD_DIC_FILE = "Dictionary_Store/standard_english.tri"

GRAMMAR_OUTPUT_FILE = "./data/combined.gmr.bz2"
GRAMMAR_INPUT_FILE  = "./data/combined.tri.bz2"
HANDGRAMMAR_FILE    = "./data/grammar.txt"
