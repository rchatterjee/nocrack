import re 


class GrammarStructure:
    g_reg = r'^(?P<lhs>[A-Z]+)\s+->(?P<rhs>.*)$'
    G = {}

    def __init__(self, g_file='sample_grammarstructure.cfg'):
        for l in open(g_file):
            l = l.strip()
            m = re.match(self.g_reg, l)
            rhs = ['xx' if re.match(r'None', y) else y.strip().strip("'") for y in  m.group('rhs').split('|')]
            try:
                self.G[m.group('lhs')].extend(rhs)
            except KeyError:
                self.G[m.group('lhs')] = rhs
    
    def getTermFiles(self):
        fl_list = {}
        for k, v in self.G.items():
            reg = re.compile(r'\<(?P<name>.+)\>')
            for r in v:
                m = reg.match(r)
                if m: 
                    fl_list[k] = m.group('name')
        return fl_list

    def to_json(self):
        return json.dumps(self.G)
    def __str__(self):
        return '\n'.join(['%s -> %s' % (lhs, ' | '.join(rhs)) for lhs, rhs in self.G.items()])


class Token:
    def __init__(self, val=None, type_=0, meta=None):
        self.value = val    # string/Token
        self.type_ = type_  # 0(NonT), 1(Terminal), 2(others)
        self.meta  = meta   # Mangles

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
            self.type_ = 1   # Terminal
            self.meta = ''
        else:
            self.value = strng
            self.type_ = 0
            self.meta  = strng

    def __eq__(self, other):
        return self.value == other.value and self.type_ == other.type_


class Rule:
    def __init__(self, rhs, freq=0):
        if type([]) == type(rhs):
            self.rhs = rhs    # list of Tokens
        else:
            self.rhs = [Token(x) for x in rhs.split(' ')]
        self.freq= freq

    def __eq__(self, other):
        if len(self.rhs) != len(other.rhs):
            return False
        for x, y in zip(self.rhs, other.rhs):
            if x != y: return False
        return True


class ParseTree:
    def __init__(self):
        self.tree = dict('S', [])

    def example(self):
        self.tree = {'G': [
            {'F': [{'B': ['']}, {'P': ['1']}, {'W': ['computer']}, {'S': ['']}]},
            {'I': ['']},
            {'F': [{'B': ['']}, {'P': ['']}, {'W': ['secret']}, {'S': ['23']}]},
        ]}


# class Grammar:
#     def __init__(self):
#         g_structure = GrammarStructure()
#         self.g = dict(('R', []))   # list of rules, R start symbol
#         for lhs, rhs in g_structure.G.items():
#             self.g[lhs] = [Rule(r) for r in rhs]


class Mangle:
    def __init__(self, w, mw):
        """
        w = "password"
        mw = Pa$$word
        0: Capitalized
        1: All Caps
        2: leet
        Scratch: Space is not allowed inside a password
        """
        self.code = mw.isalpha*(mw.isupper()*2 + mw.istitle()) 
        self.leet_transformations = ('','')
        if not code:
            self.leet_transformations = (w, mw)


class Tweaker:
    rules = {'3':'e',
             '4':'a',
             '@':'a',
             '$':'s',
             '0':'o',
             '1':'i',
             'z':'s'
             }

    def getTweakerRules(self, mangle_fl=None ):
        try:
            rules = {}
            for l in open(mangle_fl):
                l = l.strip().split(':')
                rules[l[0]] = l[1]
        except IOError:
            print mangle_fl, '-- could not be opend! Tweaker set is empty.'
        return rules;

    def __init__(self, mangle_fl=None):
        if mangle_fl:
            self.rules = self.getTweakerRules(mangle_fl)
        
    def tweak ( self, s ):
        if len(s)==1: 
            try: return self.rules[s]
            except KeyError: return s;
        else:
            return ''.join([self.tweak(c) for c in s])

