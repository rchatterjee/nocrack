import json
import math
import os
import sys

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from .honey_enc import DTE, DTE_random
from pcfg.pcfg import TrainedGrammar
import honeyvault_config as hny_config
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Util import Counter
import copy, struct
from helper import (open_, print_err, process_parallel, random,
                    print_production)
from pcfg.pcfg import VaultDistPCFG
from collections import OrderedDict

# from IPython.core import ultratb
# sys.excepthook = ultratb.FormattedTB(color_scheme='Linux', call_pdb=1)

MAX_INT = hny_config.MAX_INT


# -------------------------------------------------------------------------------
def do_crypto_setup(mp, salt):
    key = PBKDF1(mp, salt, 16, 100, SHA256)
    ctr = Counter.new(128, initial_value=int(254))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes


def copy_from_old_parallel(args):
    odte, ndte, i, p = args
    ret = []
    pw = odte.decode_pw(p)
    if not pw:
        return i, pw, []
    ret = ndte.encode_pw(pw)
    if not ret:
        print("Cool I failed in encoding!! Kudos to me. pw: {}, i: {}"
              .format(pw, i))
        ret = pw
    else:
        tpw = ndte.decode_pw(ret)
        assert pw == tpw, "Encoding-Decoding password is wrong. Expecting {!r}, got {!r}"\
            .format(pw, tpw)

    return i, pw, ret


