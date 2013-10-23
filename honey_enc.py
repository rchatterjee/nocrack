#!/usr/bin/python

"""
This script implements HoneyEncription class for password vauld.
it needs a PCFG in the following format.

"""

import sys, os
from io import BytesIO
import struct


# m is any passwrd
def Encode( m ):

    return m


# TODO: every array in grammar rule should have start with a dummy entry('',0,0) and prob zero!!
def getIndex(arr, s, e, prob ):
    if e-s==1:
        if arr[s][2] <= prob and arr[e][2] > prob: return e;
    if arr[(s+e)/2] == prob: return (s+e)/2+1;
    if arr[(s+e)/2][2] < prob: return getIndex( arr, (s+e)/2+1, e, prob)
    return getIndex( arr, s, (s+e)/2, prob)

def getGenarationAtRule( rule, prob):
    # returns: ('IloveYou',0,420)
    t = getIndex ( grammar[rule], prob );
    return grammar[rule][t]

# c is of the form set of numbers... 
# probabilities, CDF
def Decode ( c ):
    # c is io.BytesIO
    t = len( c );
    p = struct.unpack('%dd'%(t/8), c)
    word=[('S',1)]; # 1 NonT, 0 T
    # queue
    i = 0; k = len(word);
    plaintext = '';
    while i<k:
        g = getGenerationAtRule( word[i], p[i] );
        if g[1] == 1:
            word.extend(g[0].split(','))
            k = len(word):
        elif g[1] == 2: # mangling rule;
            print " I don't know"
        else: # zero, terminal add 
            plaintext += w[0];


def writePasswords ( p ):
    # writes the encoded passwords.. 
    f = open("password_vault.hny", 'w')
