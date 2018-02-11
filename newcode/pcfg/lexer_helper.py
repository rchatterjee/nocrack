import re, json, string
from collections import OrderedDict, defaultdict


class GrammarStructure:
    g_reg = r'^(?P<lhs>[A-Z]+)\s+->(?P<rhs>.*)$'
    G = {}

    def __init__(self, g_file='static/sample_grammarstructure.cfg'):
        for l in open(g_file):
            l = l.strip()
            m = re.match(self.g_reg, l)
            rhs = ['xx' if re.match(r'None', y)
                   else y.strip().strip("'")
                   for y in m.group('rhs').split('|')]
            try:
                self.G[m.group('lhs')].extend(rhs)
            except KeyError:
                self.G[m.group('lhs')] = rhs

    def getTermFiles(self):
        fl_list = {}
        for k, v in list(self.G.items()):
            reg = re.compile(r'\<(?P<name>.+)\>')
            for r in v:
                m = reg.match(r)
                if m:
                    fl_list[k] = m.group('name')
        return fl_list

    def to_json(self):
        return json.dumps(self.G)

    def __str__(self):
        return '\n'.join(['%s -> %s' % \
                          (lhs, ' | '.join(rhs))
                          for lhs, rhs in list(self.G.items())])


class Token:
    def __init__(self, val=None, type_=0, meta=None):
        self.value = val  # string/Token
        self.type_ = type_  # 0(NonT), 1(Terminal), 2(others)
        self.meta = meta  # Mangles

    def __str__(self):
        return str([self.value, self.type_])

    def show(self):
        return self.value

    def getval(self):
        return self.value

    def __init__(self, strng):
        m = re.match(r"'(.*)'", strng)
        if m:
            self.value = m.group(1)
            self.type_ = 1  # Terminal
            self.meta = ''
        else:
            self.value = strng
            self.type_ = 0
            self.meta = strng

    def __eq__(self, other):
        return self.value == other.value and self.type_ == other.type_


class Rule:
    def __init__(self, rhs, freq=0):
        if isinstance(rhs, list):
            self.rhs = rhs  # list of Tokens
        else:
            self.rhs = [Token(x) for x in rhs.split()]
        self.freq = freq

    def __eq__(self, other):
        if len(self.rhs) != len(other.rhs):
            return False
        for x, y in zip(self.rhs, other.rhs):
            if x != y: return False
        return True


class ParseTree(object):
    def __init__(self, l=None, r=None):
        self.tree = []
        if l and r:
            self.add_rule((l, r))

    def add_rule(self, rule, f=0):
        self.tree.append(rule)

    def extend_rules(self, ptree):
        self.tree.extend(ptree.tree)

    def get_rule(self):
        rule = self.tree[0]
        lhs = rule[0]
        rep_str = '%s_' % lhs
        rhs = ''.join([k[0].replace(rep_str, '')
                       for k in rule[1]])
        return lhs, rhs

    def rule_set(self):
        r = RuleSet()
        for p in self.tree:
            if isinstance(p[1], str):
                r.add_rule(p[0], p[1])
            else:
                r.add_rule(*(self.get_rule()))
                r.update_set(p[1].rule_set())
        return r

    def __str__(self):
        return str(self.tree)

    def __repr__(self):
        return str(self.tree)

    def __bool__(self):
        return bool(self.tree)

    def __getitem__(self, index):
        return self.tree[index]

    def __len__(self):
        return len(self.tree)

    def save(self, fname):
        json.dumps(self.tree, fname)


class RuleSet(object):
    """
    Set of rules, l -> r1 | r2 | r3
    """

    def __init__(self, l=None, r=None, d=None):
        self.G = defaultdict(OrderedDict)
        if l and r:
            self.add_rule(l, r)
        if d:
            for k, v in list(d.items()):
                self.G[k].update(v)

    def add_rule(self, l, r, f=0, rule=None):
        if rule:
            l = rule[0]
            r = rule[1]
        self.G[l][r] = self.G[l].get(r, 1) + f

    def update_set(self, T, with_freq=False, freq=0):
        for l, v in list(T.items()):
            if with_freq:
                for r, f in list(v.items()):
                    f = freq if freq > 0 else f
                    self.G[l][r] = self.G[l].get(r, 0) + f
            else:
                self.G[l].update(v)

    def __getitem__(self, k):
        return self.G.__getitem__(k)

    def __iter__(self):
        return iter(self.G)

    def __keytransform__(self, key):
        return key

    def save(self, outf):
        # sanity check
        for c in string.ascii_lowercase:
            k = 'L_%s' % c
            self.G[k] = self.G.get(k, {c: 1, c.upper(): 1})
        json.dump(self.G, outf, sort_keys=True,
                  separators=(',', ':'), indent=2)

    def load(self, in_file):
        self.G = json.load(open_(in_file),
                           object_pairs_hook=OrderedDict)

    def __str__(self):
        return json.dumps(self.G, separators=(',', ':'),
                          sort_keys=True, indent=2)

    def items(self):
        return list(self.G.items())

    def __bool__(self):
        return bool(self.G)


