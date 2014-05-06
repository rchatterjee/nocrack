import os, sys
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
import json
from collections import defaultdict
from sklearn import svm, preprocessing, cross_validation
import Levenshtein as lv
import numpy as np
import random
from helper.helper import get_line, open_, print_err
from dawg import IntCompletionDAWG

#
# m is always the size of the vector
# s is the size of the vault
# n is for 
#    - ngram: value of n
# ...to be completed!
#

M = 1000000
class Classifier(object):
    _name = 'Classifier'
    def __init__(self, m=5, s=2):
        self.s = s
        self.m = m
        self.db = [[],[]]
        self.n = 0
        self. clf = svm.SVC(degree=4)

    def train_with(self, json_filename, c=1):
        D = json.load(open(json_filename))
        for k,v in D.items():
            if len(v) >= self.s:
                random.shuffle(v)
                self.add_vault(v[:self.s], c)
        
    def learnNtest(self, real_vault=None, false_vault=None ):
        if real_vault:
            self.train_with(real_vault, c=1)
        if false_vault:
            self.train_with(false_vault, c=0)
        if self.db[0] and self.db[1]:
            k = self.k = min(len(self.db[0]), len(self.db[1]))
            print "Total Samples:", k
            X = np.concatenate((self.db[0][:k], self.db[1][:k]))
            X = X.astype(float)
            Y = np.append(np.zeros(k), 
                          np.ones(k))
            X_scale = preprocessing.scale(X)
            self.clf.fit(X, Y)
            self.score = cross_validation.cross_val_score(self.clf, X_scale, Y, cv=5)
            return self.score.mean(), self.score.std()

    def cross_validate(self):
        k = self.k
        random.shuffle(self.db[0])
        random.shuffle(self.db[1])
        X = np.concatenate((self.db[0][:k], self.db[1][:k]))
        X = X.astype(float)
        #X = preprocessing.scale(X)
        Y = np.append(np.zeros(k), 
                      np.ones(k))
        kf = cross_validation.KFold(k, n_folds=k, shuffle=True)        
        err = 0.
        for tr_set, ts_set in kf:
            tr_index = np.append(tr_set, tr_set+k)
            ts_index = np.append(ts_set, ts_set+k)
            X_train, X_test = X[tr_index], X[ts_index]
            Y_train, Y_test = Y[tr_index], Y[ts_index]
            self.clf.fit(X_train, Y_train)
            for p,q in zip(X_test, Y_test):
                err += abs(self.clf.predict(p)-q)
        return err/len(kf)


    def add_vault(self, vault, c=1):
        v = self.get_vault_stat(vault)
        self.db[c].append(v)

    def predict(self, vault):
        s = self.get_vault_stat(vault)
        return int(self.clf.predict(s))

class NGramProbClassifier():
    """
    This classifier uses the fact that given a password what is the probability
    that it is generated from grammar and not from real. This is more suitable for 
    single password case.
    x_i is the probability of a pw in n-gram model
    NOT SURE how to do this
    """
    _name = 'NGramProbClassifier'
    def __init__(self, n=4, train_file=None):
        self.n = n
        self.db = defaultdict(int)
        self.train(train_file)
        
    def train(self, train_file):
        if train_file:
            with open_(train_file) as f:
                self.db = IntCompletionDAWG(((pw,f) 
                                 for pw,f in get_line(f, M)))
                self.db.save('data/ngram-freq-%d.dawg' % self.n)
        else:
            self.db = IntCompletionDAWG().\
                load('data/ngram-freq-%d.dawg' % self.n)

    def get_cond_prob(self, w, c):
        w = unicode(w)
        w1 = w+c
        assert len(w) == self.n
        f_total = sum((self.db[x] for x in self.db.keys(w)))
        f = sum((self.db[x] for x in self.db.keys(w1)))
        print f_total, f
        return (f+1.0)/(f_total+1)

    def get_prob(self, pw):
        p = 1.0
        for i in range(len(pw)-self.n):
            p *= self.get_cond_prob(pw[i:i+self.n], 
                                    pw[i+self.n])
        return p


class NGramClassfier(Classifier):
    """
    - take the top m ngrams and use their probability-vec as the feature in m-dimension
    so, x_i is the probability of i-th most frequent n-gram in the vault
    """
    _name = 'NGramClassfier'
    def __init__(self, n=8, m=5, trained_file=None, training_data=None):
        super(NGramClassfier, self).__init__(m=m)
        self.n = n

    def get_vault_stat(self, vault):
        pw_set = defaultdict(int)
        for pw in vault:
            pw_set[pw] += 1
        r = defaultdict(int)
        for pw,f  in pw_set.items():
            for i in range(len(pw)-self.n+1):
                r[pw[i:i+self.n]] += f
        t = float(sum(r.values()))
        s = [x/t for p,x in sorted(r.items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)][:self.m]
        if len(s) < self.m:
            s.extend([0]*(self.m-len(s)))
        return s


class EditDistClassifier(Classifier):
    """
    - x_i is the numer of pw's which are at an editdistance of i
    """
    _name = 'EditDistClassifier'
    def __init__(self, *args, **kwargs):
        super(EditDistClassifier, self).__init__(*args, **kwargs)

    def get_vault_stat(self, vault):
        vec = [0 for i in range(self.m)]
        for i,p in enumerate(vault):
            for q in vault[i+1:]:
                d = min(lv.distance(p,q), self.m-1)
                vec[d] += 1
        return vec


class RepeatClassifier(Classifier):
    """
    - x_i is the number of pw's which are repeated i times
    """
    _name = 'RepeatClassifier'
    def __init__(self, *args):
        super(RepeatClassifier, self).__init__()
    
    def get_vault_stat(self, vault):
        vec = [0 for i in range(self.m)]
        pw_set = defaultdict(int)
        for pw in vault:
            pw_set[pw] += 1
        for k,v in pw_set.items():
            vec[min(v,self.m)-1] += 1
        return vec


if __name__ == "__main__":
    if sys.argv[1]=='-classify':
        for e in [EditDistClassifier, 
                  NGramClassfier, 
                  RepeatClassifier]:
            E = e()
            m, sd = E.learnNtest(*sys.argv[2:])
            acc = E.cross_validate()
            print E._name, acc, m, sd        
    elif sys.argv[1] == '-ngramprob':
        if len(sys.argv)>3:
            E = NGramProbClassifier(5, sys.argv[2])
            print E.get_prob(sys.argv[3])
        elif len(sys.argv)>2:
            E = NGramProbClassifier(5)
            print E.get_prob(sys.argv[2])
    else:
        e = min([EditDistClassifier, 
                 NGramClassfier, 
                 RepeatClassifier], 
                key = lambda x: lv.distance(x._name.lower(), sys.argv[1]))
        E = e()
        m, sd = E.learnNtest(*sys.argv[2:4])
        acc = E.cross_validate()
        print E._name, acc, m, sd

    # Rset = json.load(open(sys.argv[1]))
    # Dset = json.load(open(sys.argv[2]))
    # for i,v in Dset.items()[:10]:
    #     print v, E.predict(v)
    # lim = 10
    # for i,v in Rset.items():
    #     if lim < 0: break
    #     if len(v) == 5:
    #         lim -= 1
    #         print v, E.predict(v)
