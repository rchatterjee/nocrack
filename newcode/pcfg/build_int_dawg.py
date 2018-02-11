import os, sys

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dawg import IntDAWG
import marisa_trie
import struct, json, bz2, re
from helper import open_

sum_freq = 0


def get_f_w_freq(line):
    """
    <freq> <word>
    format
    """
    x = line.strip().split()
    global sum_freq
    sum_freq += int(x[0])
    return x[1], int(x[0])


def get_wiki_freq(line):
    """
    <rank> <word> <freq>
    """
    x = line.strip().split()
    global sum_freq
    sum_freq += int(float(x[2]))
    return x[1], int(float(x[2]))


def get_w_f_freq(line):
    """
    <word>  <freq> 
    format
    """
    x = line.strip().split()
    global sum_freq
    sum_freq += int(x[1])
    return x[0], int(x[1])


def get_file_data_format(format):
    if (format[0] == 'word' and
                format[1] == 'freq'):
        return get_w_f_freq
    if (format[0] == 'freq' and
                format[1] == 'word'):
        return get_f_w_freq
    if (format[0] == 'rank' and
                format[1] == 'word' and
                format[2] == 'freq'):
        return get_wiki_freq
    else:
        return get_f_w_freq


def build_int_dawg(filename):
    with open_(filename) as inpf:
        freq_style = get_f_w_freq
        f_line = inpf.readline()
        w = []
        if f_line.startswith('#'):
            words = f_line.strip().split()
            freq_style = get_file_data_format(words[1:])
        else:
            w = [freq_style(f_line)]
        w.extend([freq_style(line)
                  for line in inpf])
        w.append(('__total__', sum_freq))
        int_dawg = IntDAWG(w)
        of = filename.split('.')[0] + '.dawg'
        with open(of, 'wb') as o:
            int_dawg.write(o)
        test_dawg(of, w[:10] + w[-10:])


def test_dawg(filename, wlist):
    d = IntDAWG()
    d = d.load(filename)
    for w in wlist:
        assert w[1] == d[str(w[0])]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Provide the input file name")
    else:
        build_int_dawg(sys.argv[1])
