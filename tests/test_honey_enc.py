import sys, os, math, struct, bz2, resource
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault.honey_enc import DTE_random, DTE_large
import unittest
from lexer import pcfg
from helper.helper import random, MAX_INT
import honeyvault_config as hny_config
from honeyvault.honey_vault import HoneyVault
VAULT_FILE  = 'static/vault.db'

class TeastDteRandom(unittest.TestCase):
    def test_DTE_random(self):
        r_dte = DTE_random()
        for i in range(100):
            pw, N = r_dte.generate_and_encode_password()
            pw_prime = r_dte.decode_pw(N)
            self.assertEqual(pw, pw_prime, "Password mismatch in decoding"\
                             "for ({}) pw: {}, N: {}, pw': {}".format(i, sorted(pw), N[:5], sorted(pw_prime)))
    
    def test_encode_decode_subgrammar(self):
        H = random.randints(0, MAX_INT, hny_config.HONEY_VAULT_GRAMMAR_SIZE)
        pcfg = DTE_large()
        G = pcfg.decode_grammar(H)
        for i in range(5):
            Hprime = pcfg.encode_grammar(G)
            Gprime = pcfg.decode_grammar(Hprime)
            self.assertEqual(Gprime, G, "G and Gprime are not equal.\n"\
                             "G: {}\nGprime: {}\n".format(G.nonterminals(), Gprime.nonterminals()))


class TestNormalDTE(unittest.TestCase):
    def test_DTE(self):
        vault_file = VAULT_FILE+'~test'
        mpw = 'Masterpassw0rd'+str(random.randint(0,100))
        hv = HoneyVault(vault_file, mpw)
        PW_set = dict((i, hv.dte.decode_pw(pw_encodings)) for i, pw_encodings in \
                  enumerate(hv.S) if hv.machine_pass_set[i]=='0')
        for i, pw in PW_set.items():
            s = hv.dte.encode_pw(pw)
            tpw = hv.dte.decode_pw(s)
            self.assertEqual(tpw, pw, "Encode-decode pw is wrong. {}: {} ----> {}".format(i, pw, tpw))
        print "All encode-decoing test passed"
        return
        hv.add_password({'google.com': 'password' + str(random.randint(0, 1000))})
        ignore = set([hv.get_domain_index('google.com')])

        for i, pw_encodings in enumerate(hv.S):
            if hv.machine_pass_set[i] == '0' and i not in ignore:
                npw = hv.dte.decode_pw(pw_encodings)
                self.assertEqual(PW_set[i], npw, "New passwords changed!!!"\
                    "Expecting: '{}' at {}. Got '{}'")


class TestHoneyClient(unittest.TestCase):
    def test_getpass(self):
        return
        h_string =  """
        Just a test framework for testing getpass  function.
        """
        vault_file = VAULT_FILE + "~test"
        try:
            os.remove(vault_file)
        except OSError:
            pass;
        mpw = 'Masterpassw0rd12'
        hv = HoneyVault(vault_file, mpw)
        u = 'google.com'
        w = hv.get_password([u])[u]
        hv.add_password({u: w})
        ret_pw = hv.get_password([u])[u]
        self.assertEqual(w, ret_pw, "PasswordAddFailed: added=<{}>, returned=<{}>"\
                         .format(w, ret_pw))  # password added correctly.
        v = hv.gen_password(mpw, [u])[u]
        self.assertEqual(v, hv.get_password([u])[u], "PasswordGenFailed: expecting={}, returned={}"\
                         .format(v, hv.get_password([u])[u]))   # password generated correctly.
        
        d_pws = {
            'asdfadsf.com': 'lkjandfa98w3ufh9 awe98fa',
            'a': 'a',
            '123': 'adf',
            'tt.com': 'thisismymasterpasswordanditiss',
            'fb.com': 'Amazing@#ComplexPassword',
           }
        hv.add_password(d_pws)
        ret_pws = hv.get_password(d_pws.keys())
        for k,v in d_pws.items():
            self.assertEqual(ret_pws[k],v, "Decoding mismatch @ added: {} <--> returned: {}"\
                             .format(v, ret_pws[k]))
    
        os.remove(vault_file)

# class TestHoneyClient(unittest.TestCase):
#     def test_honeyclient(self):
#         from honey_client import add_pass, get_pass
#         # add random password
#         urls = ["google.com", "youtube.com", "facebook.com", "msn.com", "ebay.com", "microsoft.com",
#                 "yahoo.com", "twitter.com", "answers.com", "amazon.com", "yelp.com", "buzzfeed.com",
#                 "pinterest.com", "wordpress.com", "wikipedia.org","bing.com","about.com","linkedin.com",
#                 "blogger.com","blogspot.com","nbcnews.com","live.com"]
#         moreurls = [reversed(u.split('.')[0]) for u in urls]
#         add_pass("google.com", 'amazingpassword')
#         self.assertEqual(get_pass("google.com", 
#         for u in urls:
#             add_pass(*urls, *moreurls)



if __name__ == "__main__":
    unittest.main()

