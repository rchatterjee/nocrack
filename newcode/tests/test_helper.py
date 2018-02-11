import os
import sys

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from helper import random, diff
import unittest


class TestHelper(unittest.TestCase):
    def test_random(self):
        for l in [1, 2, 5, 10, 100]:
            a = random.randints(0, 1, l)
            self.assertEqual(len(a), l, "Not returning correct length, should be {}" \
                                        "returning {}".format(l, len(a)))
            self.assertTrue(all(x >= 0 and x < 1 for x in a), "All values are not in limit")

    def test_diff(self):
        A = {'a': 1, 'b': 3}
        B = {'a': 2, 'c': 3, 'd': {'4': 5}}
        print(list(diff(A, B)))
        print(list(diff(B, A)))


if __name__ == "__main__":
    unittest.main()
