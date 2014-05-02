from honey_vault import vault_encode
from honey_enc import *
from buildPCFG import *


S = Scanner()
dte = DTE()
G = Grammar()

def generate_sub_grammar( vault ):
    global S, dte, G
    G.G = {}    
    # sub-grammar generation
    for v in set(vault): # bring in Vault distribution
        T, W, U = S.tokenize(v, True)
        rule = ','.join(T)
        f = dte.get_freq('G', rule)
        if f[0]==-1 or f[1]==-1:
            return None
        G.addRule_lite('G', rule, f[0], f[1], True )
        for (l,r) in zip(T,W):
            f = dte.get_freq(l, r)
            if f[0] ==-1 or f[1]==-1:
                return None
            G.addRule_lite(l, r, f[0], f[1], True )
    return G

def calculate_vault_distribution( vault_file ):
    with open(vault_file) as f:
        for l in f:
            v = [x.strip("'") for x in l.strip().split(',')]
            if len(v)<5: continue   #discard small vault size <=4
            g = generate_sub_grammar( v )
            if g:
                print "-->",v, '\n', g
            else:
                print "xxx>", v 

if __name__=='__main__':
    calculate_vault_distribution( sys.argv[1] )