class Tweaker:
    rules = {'3': 'e',
             '4': 'a',
             '@': 'a',
             '$': 's',
             '0': 'o',
             '1': 'i',
             'z': 's'
             }

    def getTweakerRules(self, mangle_fl=None):
        try:
            rules = {}
            for l in open(mangle_fl):
                l = l.strip().split(':')
                rules[l[0]] = l[1]
        except IOError:
            print(mangle_fl, '-- could not be opend! Tweaker set is empty.')
        return rules;

    def __init__(self, mangle_fl=None):
        if mangle_fl:
            self.rules = self.getTweakerRules(mangle_fl)

    def tweak(self, s):
        if len(s) == 1:
            try:
                return self.rules[s]
            except KeyError:
                return s;
        else:
            return ''.join([self.tweak(c) for c in s])


class KeyBoard:
    offset = 50;  # to handle negetive!!!!
    layout_matrix = [
        "1234567890-=",
        "!@#$%^&*()_+",
        "qwertyuiop[]|",
        "QWERTYUIOP{}\\",
        "asdfghjkl;'",
        'ASDFGHJKL:"',
        "zxcvbnm,./",
        "ZXCVBNM<>?"
    ]

    def __init__(self, keyboard_layout_fl=None):
        self.layout_map = {}
        for i, row in enumerate(self.layout_matrix):
            for j, c in enumerate(row):
                self.layout_map[c] = (i / 2, j)

    def isShift(self, c):
        p = self.layout_map[c];
        return int(self.layout_matrix[2 * p[0]][p[1]] != c)

    def dist(self, p1, p2):
        dy = p2[0] - p1[0] + self.offset
        dx = p2[1] - p1[1] + self.offset
        return (dy, dx)

    def encode_keyseq(self, seq):
        if not seq[1]: seq[1] = (0, 0)
        a = (seq[1][0] << 24) | (seq[1][1] << 16) | (seq[2] << 8) | seq[3]
        return a

    def decode_keyseq(self, a):
        return [((0xff000000 & a) >> 24, (0xff0000 & a) >> 16), (0xff00 & a) >> 8, 0xff & a]

    def generate_passqord_fromseq(self, seq):
        p = ''
        for s in seq:
            p += s[0]
            pos = list(self.layout_map[s[0]])
            n = self.decode_keyseq(s[1])
            for i in range(n[2]):
                pos[0] += (n[0][0] - self.offset)
                pos[1] += (n[0][1] - self.offset)
                p += self.layout_matrix[pos[0] * 2 + n[1]][pos[1]]
        return p

    def IsKeyboardSeq(self, w):
        if len(w) < 5: return 99.0, []
        M = self.layout_map
        score = 0;
        try:
            pos = [M[c] for c in w]
        except KeyError:
            return 99.0, []
        dist_pos = [self.dist(pos[i - 1], pos[i])
                    for i in range(1, len(w))]
        group_dist_pos = [1]
        last = dist_pos[0]
        # for i, p in range(1, len(dist_pos)):
        #     if last == dist_pos[i]: group_dist_pos[-1]+=1
        #     else: 
        #         last = dist_pos[i]
        #         group_dist_pos.append(1)

        n_transition = len(set(dist_pos))
        n_char = len(set(w))
        # [start_char, [direction, shift, number]+]+
        # direction, 
        #     0 - same, 
        #     1,2..8 - U, UR, R, RD, D, DL, L, UL

        weight = float(n_transition) / len(dist_pos) + \
                 float(len(w)) / n_char
        seq_list = []
        if weight < 1.3:
            seq = [w[0], [], self.isShift(w[0]), 0]
            for i in range(1, len(w)):
                is_shift_ = self.isShift(w[i])
                if not seq[1] and is_shift_ == seq[2]:
                    seq[1] = dist_pos[i - 1]
                    seq[3] += 1
                elif seq[1] != dist_pos[i - 1] or seq[2] != is_shift_:
                    seq_list.append(seq)
                    seq = [w[i], [], is_shift_, 0]
                else:
                    seq[3] += 1
            if seq: seq_list.append(seq)
            for i, seq in enumerate(seq_list):
                seq_list[i] = [seq[0], self.encode_keyseq(seq)];
        return weight, seq_list


