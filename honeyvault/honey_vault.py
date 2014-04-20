from honey_enc import DTE, DTE_large
from scanner import Grammar, Scanner
import honeyvault_config as hny_config
#from buildPCFG import *
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random
import copy
from helper import convert2group

rnd_source = Random.new()

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
        domain_hash_map_fl = domain_hash_map if domain_hash_map \
            else 'server/static_domain_hashes.txt'
        self.domain_hash_map = json.load(open_(domain_hash_map_fl))
        self.vault_fl = vault_fl
        self.initialize_vault(mp)
        self.dte = DTE(self.PCFG.decode_grammar(self.H))

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

    def initialize_vault(self):
        if not os.path.exist(self.vault_fl):
            self.H = [convert2group(0,1) 
                      for x in range(self.s_g)]
            self.S = [convert2group(0,1) 
                      for x in range(self.s)]
            self.H[0] = hny_config.VAULT_SIZE_TO_FREQ[0]
            self.salt = rnd_source.read(size=16)
            self.save()
        else:
            self.load()

    def add_password(self, domain_pw_map):
        nG = copy.deepcopy(self.dte.G)
        for p in domain_pw_map.values(): 
            nG.update(p)
        nG.fix_freq(self.pcfg)
        ndte = DTE(nG)
        if ndte != DTE:
            # if new dte is different then 
            for i, p in enumerate(self.S):
                self.S[i] = ndte.encode(
                    self.dte.decode_pw(self.S[i]))
        for d,p in domain_pw_map:
            self.S[ self.get_domain_index(d) ] = \
                self.dte.encode_pw(p)

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

    def save(self):
        with open(self.vault_fl, 'wb') as fvault:
            fvault.write(self.salt)
            arr = self.H
            for a in self.S:
                arr.extend(a) 
            assert len(arr) == hny_config.HONEY_VAULT_ENCODING_SIZE
            
            aes = do_crypto_setup(mp, self.salt)
            fvault.write(aes.encrypt(
                    struct.pack('!%sI' % len(arr), arr)))

    def load(self, mp):
        with open(vault_fl, 'rb') as fvault:
            self.salt = fvault.read(16)
            aes = do_crypto_setup(mp, self.salt)
            buf = aes.decrypt(self.fvault.read())
            self.H, t_s = \
                struct.unpack('!%(s_g)sI%(s)sI' % self, buf)
            self.S = [t_s[i*hny_config.PASSWORD_LENGTH:\
                              (i+1)*hny_config.PASSWORD_LENGTH] 
                      for i in range(self.s)]





def vault_encode(vault, mp):
    #print vault
    S = Scanner()
    dte = DTE()
    G = Grammar()
    G.G = {}

    # sub-grammar generation
    for v in set(vault): # bring in Vault distribution
        T, W, U = S.tokenize(v, True)
        rule = ','.join(T)
        f = dte.get_freq('G', rule)
        G.addRule_lite('G', rule, f[0], f[1], True )
        for (l,r) in zip(T,W):
            f = dte.get_freq(l, r)
            G.addRule_lite(l, r, f[0], f[1], True )


    # Encode sub-grammar
    stack = ['G']
    code_g = []
    while stack:
        head = stack.pop()
        rule = G[head][0]
        t_set = []
        t_set = list(set([ x for i,r in enumerate(rule) 
                           for x in r.split(',') 
                           if G[head][1][i][1] is NONTERMINAL ]))
        t_set.reverse()
        stack.extend(t_set)
        n = len(rule)
        code_g.append(convert2group(sum(VAULT_SIZE_TO_FREQ[:n]), 
                                    VAULT_SIZE_TO_FREQ[-1]))
        code_g.extend([dte.encode(head, r) for r in rule])
        

    # reset the dte and use the subgrammar for subsequent operations
    dte.update_dte_for_vault(G)
    
    # we have to publish the vault size some where in the encoding.
    # n = len(vault)
    # code_g.append(convert2group(n, MAX_VAULT_SIZE)) # this is public info

    # encode every password in the vault using the newly generated sub-grammar
    for v in vault: # bring in Vault distribution
        T, W, U = S.tokenize(v, True)
        rule = ','.join(T)
        code_g.append(dte.encode('G', rule))
        for i,p in enumerate(T):
            t=dte.encode(p, W[i])
            if t==-1: 
                print "Sorry boss! iQuit!"
                exit(0)
                # return Encode_spcl(m, grammar)
            code_g.append( t )

    # padd the encoding with some random numbers to make it of size PASSWORD_LENGTH 
    if PASSWORD_LENGTH>0:
        extra = PASSWORD_LENGTH - len(code_g);
        code_g.extend( [ convert2group(0,1) for x in range(extra) ] )

    # pack the 'integers' into a struct
    c_struct = struct.pack('%sI' % len(code_g), *code_g )
    return c_struct


def vault_decode(cipher, mp, vault_size):
    dte = DTE()
    t = len( cipher );
    P = struct.unpack('%sI'%(t/4), cipher )

    # first decode the sub-grammar part from the large grammar
    G=Grammar()
    G.G = {}
    iterp = iter(P)
    stack = ['G']
    while stack:
        head = stack.pop()
        p = iterp.next()
        n = getIndex(p, VAULT_SIZE_TO_FREQ)
        #print p, p%VAULT_SIZE_TO_FREQ[-1], VAULT_SIZE_TO_FREQ
        NonTlist = []
        for x in range(n):
            r = dte.decode(head, iterp.next(), freq_also=True)
            G.addRule_lite(head, r[0], r[1], r[2], True)
            if r[2]==NONTERMINAL: NonTlist.extend(r[0].split(','))
            # print 'Grammar:', G
        t_set = list(set(NonTlist))
        t_set.reverse()
        stack.extend(t_set)

    # decode every password in order using the newly generated sub-grammar
    #print "DecodedGrammar", G
    dte.update_dte_for_vault(G)
    pass_vault = []
    for i in range(vault_size):
        plaintext = '';
        stack = ['G']
        while stack:
            head = stack.pop()
            g = dte.decode(head, iterp.next())
            if g[1]==NONTERMINAL:
                arr = g[0].split(',')
                arr.reverse()
                stack.extend(arr)
            else:
                plaintext += g[0]
        pass_vault.append(plaintext)
    return pass_vault;

                           


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

