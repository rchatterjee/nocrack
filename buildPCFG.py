#!/usr/bin/python

import csv, sys, os, re, bz2
from honeyvault_config import GRAMMAR_DIR, MIN_COUNT, MEMLIMMIT
from scanner.scanner_helper import GrammarStructure
from scanner.scanner import Scanner, Grammar
from helper.helper import open_
import resource  # For checking memory usage
import marisa_trie

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


def buildpcfg(passwd_dictionary):
    G = Grammar()
    # resource track
    resource_tracker = 5240
    allowed_sym = re.compile(r'[ \-_]')
    out_grammar_fl = GRAMMAR_DIR + '/grammar.cfg'
    for n, line in enumerate(open_(passwd_dictionary)):
        if n>resource_tracker:
            r = MEMLIMMIT*1024 - \
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;
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
        except UnicodeDecodeError:
            continue    # not ascii hence return
        if c < MIN_COUNT*20 : # or (len(w) > 2 and not w[:-2].isalnum() and len(re.findall(allowed_sym, w)) == 0):
            print "Word frequency dropped to %d for %s" % (c, w), n
            break  # Careful!!!
        G.insert(w, c)
        # print t
        # root_fl.write("%s\t<>\t%s\n" % (' '.join(line), '~'.join(str((x,y)) for x,y in zip(W, Tag))))
        
    # TODO
    #push_DotStar_IntoGrammar( grammar );
    G.update_total_freq()
    G.save(bz2.BZ2File(out_grammar_fl, 'w'))
    #marisa_trie.Trie(Grammar.inversemap.keys()).save(out_trie_fl)
    return G


def breakwordsintotokens(passwd_dictionary):
    """
    Takes a password list file and break every password into possible tokens,
    writes back to a output_file, named as <input_fl>_out.tar.gz,in csv format.
    """
    # for the direcotry
    if not os.path.exists(GRAMMAR_DIR):
        os.mkdir(GRAMMAR_DIR)
    G_out_files = dict()
    for k, f in GrammarStructure().getTermFiles().items():
        G_out_files[k] = os.path.join(GRAMMAR_DIR, f)
    Arr = {}
    for k in G_out_files.keys():
        Arr[k] = dict()
    out_file_name = 'data/'+os.path.basename(passwd_dictionary).split('.')[0]+'_out.tar.gz'
    print passwd_dictionary, out_file_name
    output_file = open(out_file_name, 'wb')
    csv_writer = csv.writer(output_file, delimiter=',',
                            quotechar='"')
    T = Scanner()
    # G = Grammar(scanner=T)
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
        if c < MIN_COUNT*10:
            break
        # P is the patterns, W is the unmangled words, U is the original
        Tags, W, U  = T.tokenize(w, True) 
        # print t
        if 'password' in w:
            print Tags, W
        if Tags:
            for t,w in zip(Tags, W):
                try:
                    Arr[t][w] += c
                except KeyError:
                    try: Arr[t][w] = c
                    except KeyError:
                        print "Something is wrong:", Tags, W
            csv_writer.writerow([c, w, str(Tags), str(W), str(U)])
        else:
            print 'Failed to Parse:', w
    for k, D in Arr.items():
        T = marisa_trie.Trie(D.keys())
        T.save(G_out_files[k] + '.tri')
        n = len(D.keys())+1
        A = [0 for i in xrange(n)]
        s = 0
        for w,c in D.items():
            i = T.key_id(unicode(w))
            try: 
                A[i] =  c
                s += c
            except IndexError: 
                print "IndexError", w
        A[-1] = s
        with open(G_out_files[k] + '.py', 'w') as f:
            f.write('%s = [' % k)
            f.write(',\n'.join(['%d' % x for x in A]))
            f.write(']\n')
        # root_fl.write("%d,\'%s\t<>\t%s\n" % ( ' '.join(line), '~'.join(((t)))))
        
    # TODO
    #push_DotStar_IntoGrammar( grammar );
    output_file.close()

def main():
    if len(sys.argv)<2 or sys.argv[0] in ['-h', '--help']:
        print '''Taste the HoneyVault1.1 - a New Password Encrypting paradigm!
This is the PCFG generator script! Are you sure you wanna use this script.
--build-dawg password_leak_file
--build-pcfg password_leak_file
--build-all password_leak_file
        '''
    else:
        if sys.argv[1] == '--build-dawg': breakwordsintotokens( sys.argv[2] )
        elif sys.argv[1] == '--build-pcfg': buildpcfg( sys.argv[2] )
        elif sys.argv[1] == '--build-all':  
            breakwordsintotokens( sys.argv[2] )
            buildpcfg( sys.argv[2] )
        else: print "Sorry Hornet! Command not recognised."
        


if __name__ == "__main__":
    main()
    #G = buildpcfg(sys.argv[1])
    #print G
    
    #T = Scanner()
    #for w in ['~~~1234567879!@~abc', 'iloveyou@2013', '121293', 'ihateyou', 'eeyore', 'fuckyou1', 'C0mput3rS3cr3t@1032', 'lovendall', 'fuckyou1', 'derek2', 'cutiepie1230', 'password1']:
    #       print T.tokenize(w, True)
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
    # buildpcfg(sys.argv[1])
    # G = Grammar()
    # G.load(GRAMMAR_DIR+'grammar.cfg')
    # print G.G



    



