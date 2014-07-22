#!/usr/bin/python

"""
This script generates the complete PCFG usable for 
honey encryption. The inputs to this script are,
a) vault file b) password leak file (if not provided
the vault password distribution is used.) c) test the accuracy or not 
etc.
"""

#import sys, os, math, struct, bz2, resource
#BASE_DIR = os.getcwd()
#sys.path.append(BASE_DIR)
import string, os, sys, json
from helper.helper import open_
from collections import defaultdict
from lexer.lexer import parallel_buildpcfg
from lexer.pcfg import TrainedGrammar
from analysis_tools.classifier import Experiment
from vaultanalysis.train_vault_dist import cal_size_subG, cal_stat
from analysis_tools.gen_decoy_data import decoy_vault_random

PW_TMP_FILE = 'pw_set_tmp.txt'
def create_pcfg(vault_leak, password_leak=None):
    # learn the grammar
    vault_d = json.load(open(vault_leak))
    print "# of vaults: ", len(vault_d)
    print "max size of vault:", max(len(x) for x in vault_d.values())
    print "max size of vault:", min(len(x) for x in vault_d.values())

    if not password_leak:
        D = defaultdict(int)
        for k,v in vault_d.items():
            if len(v)>40: continue
            for x in v:
                D[x] += 1
        password_leak = PW_TMP_FILE 
        with open(password_leak, 'w') as f:
            f.write('\n'.join(
                    '%d\t%s' % (f,p) 
                    for p,f in sorted(D.items(), key=lambda x: x[1],
                                      reverse=True))
                    )
        print "Password file created"
    parallel_buildpcfg(password_leak)

    # learn the vault distribution
    tg = TrainedGrammar()
    G = cal_size_subG(tg, vault_leak)
    f = os.tmpfile()
    json.dump(G, f)
    f.seek(0)
    cal_stat(fds=[f])
    f.close()


def test(vault_leak):
    trn_fl = 'analysis_tools/decoy_trn.txt'
    tst_fl = 'analysis_tools/decoy_tst.txt'
    length_dist = defaultdict(int)
    D = json.load(open(vault_leak))
    for k,v in D.items():
        length_dist[len(v)] += 1
    if 1 in length_dist:
        del length_dist[1]
    s = max(length_dist.values())
    json.dump(decoy_vault_random(n=1000, s_max=s, length_dist=length_dist), 
              open(trn_fl, 'w'), indent=2)
    json.dump(decoy_vault_random(n=1000, s_max=s, length_dist=length_dist), 
              open(tst_fl, 'w'), indent=2)
    for s,t in [(2,4), (5,8), (9,40), (4,40)]:
        Experiment(
            _s=s,
            _t=t,
            trn_fl=trn_fl,
            tst_fl=tst_fl,
            vault_fl=vault_leak,
            plot_graph=True)


def main():
    if len(sys.argv)<2 or sys.argv[1] == '-help':
        print """This script will (should) generate all the static required files
for honey encryption. options are '-vault' <vault-file> '-pwfile' <pw-file> -test
'-pwfile' and '-test' are optional arguments. If '-test' option is provided it will
test the security of the newly created pcfg using the SVM classifier."""
        exit(0)
    vault_fl = None
    pw_fl = None
    istest = False
    if '-test' in sys.argv:
        istest = True
    try:
        i = sys.argv.index('-vault')
        vault_fl = sys.argv[i+1]
        if '-pwfile' in sys.argv:
            i = sys.argv.index('-pwfile')
            pw_fl = sys.argv[i+1]
    except:
        print "Sorry you have to specify vault file with '-vault' option!"
    print "---\nVault: %s\nPwFile: %s\ntest: %s\n----" % (
        vault_fl, pw_fl, istest)
    if  istest:
        create_pcfg(vault_fl, pw_fl)
    if istest:
        test(vault_fl)
main()
