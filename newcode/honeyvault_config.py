# The following dictionaries should be provided to buildcfg.py
# 1: base dictionary //only character words will be considered
# 2: tweak set file
# 3: dictionary with count // PCFG will be built over this
# 4: output PCFG file name/path
# 5: output Trie file name/path

# empty lines and line beginning with '#' will be discarded
# exact dicionary path should be given.
import math
import os
import random


DEBUG = os.environ.get("DEBUG", False)

BASE_DIR = os.getcwd()
thisdir = os.path.dirname(os.path.abspath(__file__))

# DIC_TRIE_FILE = 'data/english.tri'
# DICTIONARY_DAWG = '{}/Dictionary_Store/dictionary1.1.dawg.gz'.format(thisdir)
# STANDARD_DIC_FILE = "{}/Dictionary_Store/standard_english.tri.gz".format(thisdir)

# GRAMMAR_OUTPUT_FILE = "{}/data/combined.gmr.bz2".format(thisdir)
# GRAMMAR_INPUT_FILE = "{}/data/combined.tri.bz2".format(thisdir)
# HANDGRAMMAR_FILE = "{}/data/grammar.txt".format(thisdir)

STATIC_DIR = os.path.join(thisdir, 'static')
TRAINED_GRAMMAR_FILE = os.path.join(STATIC_DIR, 'grammar.cfg.gz')
if DEBUG:
    TRAINED_GRAMMAR_FILE += '~orig'
VAULT_DIST_FILE = os.path.join(STATIC_DIR, 'vault_dist.cfg')


# Don't change
EPSILON = '|_|'
GRAMMAR_R = 0
MEMLIMMIT = 1024  # 1024 MB, 1GB
MIN_COUNT = 2



PRODUCTION = 1
NONTERMINAL = 1
TERMINAL = 1 - NONTERMINAL

REPR_SIZE = 4  # number of bytes to represent an integer. normally 4 bytes. But
               # we might go for higher values for better security.

MAX_INT = 256 ** REPR_SIZE  # value of maximum integer in this representation.

PASSWORD_LENGTH = 100  # length of the password encoding
HONEY_VAULT_GRAMMAR_SIZE = 500  # 400 bytes, 50 integers/rules

# This controls the size of the NoCrack vault. Refer to the Oakland 15 paper
# (NoCrack) for more details.  If you change this remember to delete
# static/vault.db to see the effect.  Need less to say, you will lose all your
# passwords. Export/import operation are on its way. (TODO: Import-Export
# functions)
HONEY_VAULT_S1 = 1000
HONEY_VAULT_S2 = 1000

HONEY_VAULT_STORAGE_SIZE = HONEY_VAULT_S1 + HONEY_VAULT_S2
# For each password there is 1 byte saying whether the password is m/c or human
# generated.  '1' --> m/c or '0' --> human generated pw.
# TODO: move it to more succinct repr, Google's protobuf!
HONEY_VAULT_MACHINE_PASS_SET_SIZE = int(math.ceil(HONEY_VAULT_STORAGE_SIZE / 8))
HONEY_VAULT_ENCODING_SIZE = HONEY_VAULT_GRAMMAR_SIZE + \
                            HONEY_VAULT_STORAGE_SIZE * PASSWORD_LENGTH
HONEY_VAULT_TOTAL_CIPHER_SIZE = HONEY_VAULT_ENCODING_SIZE + \
                                int(math.ceil(HONEY_VAULT_MACHINE_PASS_SET_SIZE / 4)) + \
                                8  # PBKDF1 salt size

SECURITY_PARAM = 16
SECURITY_PARAM_IN_BASE64 = (SECURITY_PARAM * 4) / 3 + 1

# Static domain mapping list
STATIC_DOMAIN_LIST = '{}/server/static_domain_map.txt'.format(thisdir)
STATIC_DOMAIN_HASH_LIST = '{}/static/static_domain_hashes.txt'.format(thisdir)

# Machie generated password probability in set of 1000
MACHINE_GENRATED_PASS_PROB = 10

# Required by honey_client
HONEY_SERVER_URL = "http://localhost:5000/"
VAULT_FILE = 'static/vault.db'


L33T = {
    '3': 'e', '4': 'a', '@': 'a',
    '$': 's', '0': 'o', '1': 'i',
    'z': 's'
}

if DEBUG:
    random.seed(123456)
else:
    random.seed(os.urandom(4))
