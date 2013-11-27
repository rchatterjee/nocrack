
import sys, os

# helper script to mangle the letters

class NonTerminal:
    type_is = ''
    isNonT = True;
    length = 0;

    def __init__( self, _type_is, length=1, isNT=True ):
        self.type_is = _type_is;
        self.length  = length
        self.isNonT  = isNT;

    def add(self, _type_is, amt=1, isNonT=0 ):
        if ( self.type_is == _type_is and isNonT == self.isNonT ):
            self.length += amt; 
            return True;
        return False;

    def __str__(self):
        if self.type_is in ['S', 'L', 'D']:
            return "%s%d" %(self.type_is, self.length)
        else:
            return "%s<%d>" %(self.type_is, self.length)

class Mangle:
    manglingRule=dict()
    def parseManglingRules ( self, fl_name ):
        with open(fl_name) as f:
            for line in f.readlines() :
                line = line.strip();
                if not line or line[0] == '#': continue;
                line = [x.strip() for x in line.strip().split('->')]
                try:
                    self.manglingRule[line[0]].append( line[1] );
                except:
                    self.manglingRule[line[0]] = [line[1]]
    
    def loadManglingRule(self):
        m = '$@3!0'
        p = 'saeio'
        for x,y in zip(m,p):
            self.manglingRule[x] = y
        
    def __init__ ( self, 
                   fl_name = "/home/rahul/Dropbox/HoneyEncryption/ManglingRule.txt" ):
        # TODO - change this path
        #self.parseManglingRules( fl_name );
        self.loadManglingRule()
    
    def mangle( self, w ):
        ret =''
        M = []
        for i,c in enumerate(w):
            if c in self.manglingRule: 
                ret += self.manglingRule[c][0];
                M.append(NonTerminal(c,i)) 
            else: ret += c;
        return [M,ret];

    def __str__(self) :
        return '';

def getCapitalizeInfo( w ):
    info = []
    for i, c in enumerate(w):
        if c.isalpha():
            if c.isupper(): info.append(i);
    return converIntoNumber( info );

def converIntoNumber( arr ):
    """
    converts an array of indexes to a 32 bit number
    (0,2,3,9) = (9,3,2,0) = (0x00 00 02 0d) = 
    """
    a=['0' for i in range(64)];
    for x in arr:
        a[x] = '1';
    a = ''.join(a)
    return int(a,2)

def convertIntoArray( n ):
    a = reversed(bin(n)[2:])
    arr = [];
    for i in xrange(len(a)):
        if a[i] =='1': arr.append(i);
    return arr;

        
        
