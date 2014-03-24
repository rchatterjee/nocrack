#!/usr/bin/python

from dawg import IntDAWG
from dawg import DAWG
 
import struct, json, bz2
from helper import *
from honeyvault_config import *
from scanner_helper import *


class Scanner:
    d_w_d = re.compile(r'(?P<pre>[^a-zA-Z]*)(?P<word>[a-zA-Z]*)(?P<post>[^a-zA-Z]*)')
    non_alphabet = re.compile(r'^[^a-zA-Z]+$')

    def __init__( self, dawg=None, tweaker=None):
        self.dawg = dawg
        # TODO add these facilities later
        #self.keyboard = KeyBoard()
        #self.date = Date()
        #self.standard_english = None;
        self.M = tweaker or Tweaker()
        if not self.dawg and os.path.exists(DICTIONARY_DAWG):
            # print 'Using the old dicrionary already stored!'
            self.dawg = DAWG()
            self.dawg.load(DICTIONARY_DAWG)
        if not self.dawg:
            print "Oh My God!! You dont have the dictionary({DICTIONARY_DAWG}). I can't take it. Exiting!".format(**locals())
            exit(0);
        self.infix = '@._*'

    # scores how good is the chunking
    def score(self, orig, wlist):
        return sum([len(w)*len(w) for w in wlist])
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
    def unmangle_word(self, w, pre=''):
        if re.match(self.non_alphabet, w): return [w]
        if len(w)>6 and len(set(w))<=2: return None
        
        #nw = w
        w = w.lower();
        nw = self.M.tweak(w) if len(w)>1 else w
        P = self.dawg.prefixes(unicode(nw))
        if not P:
            # print 'Failed!!', w; 
            return [w]
        if len(P)<=1 and P[0].isalpha() and (len(w) - len(P[-1]))*2>len(w):
            # print "Couldnot find!", w, '-->', P
            return None
        #P.sort(key = lambda x: len(x)*(1+(x in self.standard_english)), reverse=True)
        P.sort(key = lambda x: len(x), reverse = True)
        #print pre+w+str(P)
        nWlist=[]
        oWlist=[[], -99]
        test = 0;
        for p in P:
            npw = '<3>';
            if len(p) < len(w): 
                npw = self.unmangle_word(w[len(p):], pre+'++')
            if npw:
                nWlist.append(p)
                if npw != '<3>': nWlist.extend(npw)
                s = self.score(w, nWlist)
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
        # if s: return ['K%d'%len(s)], s, [w]
        #grp = self.date.IsDate(w)
        #if grp:
        #    print grp
        #    # w1,w2=grp[0], grp[1]
        #    # dt, mob=grp[2], grp[3]
        #    # if dt: 'T'
        #    # R1, R2=[[],[],[]], [[],[],[]]
        #    # if w1: R1 = tokenize(w1, isMangling)
        #    # if w2: R2 = tokenize(w2, isMangling)
        #    # print 'Mobmatch:', w1, dt, mob, w2
        #else:
        #    pass
        #    #print "not Date"
        save_w=w
        T = [w]
        # print self.unmangle_word(w)
        #m = re.match(self.d_w_d, w)        
        if isMangling:
            T = self.unmangle_word(w) # unmangled breakup
            if not T: T = [w]
            # print 'TOkenize:', T

        # Dumbest Grammar one can think of,. But just to complete the pipeline
        # will come an reiterate later
        # if len(T) > 5: 
        #     print "Say something, I am giving upon you:", w, T; 
        #     return None, None
        Tags = [None for i in range(len(T)+2)]
        Tags[0] = '^'
        Tags[-1] = '$'
        for i, w in enumerate(T): 
            if len(w)>4: Tags[i+1] = 'W'

        if None in Tags:
            if len(Tags) == 3: Tags[1] = 'W'
            elif not all(Tags):            
                for i, w in enumerate(T): 
                    if len(w)>3: Tags[i+1] = 'W'
                    
            conversion_rules = { '^' : { 'W' : 'P', None : 'W' },
                                 'W' : { 'P' : 'S', 'W' : 'S', '$' : 'S', None: 'S' },
                                 'S' : { 'W' : 'P', 'P' : 'I', None: 'W', '$': 'P'}
                                 }                             
            for i, t in enumerate(Tags[1:-1]):
                if t: continue;
                if not i:
                    if len(T[i]) >= 4: Tags[i+1] = 'W'
                try: 
                    Tags[i+1] = conversion_rules[Tags[i]][Tags[i+2]]
                except KeyError or IndexError:
                    print Tags, T
                    
        # for i, t in enumerate(Tags):
        # W = [ sym for w in T for list_match in re.findall(regex, w) 
        #       for sym in list_match if sym ]
        # P = [ "%s%d" % ( whatchar(x[0]), len(x)) for x in W ]
        U,s,w = [], 0, save_w
        for p in T: 
             U.append(w[s:s+len(p)])
             s += len(p)
        return Tags[1:-1], T, U