class Date:
    """
    Dt --> MDY, DMY, Y, MD, YMD, M/D/Y, D/M/Y
    Y --> yy | yyyy
    M --> mm | mon
    D --> dd
    mm --> 01 - 12
    dd --> 01 - 31
    mon --> Jan - dec
    yy --> [4-9][0-9] | [0-2][0-9]
    yyyy --> 19[4-9][0-9] | 2[01][0-9][0-9]
    """
    yy = '([6-9][0-9])'
    yyyy = '(19[4-9][0-9]|20[0-3][0-9])'
    mm = '(0[0-9]|1[0-2])'
    mon = '(jan | feb)'  # TODO: Not sure how to handle this
    dd = '([0-2][0-9]|3[01])'
    date_regex = re.compile(r"""^(?P<date>
(?P<mdy>{mm}{dd}{yy})|
(?P<mdY>{mm}{dd}{yyyy})|
(?P<dmy>{dd}{mm}{yy})|
(?P<dmY>{dd}{mm}{yyyy})|
(?P<y>{yy})|
(?P<Y>{yyyy})|
(?P<YY>{yyyy}{yyyy})|
(?P<md>{mm}{dd})|
(?P<ymd>{yy}{mm}{dd})|
(?P<Ymd>{yyyy}{mm}{dd})
)
$""".format(**{'mm': mm, 'yy': yy, 'yyyy': yyyy,
               'dd': dd}),
                            re.VERBOSE)

    # TODO: randomize the ordering of mm and dd,
    # Secuirty concern

    def __init__(self, word=None, T_rules=None):
        # self.date += "|(?P<mobno>\(\d{3}\)-\d{3}-\d{4}|\d{10}))(?P<postfix>\D*$)"
        self.date = {}
        if word:
            self.set_date(word)
        if T_rules:
            self.update_date_regex(T_rules)

    def set_date(self, date_W):
        self.date = self.IsDate(date_W)

    def update_date_regex(self, T_rules):
        # customized Date regex
        regex = '^(?P<date>%s)' % \
                ('|'.join(['(?P<%s>%s)' % \
                           (r.replace(',', ''),
                            ''.join([self.regexes(x)
                                     for x in r.split(',')]))
                           for r in T_rules])
                 )
        self.date_regex = re.compile(regex)

    def regexes(self, sym):
        D = {'m': 'mm',
             'y': 'yy',
             'Y': 'yyyy',
             'd': 'dd'}
        return eval('self.' + D[sym])

    def symbol(self):
        return 'T'

    def length(self, var):
        if var == 'Y':
            return 4
        elif var in ['m', 'd', 'y']:
            return 2
        else:
            return 99

    def encodeDate(self):
        return ''

    def parse_tree(self):
        print(self.date)
        return self.date

    def rule_set(self):
        r = RuleSet()
        comb = ''.join([x[0][-1] for x in self.date])
        r.add_rule('T', comb)
        for l in self.date:
            r.add_rule(*l)
        return r

    def IsDate(self, s):
        m = re.match(self.date_regex, s)
        if not m: return None;
        m_dict = dict((k, v)
                      for k, v in m.groupdict().items()
                      if v and k != 'date')
        k, v = list(m_dict.items())[0]
        x = ParseTree()
        for l in k:
            x.add_rule(("T_%s" % l, v[:self.length(l)]))
            v = v[self.length(l):]
        return x

    def __deepcopy__(self, memo):
        return self

    def __bool__(self):
        return bool(self.date)

    __bool__ = __nonzero__

    def __str__(self):
        return str(self.date)


if __name__ == "__main__":
    # print GrammarStructure().getTermFiles()
    print(Date(T_rules=['Y,m,d'], word='20131026'))
