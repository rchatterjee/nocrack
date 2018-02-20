from buildPCFG import parse, buildpcfg
import unittest

class test_buildPCFG(unittest.TestCase):
    def test_parse(self):
        T = parse("Password123")
        assert str(T.parse_tree()) == str([('W7',
                                            [('W7', 'password'), ('L', 'Caps')]),
                                           ('D2',
                                            [('D2', '123')])])
