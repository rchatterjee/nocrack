import sys, os, math, struct, bz2, resource
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from honeyvault.honey_enc import DTE_random
import unittest

class TeastDteRandom(unittest.TestCase):
    def test_DTE_random(self):
        r_dte = DTE_random()
        for i in range(100):
            pw, N = r_dte.generate_and_encode_password()
            pw_prime = r_dte.decode_pw(N)
            self.assertEqual(pw, pw_prime, "Password mismatch in decoding"\
                             "for ({}) pw: {}, N: {}, pw': {}".format(i, sorted(pw), N[:5], sorted(pw_prime)))

if __name__ == "__main__":
    unittest.main()

