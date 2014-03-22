#!/usr/bin/python

from dawg import IntDAWG
from dawg import DAWG
 
import struct, json, bz2
from helper import *


class Scanner:
    d_w_d = re.compile(r'(?P<pre>[^a-zA-Z]*)(?P<word>[a-zA-Z]*)(?P<post>[^a-zA-Z]*)')
    non_alphabet = re.compile(r'^[^a-zA-Z]+$')

    def __init__( self, dictionary_fl=None, mangle_fl=None, 
                  trie=None, tweaker=None):
        Words = []
        self.M = tweaker
        if not tweaker:
            self.M = Tweaker(mangle_fl)
        self.T = trie
        self.keyboard = KeyBoard()
        self.date = Date()
        self.standard_english = None;

        if os.path.exists(DIC_TRIE_FILE):
            # print 'Using the old dicrionary already stored!'
            self.T = marisa_trie.Trie().load(DIC_TRIE_FILE)
            self.standard_english = marisa_trie.Trie().load(STANDARD_DIC_FILE)

        if not self.T:
            print "Oh My God!! You dont have the dictionary({DIC_TRIE_FILE}). I can't take it. Exiting!".format(**locals())
            exit(0);


    # scores how good is the chunking
    def score(self, orig, wlist):
        dic_words = filter(lambda x: unicode(x) in self.standard_english, wlist )
        num_words = filter(lambda x : re.match(self.non_alphabet, x) is not None, wlist)
        # t_d = float(sum([len(x) for x in dic_words]))/(0.1+len(dic_words))+1
        # t_all = len(orig)/len(wlist)
        # t_last = (0 if re.match(self.non_alphabet, wlist[-1]) is None else 1)
        # t_last+= (0 if re.match(self.non_alphabet, wlist[0] ) is None else 1)
        non_dic_words = 2*len(wlist)-len(num_words)-len(dic_words)
        scr = - non_dic_words #float(t_d)+t_all + t_last + (len(wlist) - len(dic_words) - len(num_words))
        #print 'Score:', wlist, scr
        return scr

    # It converts the password into unmnagled version and 
    # break it into 'best' possible chunks
    def unmangleWord(self, w, pre=''):
        if re.match(self.non_alphabet, w): return [w]
        if len(w)>6 and len(set(w))<=2: return None
        if len(w)==1:
            return None if w.isalpha() and w not in ['i', 'a'] else [w]
        
        w = w.lower();
        nw = self.M.tweak(w) if len(w)>1 else w
        P = self.T.prefixes(unicode(nw))
        if not P:
            #print 'Failed!!', w; 
            return [w]
        if len(P)<=1 and P[0].isalpha() and (len(w) - len(P[-1]))*2>len(w):
            # print "Couldnot find!", w, '-->', P
            return None
        P.sort(key = lambda x: len(x)*(1+(x in self.standard_english)), reverse=True)
        #print pre+w+str(P)
        nWlist=[]
        oWlist=[[], -99]
        test = 0;
        for p in P:
            npw = '<3>';
            if len(p) < len(w): 
                npw = self.unmangleWord(w[len(p):], pre+'++')
            if npw:
                nWlist.append(p)
                if npw != '<3>': nWlist.extend(npw)
                s = self.score(w, nWlist) + 1.0/(test+5)
                if s>oWlist[1]:
                    oWlist = [nWlist, s]
                    #print pre+"Changing: "+str(oWlist)
                nWlist = []
                if test>2 or len(p) == len(w): break
                test+=1
        #if oWlist[0]: print pre+"returning==>", oWlist, [nWlist, s]
        return oWlist[0];

        
    # Splits the word into parts, 
    # tokenize works like the following 
    # Input: Comput3rS3cret@1302 --> 
    # Output:
    # (['L8', 'L6', 'Y1', 'D4'], 
    #  [u'computer', u'secret', u'@', u'1302'], 
    #  [u'Comput3r', u'S3cret', u'@', u'1302'])
    def tokenize(self, w, isMangling=False):
        #s = self.keyboard.IsKeyboardSeq(w)
        if s: return ['K%d'%len(s)], s, [w]
        grp = self.date.IsDate(w)
        if grp:
            print grp
            # w1,w2=grp[0], grp[1]
            # dt, mob=grp[2], grp[3]
            # if dt: 'T'
            # R1, R2=[[],[],[]], [[],[],[]]
            # if w1: R1 = tokenize(w1, isMangling)
            # if w2: R2 = tokenize(w2, isMangling)
            # print 'Mobmatch:', w1, dt, mob, w2
        else:
            pass
            #print "not Date"
        save_w=w
        T = [w]
        #m = re.match(self.d_w_d, w)        
        if isMangling:
            T = self.unmangleWord(w) # unmangled breakup
            if not T: T = [w]
            # print 'TOkenize:', T
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
        self.addDotStarRules();

    def addRule(self, lhs, rhs, isNonT, freq):
        G = self.G
        # is lhs exist?
        try: x = G[lhs]
        except KeyError: # insert the lhs first
            G[lhs] = []
        try: # found in the inversemap => previous entry exist
            if len(rhs)>1:
                pos = Grammar.inversemap[rhs]
            else:
                pos = -1;
                for i,x in enumerate(G[lhs]):
                    if rhs == x[0]:
                        pos = i;
                        break
            if pos==-1: G[lhs].append([rhs, isNonT, freq])
            else: G[lhs][pos][2] += freq

        except KeyError: #first time in this place
            Grammar.inversemap[rhs] = len(G[lhs])
            G[lhs].append([rhs,isNonT,freq])
        except IndexError:
            print 'IndexERROR:', lhs, '--->', rhs, freq
            for k,v in G.items(): print k, '=>', v
            exit()

    def insert(self, w, freq):
        P, W, U = self.tokenizer.tokenize(w, True)
        # print w, freq, P, W, U
        # S -> P
        self.addRule('S', ','.join(P), 1, freq)
        for i,p in enumerate(P):
            if len(W[i])>30: continue; # too big password
            # first add the nonterminal word
            if W[i].isalpha():
                self.addRule(p, W[i], 2, freq) # word NT- Complicated!
                for w,u in zip(W[i],U[i]):
                    self.addRule(w, u, 0, freq)
            else:
                self.addRule(p, W[i], 0, freq)
        # print 'insert: ', U
        return U

    def addDotStarRules(self):
        """
        This is to support parsing all possible passwords. 
        Artifical rules like, S -> L,S | D,S | Y,S
        and L -> a|b|c|d..
        D -> 1|3|4 etc
        """
        self.addRule('S', 'L1,S', 1, MIN_COUNT-1);
        self.addRule('S', 'D1,S', 1, MIN_COUNT-1);
        self.addRule('S', 'Y1,S', 1, MIN_COUNT-1);

        for i in range(26):     
            c = chr(ord('a')+i)
            self.addRule('L1', c, 0, MIN_COUNT-1 )
            self.addRule(c, c.upper(), 0, MIN_COUNT-1 )
            self.addRule('L1', c.upper(), 0, MIN_COUNT-1 )
            
            
        for d in '0123456789' :                    
            self.addRule('D1', d, 0, MIN_COUNT-1 )
        for s in '!@#$%^&*()_-+=[{}]|\'";:<,.>?/': 
            self.addRule('Y1', s, 0, MIN_COUNT-1 )
        for e, s in self.tokenizer.M.rules.items():
            self.addRule(s, e, 0, MIN_COUNT-1)
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



