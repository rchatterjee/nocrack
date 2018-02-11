import sys, os, math, struct, bz2, resource

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dte.honey_enc import DTE_random
import unittest
from pcfg import pcfg
from helper import random, MAX_INT, diff
import honeyvault_config as hny_config
from dte.honey_vault import HoneyVault

VAULT_FILE = 'static/vault.db'

RANDOM_PW_SET = ["bhabyko", "barkley", "baltazar", "augusta",
                 "asuncion", "april7", "adam12", "Thomas", "686868", "575757",
                 "1234565", "121090", "111189", "1111", "110589", "01230123", "ysabel",
                 "123xxxxxxxx", "thomson", "sweetz", "srilanka", "softball6",
                 "sexylove1", "sexyangel", "screen!!@", "1runaway", "randolph",
                 "pyramid", "putanginamo", "pinkys", "payatot", "patrik", "papagal",
                 "<oneluv>", "namaste", "mymother", "misery", "mimamamemima",
                 "luis123", "luckystar", "lucky8", "12lucky12", "loveyah", "lovey",
                 "loveisblind", "leopardo", "lala12", "knicks", "jonas1"]


class TestDteRandom(unittest.TestCase):
    def test_DTE_random(self):
        r_dte = DTE_random()
        for i in range(100):
            pw, N = r_dte.generate_and_encode_password()
            pw_prime = r_dte.decode_pw(N)
            self.assertEqual(pw, pw_prime, "Password mismatch in decoding" \
                                           "for ({}) pw: {}, N: {}, pw': {}".format(i, sorted(pw), N[:5],
                                                                                    sorted(pw_prime)))


class TestDTE(unittest.TestCase):
    def test_DTE(self):
        vault_file = VAULT_FILE + '~test'
        mpw = 'Masterpassw0rd' + str(random.randint(0, 100))
        hv = HoneyVault(vault_file, mpw)
        PW_set = dict((i, hv.dte.decode_pw(pw_encodings)) for i, pw_encodings in \
                      enumerate(hv.S) if hv.machine_pass_set[i] == '0')
        for i, pw in list(PW_set.items()):
            s = hv.dte.encode_pw(pw)
            tpw = hv.dte.decode_pw(s)
            self.assertEqual(tpw, pw, "Encode-decode pw is wrong. {}: {} ----> {}".format(i, pw, tpw))
        print("All encode-decoing test passed")
        return
        hv.add_password({'google.com': 'password' + str(random.randint(0, 1000))})
        ignore = set([hv.get_domain_index('google.com')])

        for i, pw_encodings in enumerate(hv.S):
            if hv.machine_pass_set[i] == '0' and i not in ignore:
                npw = hv.dte.decode_pw(pw_encodings)
                self.assertEqual(PW_set[i], npw, "New passwords changed!!!" \
                                                 "Expecting: '{}' at {}. Got '{}'".format(PW_set[i], npw))


class TestVaultDistPCFG(unittest.TestCase):
    def test_enc_dec_vault_size(self):
        vd = pcfg.VaultDistPCFG()
        X = vd.encode_vault_size('D', 3)
        t = vd.decode_vault_size('D', X)
        self.assertEqual(t, 3, str((X, t)))

        for i in range(25):
            k = random.randint(1, pcfg.MAX_ALLOWED)
            lhs = random.choice(list(vd.G.keys()))
            e = vd.encode_vault_size(lhs, k)
            self.assertEqual(vd.decode_vault_size(lhs, e), k, "VaultSizeDecodingError:" \
                                                              " Expecting: {} for (lhs: {}, e:{}), but decoded to: {}" \
                             .format(k, lhs, e, vd.decode_vault_size(lhs, e)))


class TestPCFG(unittest.TestCase):
    def test_encode_decode_subgrammar(self):
        H = random.randints(0, MAX_INT, hny_config.HONEY_VAULT_GRAMMAR_SIZE)
        tr_pcfg = pcfg.TrainedGrammar()
        G = tr_pcfg.decode_grammar(H)
        for i in range(10):
            Hprime = tr_pcfg.encode_grammar(G)
            Gprime = tr_pcfg.decode_grammar(Hprime)
            self.assertEqual(Gprime, G, "G and Gprime are not equal.\n" \
                                        "G: {}\nGprime: {}\Difference: o-n = {}, n-o = {}" \
                             .format(G.nonterminals(), Gprime.nonterminals(),
                                     diff(G, Gprime), diff(Gprime, G)))

    def test_encode_decode_rule(self):
        H = random.randints(0, MAX_INT, hny_config.HONEY_VAULT_GRAMMAR_SIZE)
        tr_pcfg = pcfg.TrainedGrammar()
        G = tr_pcfg.decode_grammar(H)

        for i, pw in enumerate(random.sample(RANDOM_PW_SET, 10)):
            pt = tr_pcfg.l_parse_tree(pw)
            for p in pt:
                t = tr_pcfg.encode_rule(*p)
                c = tr_pcfg.decode_rule(p[0], t)
                assert p[1] == c, "Decoding {} we got {}. Expecting {}" \
                    .format(t, c, p[1])

    def test_encode_decode_pw(self):
        H = random.randints(0, MAX_INT, hny_config.HONEY_VAULT_GRAMMAR_SIZE)
        tr_pcfg = pcfg.TrainedGrammar()
        G = tr_pcfg.decode_grammar(H)
        for i, pw in enumerate(random.sample(RANDOM_PW_SET, 30)):
            pwprime = G.decode_pw(G.encode_pw(pw))
            self.assertEqual(pwprime, pw, "Password encode-decode error!\n" \
                                          "EncodedPw={}, DecodedPw={}".format(pw, pwprime))


class TestHoneyClient(unittest.TestCase):
    def test_getpass(self):
        h_string = """Just a test framework for testing getpass
        function.

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
        self.assertEqual(w, ret_pw, "PasswordAddFailed: added=<{}>, returned=<{}>" \
                         .format(w, ret_pw))  # password added correctly.
        v = hv.gen_password(mpw, [u])[u]
        self.assertEqual(v, hv.get_password([u])[u], "PasswordGenFailed: expecting={}, returned={}" \
                         .format(v, hv.get_password([u])[u]))  # password generated correctly.

        d_pws = {
            'asdfadsf.com': 'lkjandfa98w3ufh9 awe98fa',
            'a': 'a',
            '123': 'adf',
            'tt.com': 'thisismymasterpasswordanditiss',
            'fb.com': 'Amazing@#ComplexPassword',
        }
        hv.add_password(d_pws)
        ret_pws = hv.get_password(list(d_pws.keys()))
        for k, v in list(d_pws.items()):
            self.assertEqual(ret_pws[k], v, "Decoding mismatch @ added: {} <--> returned: {}" \
                             .format(v, ret_pws[k]))

        hv.add_password(d_pws)
        ret_pws = hv.get_password(list(d_pws.keys()))
        for k, v in list(d_pws.items()):
            self.assertEqual(ret_pws[k], v, "Decoding mismatch @ added: {} <--> returned: {}" \
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
