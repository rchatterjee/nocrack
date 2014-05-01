import os, sys, json, math
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honey_enc import DTE, DTE_large, DTE_random
import honeyvault_config as hny_config
from lexer.pcfg import TrainedGrammar 
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random
import copy, struct
from helper.helper import convert2group, open_, getIndex, print_err
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
    sample = [10,19,20,31]
    mpass_set_size = hny_config.HONEY_VAULT_MACHINE_PASS_SET_SIZE

    def __init__(self, vault_fl, mp):
        self.pcfg = DTE_large()
        domain_hash_map_fl = hny_config.STATIC_DOMAIN_HASH_LIST
        self.domain_hash_map = json.load(open_(domain_hash_map_fl))
        self.vault_fl = vault_fl
        self.mp = mp
        self.initialize_vault(mp)
        self.dte = DTE(self.pcfg.decode_grammar(self.H))
        # print_err (self.dte.G)
        
    def get_domain_index(self, d):
        h = SHA256.new()
        h.update(d)
        d_hash = h.hexdigest()[:32]
        try:
            return self.domain_hash_map[d_hash]
        except KeyError:
            sys.stderr.write('WARNING! S1 miss for %s\n' % d)
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
            self.machine_pass_set = [
                '1' if random.randint(0,1000) < hny_config.MACHINE_GENRATED_PASS_PROB
                else '0'
                for x in range(self.mpass_set_size*8)]
            self.salt = rnd_source.read(8)
            self.save(mp)
        else:
            self.load(mp)

    def gen_password(self, mp, domain_list, size=10):
        r_dte = DTE_random()
        reply = []
        for d in domain_list:
            i = self.get_domain_index(d)
            p, encoding = r_dte.generate_and_encode_password(size)
            self.S[i] = encoding
            self.machine_pass_set[i] = '1'
            reply.append(p)
            self.save()
        return OrderedDict(zip(domain_list, reply))
    
    def add_password(self, domain_pw_map):
        nG = copy.deepcopy(self.dte.G)
        nG.update_grammar(*(domain_pw_map.values()))
        ndte = DTE(nG)
        if ndte != self.dte:
            # if new dte is different then
            for i, p in enumerate(self.S):
                if self.machine_pass_set[i] == '1':
                    continue
                pw = self.dte.decode_pw(self.S[i])
                if not pw: continue   # TODO SECURITY
                self.S[i] = ndte.encode_pw(pw)
            self.H = self.pcfg.encode_grammar(nG)
            print_err(self.H[:10])
            G_ = self.pcfg.decode_grammar(self.H)
            print_err("-"*50)
            print_err("Original: ", nG, '\n', '='*50)
            print_err("After Decoding:", G_)
            assert G_ == nG
        for d,p in domain_pw_map.items():
            i = self.get_domain_index(d)
            self.S[i] = ndte.encode_pw(p)
            self.machine_pass_set[i] = '0'
        self.dte = ndte
        
    def get_password(self, domain_list):
        pw_list = []
        r_dte = DTE_random()
        for d in domain_list:
            i = self.get_domain_index(d)
            if self.machine_pass_set[i] == '1':
                print_err("Machine Password")
                pw = r_dte.decode_pw(self.S[i])
            else:
                pw = self.dte.decode_pw(self.S[i])
            pw_list.append(pw)
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
            buf = list(self.H[:])
            for i, a in enumerate(self.S):
                buf.extend(a)
            aes = do_crypto_setup(mp, self.salt)
            fvault.write(aes.encrypt(
                    struct.pack('!%sI' % \
                                    hny_config.HONEY_VAULT_ENCODING_SIZE, 
                                *buf))
                         )
            for i in range(self.mpass_set_size):
                fvault.write(struct.pack('!B', int(
                            ''.join(self.machine_pass_set[i*8:(i+1)*8]), 2)))
                
    def load(self, mp):
        with open(self.vault_fl, 'rb') as fvault:
            self.salt = fvault.read(8)
            size_of_int = struct.calcsize('I')
            aes = do_crypto_setup(mp, self.salt)
            buf = aes.decrypt(
                fvault.read(hny_config.HONEY_VAULT_ENCODING_SIZE * size_of_int))
            t_s = struct.unpack(
                '!%sI' % hny_config.HONEY_VAULT_ENCODING_SIZE, buf)
            self.H = t_s[:hny_config.HONEY_VAULT_GRAMMAR_SIZE]
            t_s = t_s[hny_config.HONEY_VAULT_GRAMMAR_SIZE:]
            self.S = [t_s[i*hny_config.PASSWORD_LENGTH:(i+1)*hny_config.PASSWORD_LENGTH]
                      for i in range(self.s)]
            buf = fvault.read(self.mpass_set_size)
            self.machine_pass_set = \
                list(''.join(["{0:08b}".format(x) 
                              for x in struct.unpack(
                                "%sB" % self.mpass_set_size, buf)]))
            assert len(self.machine_pass_set) >= len(self.S)

#----------------------------------------------------------------------

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
    print "TODO: add main/test"
    # main();

