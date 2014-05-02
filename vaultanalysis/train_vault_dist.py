import os, sys, string
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG, DAWG
import marisa_trie
import struct, json, bz2, re
from helper.helper import open_, getIndex, convert2group
from Crypto.Random import random
import honeyvault_config as hny_config
from honeyvault_config import NONTERMINAL, TERMINAL, MIN_COUNT
from honeyvault_config import MEMLIMMIT, GRAMMAR_DIR
from collections import OrderedDict, defaultdict
from pprint import pprint
from lexer.pcfg import TrainedGrammar, SubGrammar

NT =  ['G', 'R', 'W', 'Y', 'D', 'T', 'T_y', 'T_Y', 'T_m', 'T_d']

def cal_size_subG(base_pcfg, vault_set_file):
    tdata = [(k,filter(lambda x: x, v)) 
                 for k,v in json.load(open(vault_set_file)).items()
                 if len(filter(lambda x: x, v))>1]
    rm = []
    for x in tdata:
        k, v = x
        for p in v:
            try: p.decode('ascii')
            except:
                rm.append(k); 
                continue
    sys.stderr.write(' '.join([str(x) for x in rm]))
    data = dict(filter(lambda x: x not in rm, tdata))
    D = {}
    for k,v in data.items():
        g = SubGrammar(base_pcfg)
        g.update_grammar(*v)
        res = [(nt, len(g[nt])-1) 
               for nt in NT]
        D[k] =  {'vault': v, 'length': len(v)}
        D[k].update(dict(res))
    return D

def draw(G, fname='plot.png'):
    import pylab
    p = {}
    for nt,v in G.items():
        p[nt] = pylab.plot(v.keys(), v.values(), 
                           label=nt)
    pylab.legend()
    pylab.savefig(fname)
    pylab.close()

def cal_stat( fds=[], fnames=[] ):
    V = {}
    R = [[] for n in NT]
    if not fds:
        fds = [open_(f) for f in fnames]
    for fn in fds:
        print fn.name
        for k,v in json.load(fn,
                             object_pairs_hook=OrderedDict).items():
            if v['length']>50: continue
            k = ','.join(str(x) for x in [ v["length"]]+ \
                             [max(v.get(nt,0),0) for nt in NT])
            if k not in V:
                for i,nt in enumerate(NT):
                    if v.get(nt,-1) > 0:
                        R[i].append(v[nt])
                V[k] = [max(v.get(nt, -1),0) for nt in NT]
    
    G = defaultdict(dict)
    for i,nt in enumerate(NT):
        for f in R[i]:
            G[nt][f] = G[nt].get(f, 0) + 1

    # s = [sum(R[i])/float(len(R[i])) for i in range(len(NT))]
    print G.keys()
    for k,v in G.items():                              
        if len(v)<30:                 
            for i in range(1,len(v)+30):   
                v[i] = 5*v.get(i, 1) 
    json.dump(G, open(GRAMMAR_DIR+'vault_dist.cfg', 'wb'),
              indent=2, separators=(',',':'), sort_keys=True)


if __name__=="__main__":
    if sys.argv[1] == '-process':
        tg = TrainedGrammar()
        print json.dumps(cal_size_subG(tg, sys.argv[2]), indent=2)
    elif sys.argv[1] == '-stat':
        # give the vaultcleaned files, 
        cal_stat(fnames=sys.argv[2:])
    elif sys.argv[1] == '-default':
        tg = TrainedGrammar()
        files = ["data_vault/%s_vaultcleaned.json" % x 
                 for x in ['joe', 'weir']]
        G = {}
        for f in files:
            G.update(cal_size_subG(tg, f))
        f = os.tmpfile()
        json.dump(G, f)
        f.seek(0)
        cal_stat(fds=[f])
        f.close()
        
