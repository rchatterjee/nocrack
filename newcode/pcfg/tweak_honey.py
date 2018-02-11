from honey_enc import *


class NumArr:
    def __init__(self, _n=[]):
        self.NumArr = _n
        self.currIndex = 0

    def __next__(self):
        currIndex += 1;
        if (currIndex == len(NumArr)): return -1;
        return self.NumArr[currIndex - 1];


N_arr = None;


def same(x):
    return x;


def gen_pass(x):
    return x


def mingle(p_word):
    if (len(p_word) == 1):
        return getGenerationAtRule(p_word, next(N_arr), grammar)
    return ''.join([mingle(c) for c in p_word])


def postfix(x):
    P, W, U = tokenizer.tokenize(x, True)
    return x


def prefix(x):
    return x


def loadtweakProb(tFile='password_tweak.txt'):
    for l in open(tFile):
        l = l.strip().split(':')


def tweak(password, tweaks):
    """
    tokenize
    for each tweak, apply accordingly
    """


Tweaks = {
    'capitalize': str.capitalize,
    'uppercase': str.upper,
    'postfix': postfix,
    'prefix': prefix,
    'mingle': mingle,
    'new': gen_pass,
    'same': same
}


def checkNums():
    x = getNextNumber()
    print(x, end=' ')


    if __name__ == "__main__":
        NumArr = list(range(100))
        n = 10;
        while (n > 0):
            print(checkNums());
            n -= 1;
