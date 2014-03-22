#!/usr/bin/python

from mangle  import *
import csv
#
# ['S']  -> [('S2,S',1,20), ('L4,S',1,34),...]
# ['S2'] -> [('!!',0,12),('$%',0,23), .. ]
# ['L1'] -> [('o',0,13),('a',0,67),....]
# ['D3'] -> [('132',0,32),('123',0,23)....]
#
#          ||
#          ||
#         \  /
#          \/
#
# After the preprocessing is done this grammar is to converted,s.t.
# Every rule, will contain the the CDF instead of probability
#

'''
gives what type of character it is.
Letter: L, Capitalized: C
Digit: D, Symbol: S
ManglingRule: M
'''
###################### --NEW VERSION-- ###################################


def buildpcfg(config_fl):
    base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(config_fl)
    root_fl = open('roots.txt', 'w')
    if os.path.exists(out_trie_fl) and os.path.exists(out_grammar_fl):
        print "The grammar(%s) and trie(%s) already exist! Not recreating. remove to force." % ( out_grammar_fl, out_trie_fl)
        # return;
    T = Tokenizer(base_dictionary, tweak_fl)
    G = Grammar(tokenizer=T)
    # resource track
    resource_tracker = 5240
    allowed_sym = re.compile(r'[ \-_]')
    print re.findall(allowed_sym, 'P@ssword')
    for n, line in enumerate(open_(passwd_dictionary)):
        if n>resource_tracker:
            r = MEMLIMMIT*1024 - resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
            print "Memory Usage:", (MEMLIMMIT - r/1024.0), "Lineno:", n
            if r < 0:
                print '''
Hitting the memory limit of 1GB,
please increase the limit or use smaller data set.
Lines processed, {0:d}
'''.format(n)
                break;
            resource_tracker += r/10+100;
        # if n%1000==0: print n;
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w, c = ' '.join(line[1:]), int(line[0])
        else:
            continue
            w, c = ' '.join(line), 1
        try:
            w.decode('ascii')
        except UnicodeEncodeError:
            continue    # not ascii hence return
        if c < MIN_COUNT or (len(w) > 2 and not w[:-2].isalnum() and len(re.findall(allowed_sym, w)) == 0):
            print "Word frequency dropped to %d for %s" % (c, w), n
            break  # Careful!!!
        t = G.insert(w, c)
        # print t
        root_fl.write("%s\t<>\t%s\n" % (' '.join(line), '~'.join(t)))
        
    # TODO
    #push_DotStar_IntoGrammar( grammar );
    root_fl.close(); exit(0)
    G.save(bz2.BZ2File(out_grammar_fl, 'w'))
    marisa_trie.Trie(Grammar.inversemap.keys()).save(out_trie_fl)
    return G


def breakwordsintotokens(config_fl):
    """
    Takes a password list file and break every password into possible tokens,
    writes back to a output_file, named as <input_fl>_out.tar.gz,in csv format.
    """
    base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(config_fl)
    out_file_name = 'data/'+basename(passwd_dictionary).split('.')[0]+'_out.tar.gz'
    print passwd_dictionary, out_file_name
    output_file = open(out_file_name, 'wb')
    csv_writer = csv.writer(output_file, delimiter=',',
                            quotechar='"')
    T = Tokenizer(base_dictionary, tweak_fl)
    G = Grammar(tokenizer=T)
    # resource track
    resource_tracker = 5240
    for n, line in enumerate(open_(passwd_dictionary)):
        if n>resource_tracker:
            r = MEMLIMMIT*1024 - resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
            print "Memory Usage:", (MEMLIMMIT - r/1024.0), "Lineno:", n
            if r < 0:
                print """
Hitting the memory limit of 1GB,
please increase the limit or use smaller data set.
Lines processed, %d
""" % n
                break
            resource_tracker += r/10+100
        # if n%1000==0: print n;
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w, c = ' '.join(line[1:]), int(line[0])
        else:
            continue
            w, c = ' '.join(line), 1
        try:
            w.decode('ascii')
        except UnicodeDecodeError:
            continue     # not ascii hence return
        if c < MIN_COUNT/100:
            break
        # P is the patterns, W is the unmangled words, U is the original
        wt, s = T.keyboard.IsKeyboardSeq(w)
        if s: 
            for l in s:
                print l
        continue 
        # print t
        if P:
            csv_writer.writerow([c, w, str(W)])
        else:
            print 'Failed to Parse:', w
        # root_fl.write("%d,\'%s\t<>\t%s\n" % ( ' '.join(line), '~'.join(((t)))))
        
    # TODO
    #push_DotStar_IntoGrammar( grammar );
    output_file.close()

if __name__ == "__main__":
    #G = buildpcfg(sys.argv[1])
    #print G
   base_dictionary, tweak_fl, passwd_dictionary, out_grammar_fl, out_trie_fl = readConfigFile(sys.argv[1])
   T = Tokenizer(base_dictionary, tweak_fl)
   for w in ['~~~1234567879!@~abc', 'iloveyou@2013', '121293', 'ihateyou', 'eeyore', 'fuckyou1', 'C0mput3rS3cr3t@1032'
, 'lovendall', 'fuckyou1', 'derek2'][:4]:
       print T.tokenize(w, True)
    #D = MobileN();
    #print D.parse('ram1992');
    # K = KeyBoard();
    # for l in sys.stdin:
    #     #    print l.strip(), '-->', T.tokenize(l.strip(), True)[2];
    #     l = l.strip().split()
    #     if len(l)<1: print l; continue
    #     w, s = K.IsKeyboardSeq(l[0])
    #     if s:
    #         p = K.generate_passqord_fromseq(s)
    #         if p != l[0]:
    #             print "ERROR:",  l[0], w, [], p
    #breakwordsintotokens(sys.argv[1])
    