class KeyBoard:
    offset = 50; # to handle negetive!!!!
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
            for j,c in enumerate(row):
                self.layout_map[c] = (i/2,j)

    def isShift(self, c):
        p=self.layout_map[c];
        return int(self.layout_matrix[2*p[0]][p[1]] != c)

    def dist(self,p1, p2):
        dy = p2[0]-p1[0] + self.offset
        dx = p2[1]-p1[1] + self.offset
        return (dy,dx)

    def encode_keyseq( self, seq ):
        if not seq[1]: seq[1] = (0,0)
        a = (seq[1][0]<<24)|(seq[1][1]<<16)|(seq[2]<<8)|seq[3]
        return a

    def decode_keyseq( self, a ):
        return [((0xff000000&a)>>24, (0xff0000&a)>>16), (0xff00&a)>>8, 0xff&a]

    def generate_passqord_fromseq( self, seq ):
        p = ''
        for s in seq:
            p += s[0]
            pos = list(self.layout_map[s[0]])
            n = self.decode_keyseq(s[1])
            for i in range(n[2]):
                pos[0] += (n[0][0] - self.offset )
                pos[1] += (n[0][1] - self.offset )
                p += self.layout_matrix[pos[0]*2 + n[1]][pos[1]]
        return p

    def IsKeyboardSeq(self, w):
        if len(w)<5 : return 99.0, []
        M = self.layout_map
        score = 0;
        try:
            pos = [M[c] for c in w]
        except KeyError:
            return 99.0, []
        dist_pos = [self.dist(pos[i-1], pos[i]) for i in range(1,len(w))]
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
        
        weight = float(n_transition)/len(dist_pos)+float(len(w))/n_char
        seq_list = []
        if weight<1.3:
            seq = [w[0], [], self.isShift(w[0]), 0]
            for i in range(1,len(w)):
                is_shift_ = self.isShift(w[i])
                if not seq[1] and is_shift_==seq[2]:
                    seq[1] = dist_pos[i-1]
                    seq[3] += 1
                elif seq[1] != dist_pos[i-1] or seq[2] != is_shift_:
                    seq_list.append(seq)
                    seq = [w[i], [], is_shift_, 0]
                else:
                    seq[3]+=1
            if seq: seq_list.append(seq)
            for i,seq in enumerate(seq_list): 
                seq_list[i] = [seq[0], self.encode_keyseq( seq )];
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
    yy = '([4-9][0-9]|[0-3][0-9])'
    yyyy = '(19[4-9][0-9]|20[0-3][0-9])'
    mm   = '(0[0-9]|1[012])'
    mon  = '(jan | feb)' # TODO: Not sure how to handle this
    dd   = '([0-2][0-9]|3[01])'
        
    def __init__(self):
        self.date = r"""^(?P<W_s>\D*)(?P<date>
(?P<mdy>{mm}{dd}{yy})|
(?P<mdY>{mm}{dd}{yyyy})|
(?P<dmy>{dd}{mm}{yy})|
(?P<dmY>{dd}{mm}{yyyy})|
(?P<y>{yy})|
(?P<Y>{yyyy})|
(?P<YY>{yyyy}{yyyy})|
(?P<md>{mm}{dd})|
(?P<ymd>{yy}{mm}{dd})
(?P<Ymd>{yyyy}{mm}{dd})
)
(?P<W_e>\D*)$""".format(**self.__class__.__dict__)
        #self.date += "|(?P<mobno>\(\d{3}\)-\d{3}-\d{4}|\d{10}))(?P<postfix>\D*$)"
        self.Dt = re.compile(self.date, re.VERBOSE)

    def encodeDate(self):
        return ''

    def IsDate(self, s):
        m = re.match(self.Dt, s)
        if not m: return None;
        m_dict = dict((k,v) for k,v in m.groupdict().iteritems() if v and k!='date')
        
        return ['T', m_dict.keys(), m_dict.values()]

if __name__ == "__main__":
    print GrammarStructure().getTermFiles()