class HoneyVault:
    s1 = hny_config.HONEY_VAULT_S1
    s2 = hny_config.HONEY_VAULT_S2
    s_g = hny_config.HONEY_VAULT_GRAMMAR_SIZE
    s = hny_config.HONEY_VAULT_STORAGE_SIZE
    vault_total_size = hny_config.HONEY_VAULT_ENCODING_SIZE
    sample = [10, 19, 20, 31]
    mpass_set_size = hny_config.HONEY_VAULT_MACHINE_PASS_SET_SIZE

    def __init__(self, vault_fl, mp):
        self.pcfg = TrainedGrammar()  # Default large trained PCFG
        domain_hash_map_fl = hny_config.STATIC_DOMAIN_HASH_LIST
        self.domain_hash_map = json.load(open_(domain_hash_map_fl))
        self.vault_fl = vault_fl
        self.mp = mp
        self.initialize_vault(mp)
        self.dte = DTE(self.pcfg.decode_grammar(self.H))

    def get_domain_index(self, d):
        h = SHA256.new()
        h.update(d.encode('utf-8'))
        d_hash = h.hexdigest()[:32]
        try:
            i = self.domain_hash_map[d_hash]
            if i > self.s1:
                raise KeyError
            else:
                return i
        except KeyError:
            sys.stderr.write('WARNING! S1 miss for %s\n' % d)
            x = struct.unpack('8I', h.digest())[0]
            return self.s1 + x % self.s2

    def initialize_vault(self, mp):
        vd = VaultDistPCFG()
        if not os.path.exists(self.vault_fl):
            print_production("\nCould not find the vault file @ {}, so, sit tight, " \
                             "creating a dummy vault for you." \
                             "\nShould not take too long...\n".format(self.vault_fl))
            t_s = random.randints(0, MAX_INT, hny_config.HONEY_VAULT_ENCODING_SIZE)
            self.H = t_s[:hny_config.HONEY_VAULT_GRAMMAR_SIZE]
            t_s = t_s[hny_config.HONEY_VAULT_GRAMMAR_SIZE:]
            self.S = [t_s[i:i + hny_config.PASSWORD_LENGTH]
                      for i in range(0, self.s * hny_config.PASSWORD_LENGTH, hny_config.PASSWORD_LENGTH)]
            assert all(len(s) == hny_config.PASSWORD_LENGTH for s in
                       self.S), "All passwords encodings are not of correct length.\n {}".format(
                (len(s), hny_config.PASSWORD_LENGTH) for s in self.S)
            self.machine_pass_set = list('0' * (self.mpass_set_size * 8))
            k = int(math.ceil(hny_config.HONEY_VAULT_STORAGE_SIZE * \
                              hny_config.MACHINE_GENRATED_PASS_PROB / 1000.0))
            for i in random.sample(list(range(hny_config.HONEY_VAULT_STORAGE_SIZE)), k):
                self.machine_pass_set[i] = '1'
            self.salt = os.urandom(8)
            self.save(mp)
        else:
            self.load(mp)

    def gen_password(self, mp, domain_list, size=10):
        """
        generates random password strings for each of the domail
        specified, and saves it in corresponding location.
        Master password (@mp) is required for that.
        """
        r_dte = DTE_random()
        reply = []
        for d in domain_list:
            i = self.get_domain_index(d)
            p, encoding = r_dte.generate_and_encode_password(size)
            self.S[i] = encoding
            self.machine_pass_set[i] = '1'
            reply.append(p)
        self.save()
        return OrderedDict(list(zip(domain_list, reply)))

    def add_password(self, domain_pw_map):
        # print self.dte.G
        nG = copy.deepcopy(self.dte.G)
        print_production("Updating the grammar with new passwords..")
        nG.update_grammar(*(list(domain_pw_map.values())))
        ndte = DTE(nG)

        # TODO: fix this, currently its a hack to way around my bad
        # parsing. A password can be generated in a different way than it is parsed in most probable
        # way. The code is supposed to pick one parse tree at random. Currently picking the most 
        # probable one. Need to fix for security reason. Will add a ticket. 
        new_encoding_of_old_pw = []

        current_passwords = ['' for _ in range(hny_config.HONEY_VAULT_STORAGE_SIZE)]

        if self.dte and (ndte != self.dte):
            # if new dte is different then copy the existing human chosen passwords. 
            # Machine generated passwords are not necessary to re-encode. As their grammar
            # does not change. NEED TO CHECK SECURITY.
            print_production("Some new rules found, so adding them to the new grammar. " \
                             "Should not take too long...\n")
            data = [(self.dte, ndte, i, p)
                    for i, p in enumerate(self.S)
                    if self.machine_pass_set[i] == '0']
            if hny_config.DEBUG:
                result = map(copy_from_old_parallel, data)
            else:
                result = process_parallel(copy_from_old_parallel, data, func_load=100)

            for i, pw, pw_encodings in result:
                if isinstance(pw_encodings, str):
                    new_encoding_of_old_pw.append((i, pw_encodings))
                current_passwords[i] = pw
                self.S[i] = pw_encodings

                # print_err(self.H[:10])
                # G_ = self.pcfg.decode_grammar(self.H)
                # print_err("-"*50)
                # print_err("Original: ", nG, '\n', '='*50)
                # print_err("After Decoding:", G_)
                # assert G_ == nG

        print_production("\nAdding new passowrds..\n")
        for domain, pw in list(domain_pw_map.items()):
            i = self.get_domain_index(domain)
            print(">>", i, pw, domain)
            current_passwords[i] = pw
            self.S[i] = ndte.encode_pw(pw)
            self.machine_pass_set[i] = '0'

        # Cleaning the mess because of missed passwords
        # Because some password might have failed in copy_from_old_function, They need to be
        # re-encoded 
        if new_encoding_of_old_pw:
            print_err("\n<<<<<<\nFixing Mess!!\n{}>>>>>>>".format(new_encoding_of_old_pw))
            nG.update_grammar(*[p for i, p in new_encoding_of_old_pw])
            for i, p in new_encoding_of_old_pw:
                self.S[i] = ndte.encode_pw(p)
                self.machine_pass_set[i] = '0'

        if hny_config.DEBUG:
            for i, pw_encodings in enumerate(self.S):
                if self.machine_pass_set[i] == '0':
                    tpw = ndte.decode_pw(pw_encodings)
                    tpwold = current_passwords[i]
                    assert len(tpwold) <= 0 or tpw == tpwold, \
                        "The re-encoding is faulty. Expecting: '{}' at {}. Got '{}'.".format(tpwold, i, tpw)

        self.H = self.pcfg.encode_grammar(nG)
        self.dte = ndte

    def get_password(self, domain_list, send_raw=False):
        pw_list = []
        r_dte = DTE_random()
        for d in domain_list:
            i = self.get_domain_index(d)
            if self.machine_pass_set[i] == '1':
                pw = r_dte.decode_pw(self.S[i])
            else:
                pw = self.dte.decode_pw(self.S[i])
            pw_list.append(pw)
        return OrderedDict(list(zip(domain_list, pw_list)))

    def get_sample_decoding(self):
        """
        check some of the sample decoding to make sure you are
        not accidentally spoiling the vault
        """
        assert all(len(self.S[i]) == hny_config.PASSWORD_LENGTH for i in self.sample), \
            "Corrupted Encoding!!"
        return [self.dte.decode_pw(self.S[i]) for i in self.sample]

    def get_all_pass(self):
        """
        Returns all the passwords in the vault.
        """
        r_dte = DTE_random()
        return ((i, self.dte.decode_pw(s)) if self.machine_pass_set[i] == '0' \
                    else (i, r_dte.decode_pw(s))
                for i, s in enumerate(self.S))

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
                    ''.join(self.machine_pass_set[i * 8:(i + 1) * 8]), 2)))

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
            self.S = [t_s[i * hny_config.PASSWORD_LENGTH:(i + 1) * hny_config.PASSWORD_LENGTH]
                      for i in range(self.s)]
            buf = fvault.read(self.mpass_set_size)
            self.machine_pass_set = \
                list(''.join(["{0:08b}".format(x)
                              for x in struct.unpack(
                        "%sB" % self.mpass_set_size, buf)]))
            assert len(self.machine_pass_set) >= len(self.S)


# ----------------------------------------------------------------------

def main():
    if len(sys.argv) < 5 or sys.argv[0] in ['-h', '--help']:
        print('''Taste the HoneyVault1.1 - a New Password Encrypting paradigm! 
|| Encrypt with confidence ||
--encode vault_plain.txt masterpassword vault_cipher.txt
--decode vault_cipher.txt masterpassword stdout
        ''')
    else:
        f1 = sys.argv[2]
        mp = sys.argv[3]
        f2 = sys.argv[4]
        if sys.argv[1] == '--encode':
            vault = [l.strip().split(',')[2] for l in open(f1) if l[0] != '#']
            cipher = vault_encrypt(vault, mp)
            with open(f2, 'wb') as outf:
                n = len(vault)
                outf.write(struct.pack('<I', n))
                outf.write(cipher)
            print("Your Vault is encrypted! Now you can delte the plaintext vault text.")
        elif sys.argv[1] == '--decode':
            dt = open(f1, 'rb').read()
            n = struct.unpack('<I', dt[:4])[0]
            vault = vault_decrypt(dt[4:], mp, n)
            print(vault)
        else:
            print("Sorry Anthofila! Command not recognised.")


if __name__ == "__main__":
    print("TODO: add main/test")
    main()
