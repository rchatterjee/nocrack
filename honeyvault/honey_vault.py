import os, sys, json
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honey_enc import DTE, DTE_large
from scanner.scanner import Grammar, Scanner
import honeyvault_config as hny_config
#from buildPCFG import *
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random
import copy, struct
from helper.helper import convert2group, open_, getIndex
from helper.vault_dist import VaultDistribution
from collections import OrderedDict
from array import array

rnd_source = Random.new()
MAX_INT = hny_config.MAX_INT
#-------------------------------------------------------------------------------
def do_crypto_setup(mp, salt = b'madhubala'):
    key = PBKDF1(mp, salt, 16, 100, SHA256)
    ctr = Counter.new(128, initial_value=long(254))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes 

class HoneyVault:
    s1 = hny_config.HONEY_VAULT_S1
    s2 = hny_config.HONEY_VAULT_S2
    s_g = hny_config.HONEY_VAULT_GRAMMAR_SIZE
    s = hny_config.HONEY_VAULT_STORAGE_SIZE
    vault_total_size = hny_config.HONEY_VAULT_ENCODING_SIZE
    sample = [0,1,2]

    def __init__(self, vault_fl, mp):
        self.pcfg = DTE_large()
        self.scanner = Scanner() # default scanner
        domain_hash_map_fl = hny_config.STATIC_DOMAIN_HASH_LIST
        self.domain_hash_map = json.load(open_(domain_hash_map_fl))
        self.vault_fl = vault_fl
        self.mp = mp
        self.initialize_vault(mp)
        self.dte = DTE(self.pcfg.decode_grammar(self.H))
        print self.dte.G
        
    def get_domain_index(self, d):
        h = SHA256.new()
        h.update(d)
        d_hash = h.hexdigest()[:32]
        try:
            return self.domain_hash_map[d_hash]
        except KeyError:
            sys.stderr('WARNING! S1 miss for', d)
            x = struct.unpack('8I', h.digest())[0]
            return self.s1 + x % self.s2

    def initialize_vault(self, mp):
        vd = VaultDistribution()
        if not os.path.exists(self.vault_fl):
            self.H = [convert2group(0,1) 
                      for x in range(self.s_g)]
            self.S = [[convert2group(0,1) 
                       for i in range(hny_config.PASSWORD_LENGTH)] 
                      for x in range(self.s)]
            self.H[0] = vd.encode_vault_size(0)
            self.salt = rnd_source.read(8)
            self.save(mp)
        else:
            self.load(mp)

    def add_password(self, domain_pw_map):
        nG = copy.deepcopy(self.dte.G)
        for p in domain_pw_map.values(): 
            nG.update_grammar(pw=p)
        nG.fix_freq(self.pcfg)
        ndte = DTE(nG)
        if ndte != self.dte:
            # if new dte is different then 
            for i, p in enumerate(self.S):
                pw = self.dte.decode_pw(self.S[i])
                if not pw: continue   # TODO SECURITY
                self.S[i] = ndte.encode_pw(pw)
            self.H = self.pcfg.encode_grammar(nG)
            G_ = self.pcfg.decode_grammar(self.H)
            print "-"*50
            print "Original: ", nG, '\n', '='*50
            print "After Decoding:", G_
            assert G_ == nG
        for d,p in domain_pw_map.items():
            self.S[self.get_domain_index(d)] = ndte.encode_pw(p)
            # DEBUG
            after_decoding = ndte.decode_pw(self.S[self.get_domain_index(d)])
            print "Original:", p, "------\tAfterDecodign", after_decoding
            assert  after_decoding == p
        print "New Grammar:", nG
        self.dte = ndte

        
    def get_password(self, domain_list):
        pw_list = [self.dte.decode_pw(
                self.S[self.get_domain_index(d)])
                   for d in domain_list ]
        return OrderedDict(zip(domain_list, pw_list)) 
    
    def get_sample_decoding(self):
        """
        check some of the sample decoding to make sure you are
        not accidentally spoiling the vault
        """
        return [self.dte.decode_pw(self.S[i]) for i in self.sample]

    def save(self, mp=None):
        if not mp:
            mp = self.mp
        with open(self.vault_fl, 'wb') as fvault:
            fvault.write(self.salt)
            buf = self.H[:]
            for i, a in enumerate(self.S):
                buf.extend(a)
            aes = do_crypto_setup(mp, self.salt)
            fvault.write(aes.encrypt(
                    struct.pack('!%sI' % \
                                    hny_config.HONEY_VAULT_ENCODING_SIZE, 
                                *buf))
                         )

    def load(self, mp):
        with open(self.vault_fl, 'rb') as fvault:
            self.salt = fvault.read(8)
            aes = do_crypto_setup(mp, self.salt)
            buf = aes.decrypt(fvault.read())
            t_s = struct.unpack( \
                '!%sI' % (hny_config.HONEY_VAULT_ENCODING_SIZE),
                buf)
            self.H = t_s[:hny_config.HONEY_VAULT_GRAMMAR_SIZE]
            t_s = t_s[hny_config.HONEY_VAULT_GRAMMAR_SIZE:]
            self.S = [t_s[i*hny_config.PASSWORD_LENGTH:\
                              (i+1)*hny_config.PASSWORD_LENGTH] 
                      for i in range(self.s)]
            # print '\n'.join(["%s" % str(a[:10]) for a in self.S])


#----------------------------------------------------------------------

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

