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
DICTIONARY_DAWG = 'Dictionary_Store/dictionary1.1.dawg'
STANDARD_DIC_FILE = "Dictionary_Store/standard_english.tri"

GRAMMAR_OUTPUT_FILE = "./data/combined.gmr.bz2"
GRAMMAR_INPUT_FILE  = "./data/combined.tri.bz2"
HANDGRAMMAR_FILE    = "./data/grammar.txt"

GRAMMAR_DIR = './Grammar/'

# Dont change 
EPSILON = '|_|'
GRAMMAR_R = 0
MEMLIMMIT = 1024  # 1024 MB, 1GB
MIN_COUNT = 30
PASSWORD_LENGTH = 50
DEBUG = 1 # 1 S --> we are not getting combined rule like L3,D4 
NONTERMINAL = 1
TERMINAL = 1 - NONTERMINAL



# vault size to number map
# we shall learn it later
VAULT_SIZE_TO_FREQ = [ 0, 6, 10, 13, 8, 9, 12, 15, 12, 3, 2, 1, 4, 1, 1, 1, 1]
VAULT_SIZE_TO_FREQ.append(sum(VAULT_SIZE_TO_FREQ))
MAX_VAULT_SIZE = 50

HONEY_VAULT_GRAMMAR_SIZE  = 400   # 400 bytes, 100 integers/rules
HONEY_VAULT_S1 = 1000
HONEY_VAULT_S2 = 1000
HONEY_VAULT_STORAGE_SIZE = HONEY_VAULT_S1 + HONEY_VAULT_S2
HONEY_VAULT_ENCODING_SIZE = HONEY_VAULT_GRAMMAR_SIZE + HONEY_VAULT_STORAGE_SIZE * PASSWORD_LENGTH

SECURITY_PARAM = 16
SECURITY_PARAM_IN_BASE64 = (SECURITY_PARAM * 4)/3 + 1

# Static domain mapping list
STATIC_DOMAIN_LIST = 'static_domain_map.txt'
