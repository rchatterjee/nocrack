import sys, os, re
import bz2;

# dictionary info
d_list = [ x.strip() for x in open('./testdiclist.txt').readlines()]
DIR = '/home/rahul/Desktop/Acads/AdvanceComputerSecurity/PasswordDictionary/passwords/'
lengths = {
    '500-worst-passwords.txt.bz2': 500,
    'alypaa-withcount.txt.bz2': 1384,
    'elitehacker-withcount.txt.bz2': 895,
    'rockyou-withcount.txt.bz2': 14344391,
    'porn-unknown-withcount.txt.bz2': 8089,
    'hotmail-withcount.txt.bz2': 8931,
    'carders.cc-withcount.txt.bz2': 1904,
    'facebook-phished-withcount.txt.bz2': 2441,
    'phpbb-withcount.txt.bz2': 184389,
    'yahoo-withcount.txt.bz2': 342517,
    'singles.org-withcount.txt.bz2': 12234,
    'faithwriters-withcount.txt.bz2': 8347,
    'combined-withcout.txt.bz2': 5142440,
    'tuscl-withcount.txt.bz2': 38820,
    'honeynet-withcount.txt.bz2': 226928,
    'hak5-withcount.txt.bz2': 2351
}

# print "Dictionary Info:"
# for d in d_list:
#     t = len(bz2.BZ2File(DIR+d).readlines())
#     print d, '\t', t
#     lengths[d] = t

info = {}
regx1 = r'--------- ../PasswordDictionary/passwords/(.*) ---------- :.*|>>>>>Total: (\d+)|>>>>>Failed: (\d+)'

prog = re.compile(regx1);
stat = {}
for d1 in d_list:
    for d2 in d_list:
        stat[(d1,d2)] = [0,0]

for d in d_list:
    _d = d
    d = d.replace('.txt.bz2', '.txt')
    with open('logfile_'+d) as f:
        d2 = []
        for line in f:
            res = prog.match(line)
            if res:
                res = res.groups()
                if res[0]: 
                    # print d2
                    if d2: stat[(_d,d2[0])] = [int(d2[1]), int(d2[2])]
                    d2 = [res[0]] 
                else: 
                    if res[1]: d2.append ( res[1] )
                    elif res[2]: d2.append ( res[2] )
        if d2: stat[(_d,d2[0])] = [int(d2[1]), int(d2[2])]

for i,x in enumerate(d_list):
    print '%2d' % (i+1), x, lengths[x];
print '--'*10

print '  ', ' '.join(['  DICT%2d ' % i for i in range(1,17)])
for i,d1 in enumerate(d_list):
    print '%2d' % (i+1), ' '.join( [ "%4d/%-4d" % ( stat[(d1,d2)][1], stat[(d1,d2)][0] ) for d2 in d_list] )