class Grammar:
    inversemap = {}
    def __init__(self, config_fl=None, scanner=None):
        self.scanner = scanner;
        if not scanner:
            self.scanner = Scanner() 
        self.grammar_structure = GrammarStructure().G
        self.G={}
        for k,v in self.grammar_structure.items():
            if len(v)!=1: 
                keys = v
                freq = [[0, (NONTERMINAL if x.isalpha() else TERMINAL)] for x in v]
                self.G[k] = [keys, freq, 0]
                
        # self.addDotStarRules();
        # TODO: make it better
        from string import ascii_letters, digits, punctuation
        for typ, characters in zip('LDY', [ascii_letters, digits, punctuation]): 
            self.G[typ] = [[x for x in characters], [[MIN_COUNT-1, TERMINAL] for x in characters], 0]
            self.G['G'][0].append('%s,G' % typ)
            self.G['G'][1].append([MIN_COUNT-1, NONTERMINAL])
            self.G['G'][2] += MIN_COUNT-1

    def addRule_lite( self, lhs, rhs, freq, typ, ignore_addingfreq = False): # typ is NONTERMINAL or NERMINAL
        G = self.G
        try:
            i = G[lhs][0].index(rhs)
            if not ignore_addingfreq:
                G[lhs][1][i][0] += freq
                G[lhs][2] += freq
        except ValueError: 
            self.G[lhs][0].append(rhs)
            self.G[lhs][1].append([freq, typ])
            self.G[lhs][2] += freq
        except KeyError:
            G[lhs]=[[rhs], [[freq,  typ]], freq]
            
            
            
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


    # Completely messed up now
    def insert(self, w, freq):
        P, W, U = self.scanner.tokenize(w, True)
        # TODO Add mangling
        # Improve the grammar
        rule = ','.join(P)
        self.addRule_lite('G', rule, freq, NONTERMINAL)
        # print w, freq, P, W, U
        # S -> P
        # self.addRule('S', ','.join(P), 1, freq)
        # for i,p in enumerate(P):
        #     if len(W[i])>30: continue; # too big password
        #     # first add the nonterminal word
        #     if W[i].isalpha():
        #         self.addRule(p, W[i], 2, freq) # word NT- Complicated!
        #         for w,u in zip(W[i],U[i]):
        #             self.addRule(w, u, 0, freq)
        #     else:
        #         self.addRule(p, W[i], 0, freq)
        # print 'insert: ', U

    def addDotStarRules(self):
        """
        This is to support parsing all possible passwords. 
        Artifical rules like, S -> L,S | D,S | Y,S
        and L -> a|b|c|d..
        D -> 1|3|4 etc
        """
        self.addRule('G', 'L,G', 1, MIN_COUNT-1);
        self.addRule('G', 'D,G', 1, MIN_COUNT-1);
        self.addRule('G', 'Y,G', 1, MIN_COUNT-1);
        import string
        for c in string.ascii_letters:
            self.addRule('L', c, 0, MIN_COUNT-1 )
        for d in string.digits:
            self.addRule('D', d, 0, MIN_COUNT-1 )
        for s in string.punctuation:
            self.addRule('Y', s, 0, MIN_COUNT-1 )
        #for e, s in self.scanner.M.rules.items():
        #    self.addRule(s, e, 0, MIN_COUNT-1)
        # mangling_rule={'a':'@', 's':'$', 'o':'0', 'i':'!'}

    def save(self, out_file):
        #for rule in self.G:
        #    self.G[rule].sort(key = lambda x: x[0])
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


    def __iter__(self):
        return self.G.iterator
    
    def __getitem__(self, key):
        return self.G[key]
    
    def __contains__(self, x):
        return x in self.G
    
    def __str__(self):
        return str(self.G)

    def findPath(self, w):
        # scanner cannont be null,
        P, W, U = self.scanner.tokenize(w)
        # start path
        try: pos = inversemap[','.join(P)]
        except KeyError: 
            print "Falling back to all-match Rule!"
            return [] # Not implemented till now
        print pos



