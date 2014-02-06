import marisa_trie, json, bz2
from helper import *


T = marisa_trie.Trie().load('data/trie_rockyou-withcount.hny.bz2')

class Tweaker:
    def getTweakerRules(self, mangle_fl ):
        try: 
            rules = {}
            for l in open(mangle_fl):
                l = l.strip().split(':')
                rules[l[0]] = l[1]
        except IOError:
            print mangle_fl, '-- could not be opend! Tweaker set is empty.'
        return rules;

    def __init__(self, mangle_fl=None):
        self.rules={}
        if mangle_fl:
            self.rules = self.getTweakerRules(mangle_fl)
        
    def tweak ( self, s ):
        try:
            return self.rules[s]
        except KeyError: return s;

    def tweakW ( self, s ):
        return ''.join([self.tweak(c) for c in s])

class Tokenizer:
    def __init__( self, dictionary_fl=None, mangle_fl=None, 
                  trie=None, tweaker=None):
        Words = []
        self.M = tweaker
        if not tweaker:
            self.M = Tweaker(mangle_fl)
        self.T = trie
        if os.path.exists('data/dictionary.tri'):
            print 'Usingn the old dicrionary already stored!'
            self.T = marisa_trie.Trie().load('data/dictionary.tri')

        if not self.T:
            for line_no, line in enumerate(open_(dictionary_fl)):
                if not line or line[0] == '#' : continue
                w = line.strip().split()[-1]
                if w.isalpha(): 
                    try: w.decode('ascii')
                    except: continue; # not ascii hence return
                    Words.append(w.lower())
                    if line_no>1000000: break;
            self.T = marisa_trie.Trie(Words)
            self.T.save('data/dictionary.tri')

    # It converts the password into unmnagled version and 
    # break it into 'best' possible chunks
    def unmangleWord(self, w):
        w = w.lower();
        nw = self.M.tweakW(w)
        P = self.T.prefixes(unicode(nw))
        if not P: print 'Failed!!', w; return [w]
        P.reverse();
        # print w, '-->', P
        nWlist=[]
        for p in P:
            if len(p) == len(w): return [p];
            npw = self.unmangleWord(w[len(p):])
            if npw:
                nWlist.append(p)
                nWlist.extend(npw)
                break
        return nWlist;

        
    # Splits the word into parts, 
    # tokenize works like the following 
    # Input: Comput3rS3cret@1302 --> 
    # Output:
    # (['L8', 'L6', 'Y1', 'D4'], 
    #  [u'computer', u'secret', u'@', u'1302'], 
    #  [u'Comput3r', u'S3cret', u'@', u'1302'])
    def tokenize(self, w, isMangling=False):
        save_w=w
        T = [w]
        if isMangling:
            T = self.unmangleWord(w) # unmangled breakup
            print 'TOkenize:', T
        W = [ sym for w in T for list_match in re.findall(regex, w) 
              for sym in list_match if sym ]        
        P = [ "%s%d" % ( whatchar(x[0]), len(x)) for x in W ]
        U,s,w = [], 0, save_w
        for p in P: 
            U.append(w[s:s+int(p[1:])])
            s += int(p[1:])
        return P, W, U

def readConfigFile(cfg_fl):
    lines = [ line.strip() for line in open_(cfg_fl) 
              if line.strip() and line[0]!='#']
    return lines

class Grammar:
    inversemap = {}
    def __init__(self, config_fl=None, tokenizer=None):
        if config_fl:
            self.base_dictionary, self.tweak_fl, self.passwd_dictionary, self.out_grmmar_fl, self.out_trie_fl = readConfigFile(config_fl)
        self.tokenizer = tokenizer;
        if not tokenizer:
            self.tokenizer = Tokenizer(base_dictionary, tweak) 
        self.G={}

    def addRule(self, lhs, rhs, isNonT, freq):
        G = self.G
        # is lhs exist?
        try: x = G[lhs]
        except KeyError: # insert the lhs first
            G[lhs] = []
        try: # found in the inversemap => previous entry exist
            pos = Grammar.inversemap[rhs]
            if isNonT == 1 and G[lhs][pos][1]==0:
                G[rhs] = [G[lhs][pos][:]] # deep copy?
                G[lhs][pos][1] = True;
            G[lhs][pos][2] += freq

        except KeyError: #first time in this place
            Grammar.inversemap[rhs] = len(G[lhs])
            G[lhs].append([rhs,isNonT,freq])
        except IndexError:
            print lhs, '--->', rhs, freq
            exit()
    def insert(self, w, freq):
        P, W, U = self.tokenizer.tokenize(w)
        # print w, freq, P, W, U
        # S -> P
        self.addRule('S', ','.join(P), 1, freq)
        for i,p in enumerate(P):
            if len(W[i])>30: continue; # too big password
            if W[i] != U[i]: 
                self.addRule(p, W[i], 1, freq)
                self.addRule(W[i], U[i], 0, freq)
            else:
                self.addRule(p, W[i], 0, freq)
    
    def dotStarRules( grammar ):
        """
        This is to support parsing all possible passwords. 
        Artifical rules like, S -> L,S | D,S | Y,S
        and L -> a|b|c|d..
        D -> 1|3|4 etc
        """
        self.addRule('S', 'L1,S', 1, MIN_COUNT-1);
        self.addRule('S', 'D1,S', 1, MIN_COUNT-1);
        self.addRule('S', 'Y1,S', 1, MIN_COUNT-1);

        for c in 'abcdefghijklmnopqrstuvwxyz':     
            self.addRule('L1', c, 0, MIN_COUNT-1 )
        for d in '0123456789' :                    
            self.addRule('D1', d, 0, MIN_COUNT-1 )
        for s in '!@#$%^&*()_-+=[{}]|\'";:<,.>?/': 
            self.addRule('Y1', s, 0, MIN_COUNT-1 )
        # mangling_rule={'a':'@', 's':'$', 'o':'0', 'i':'!'}

    def save(self, out_file):
        for rule in self.G:
            self.G[rule].sort(key = lambda x: x[0])
        json.dump(self.G, out_file)
        
    def load(self, in_file):
        self.G = json.load(open_(in_file))
        # TODO - TOCHECK wheather required or not
        # for rule in self.G:
        #     for i,w in enumerate(self.G[rule]):
        #         if w[0] != rule: 
        #             inversemap[w[0]] = i
                
    # find the left most gegneration tree for a password
    # TODO -  NOT impelemetned

    def findPath(self, w):
        # tokenizer cannont be null,
        P, W, U = self.tokenizer.tokenize(w)
        # start path
        try: pos = inversemap[','.join(P)]
        except KeyError: 
            print "Falling back to all-match Rule!"
            return [] # Not implemented till now
        print pos



