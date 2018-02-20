"""This scripts utilizes functions provided by lexer to build a PCFG grammar.
"""
import os, sys
import argparse
from helper import open_, load_dawg, check_resource, isascii
from pcfg.lexer_helper import Date, RuleSet, ParseTree
import honeyvault_config as hny_config
from honeyvault_config import MIN_COUNT
from pcfg.lexer import parse
import gzip

def buildpcfg(passwd_dictionary, start=0, end=-1,
              outf=hny_config.TRAINED_GRAMMAR_FILE):
    # MIN_COUNT=1000
    R = RuleSet()
    # resource track
    resource_tracker = 5240
    for n, line in enumerate(open_(passwd_dictionary, 'r')):
        try:
            line = line.decode('utf-8')
        except UnicodeDecodeError:
            print("Cannot decode: {}".format(line))
            continue
        if n < start: continue
        if n > end: break
        if n > resource_tracker:
            l = check_resource(n)
            if not l:
                break
            else:
                resource_tracker += l
        # if n%1000==0: print n;
        line = line.strip().split()
        if len(line) > 1 and line[0].isdigit():
            w, c = ' '.join(line[1:]), int(line[0])
        else:
            continue
            w, c = ' '.join(line), 1
        # not ascii hence return
        if not isascii(w):
            continue
        if c < MIN_COUNT:  # or (len(w) > 2 and not w[:-2].isalnum() and len(re.findall(allowed_sym, w)) == 0):
            print("Word frequency dropped to %d for %s" % (c, w), n)
            break  # Careful!!!
        T = parse(w)
        R.update_set(T.rule_set(), with_freq=True, freq=c)

    if not outf:
        return R
    else:
        R.save(gzip.open(outf, 'wt'))


def wraper_buildpcfg(args):
    return buildpcfg(*args)


def parallel_buildpcfg(password_dictionary, n_cnt=1e6):
    from multiprocessing import Pool
    p = Pool()
    n_cnt = int(n_cnt)
    Complete_grammar = RuleSet()
    load_each = 10000
    a = [(password_dictionary, c, c + load_each, None)
         for c in range(0, n_cnt, load_each)]
    R = p.map(wraper_buildpcfg, a)
    for r in R:
        Complete_grammar.update_set(r, with_freq=True)
    Complete_grammar.save(gzip.open(hny_config.TRAINED_GRAMMAR_FILE, 'wt'))


def parse_args():
    parser = argparse.ArgumentParser(description='PCFG lexer module')
    parser.add_argument('--buildG', metavar="fname", action='store',
                        help="Build a PCFG from the given file")
    parser.add_argument('--parallel', action='store_true',
                        help="buildG parallely utilizing"
                        "all cores available in the machine")
    parser.add_argument('--parse', metavar="word", nargs='+',
                        help="Parse the given password")

    parser.add_argument('--parsef', metavar="word", nargs='+',
                        help="Parse all the passwords in the file")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    print(args)
    if args.buildG:
        fname = args.buildG
        if args.parallel:
            parallel_buildpcfg(fname, 1e3)
        else:
            buildpcfg(fname, 0, 1e6)
    elif args.parse:
        for w in args.parse:
            T = parse(w)
            print("Parsing: {}\nParse-tree: {},\nSmallGrammar: {}".format(
                w, T.parse_tree(), T.rule_set()
            ))

    elif args.parsef:
        fname = args.parsef
        R = RuleSet()
        with open_(fname) as f:
            for i, line in enumerate(f):
                if i < 5000: continue
                l = line.strip().split()
                w, c = ' '.join(l[1:]), int(l[0])
                try:
                    w.decode('ascii')
                except UnicodeDecodeError:
                    continue  # not ascii hence return
                if not w or len(w.strip()) < 1:
                    continue
                T = parse(w)
                R.update_set(T.rule_set(), with_freq=True, freq=c)
                if i % 100 == 0: print(i)
                if i > 5200: break
        print(R)
