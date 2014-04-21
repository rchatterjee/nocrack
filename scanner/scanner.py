#!/usr/bin/python
import os, sys
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG
from dawg import DAWG
import struct, json, bz2, re
from helper.helper import open_
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from scanner_helper import Tweaker, GrammarStructure
from collections import OrderedDict, defaultdict
from pprint import pprint

#--------------------------------------------------------------------------------
class Scanner:
    d_w_d = re.compile(r"""(?P<pre>[^a-zA-Z]*)
(?P<word>[a-zA-Z]*)
(?P<post>[^a-zA-Z]*)
""", re.MULTILINE)
    non_alphabet = re.compile(r'^[^a-zA-Z]+$')

    def __init__( self, dawg=None, tweaker=None):
        self.dawg = dawg
        # TODO add these facilities later
        #self.keyboard = KeyBoard()
        #self.date = Date()
        #self.standard_english = None;
        self.M = tweaker or Tweaker()
        if not self.dawg and \
                os.path.exists(hny_config.DICTIONARY_DAWG):
            # print 'Using the old dicrionary already stored!'
            self.dawg = DAWG()
            self.dawg.load(hny_config.DICTIONARY_DAWG)
        if not self.dawg:
            print """Oh My God!! You dont have the dictionary({DICTIONARY_DAWG}). \
                I can't take it. Exiting!""".format(**locals())
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
            # Dont do any fansy unmangling now..:P
            T = self.unmangle_word(w) # unmangled breakup
            #T = [ sym for w in T for list_match in re.findall(regex, w) 
            #      for sym in list_match if sym ]
            if not T: T = [w]
            # print 'TOkenize:', T

        # The Dumbest Grammar one can think of,. But just to complete the pipeline
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

    def get_parse_tree(self, w):
        T, W, U = self.tokenize(w, True)
        rule = ','.join(T)
        G = defaultdict(dict)
        G['G'][rule] = [0,NONTERMINAL]
        for i,t in enumerate(T):
            l = t
            r1 = W[i]
            r2 = U[i]
            if r1 == r2:
                G[l][r1] = [0, TERMINAL ]
            else:
                G[l][r1] = [0, NONTERMINAL ]
                for c,d in zip(r1,r2):
                    G[c][d] = [0, TERMINAL]
                
        # TODO - make it better with Capitalization,
        # AllCaps, L33t etc.
        return G

#--------------------------------------------------------------------------------
class Grammar:
    def __init__(self, config_fl=None, scanner=None):
        self.scanner = scanner if scanner else Scanner()
        self.grammar_structure = GrammarStructure().G
        self.G = defaultdict(OrderedDict)
        # for k,v in self.grammar_structure.items():
        #     if len(v)!=1: 
        #         self.G[k] = OrderedDict([(x, [0, (NONTERMINAL if x.isupper() 
        #                                           else TERMINAL)
        #                                       ]) 
        #                                  for x in v])
                
        # self.addDotStarRules();
        # TODO: make it better
        from string import ascii_lowercase, digits, punctuation
        for typ, characters in zip('LDY', [ascii_lowercase, digits, punctuation]): 
            self.G[typ] = OrderedDict([(x, [MIN_COUNT-1, TERMINAL]) 
                                       for x in characters])
            self.G['G']['%s,G' % typ] = [MIN_COUNT-1, NONTERMINAL]

    def addRule_lite(self, lhs, rhs, freq, typ, 
                     ignore_addingfreq = False): # typ is NONTERMINAL or NERMINAL
        if ignore_addingfreq:
            self.G[lhs].setdefault(rhs, [freq,typ])
        else:
            self.G[lhs].setdefault(rhs, [0,typ])
            self.G[lhs][rhs][0] += freq
            
    def update_total_freq(self):
        for lhs, rhs_dict in self.G.items():
            rhs_dict['__total__'] = sum([x[0]
                                         for x in rhs_dict.values()
                                         if type(x)==type([])])

    def parse_pw(self, pw):
        return self.scanner.tokenize(pw)

    def get_freq_range(self, lhs, rhs):
        rhs_dict = self.G[lhs]
        try:
            i = rhs_dict.keys().index(rhs)
            l = 0;
            l += sum([rhs_dict[x][0] 
                      for x in rhs_dict.keys()[:i]])
            r = l + rhs_dict[rhs][0]
            return l, r   # range is [l,r), r not included rember
        except ValueError:
            print "Could not find ", lhs, rhs, "in G!"
            print rhs_dict
            return -1, -1

    def get_rhs(self, lhs, pt):
        rhs_dict = self.G[lhs]
        t = 0
        pt %= rhs_dict['__total__']
        for r, v in rhs_dict.items():
            t += v[0]
            if t > pt: break
        if t > rhs_dict['__total__']:
            print "Could not Find: ", lhs, pt
            return None, 0, TERMINAL
        return r, v[0], v[1]

    def update_grammar(self, G1=None, pw=None):
        print "Updating with", pw 
        if not G1:
            G1 = self.scanner.get_parse_tree(pw)
        for lhs,rhs in G1.items():
            self.G[lhs].update(rhs)
            if '__total__' in self.G[lhs]:
                del self.G[lhs]['__total__']
            self.G[lhs]['__total__'] = \
                sum([x[0] for x in self.G[lhs].values()])

    def fix_freq(self, pcfg):
        for l,r_dict in self.G.items():
            for r, v in r_dict.items():
                if r != '__total__':
                    v[0] = pcfg.get_freq(l,r)
        print "Fixing frequencies:", '*'*20
        self.update_total_freq()

    # Completely messed up now
    def insert(self, w, freq):
        P, W, U = self.scanner.tokenize(w, True)
        # TODO Add mangling
        # Improve the grammar
        rule = ','.join(P)
        self.addRule_lite('G', rule, freq, NONTERMINAL)
        for l,r in zip(W,U):
            if l != r:
                for c,d in zip(l,r):
                    self.addRule_lite(c, d, freq, TERMINAL)

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


    def save(self, out_file):
        json.dump(self.G, out_file)
        
    def load(self, in_file):
        self.G = json.load(open_(in_file), 
                           object_pairs_hook=OrderedDict)
        
    def __eq__(self, o_g):
        return self.G == o_g.G

    def __iter__(self):
        return self.G.iterator
    
    def __getitem__(self, key):
        return self.G[key]
    
    def __contains__(self, x):
        return x in self.G
    
    def __str__(self):
        s = "Grammar: "
        s += '\n'.join('%s -> %s' %(k, str(v)) 
                  for k, v in self.G.items()
                       if k not in ['L', 'D', 'Y'])
        return s

    def findPath(self, w):
        # scanner cannont be null,
        P, W, U = self.scanner.tokenize(w)
        # start path
        try: pos = inversemap[','.join(P)]
        except KeyError: 
            print "Falling back to all-match Rule!"
            return [] # Not implemented till now
        print pos



