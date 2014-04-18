import os, sys
import urllib, urllib2
import binascii
from Crypto.Hash import SHA256

HONEY_SERVER_URL = "http://localhost:5000/"
VAULT_FILE  = 'vault.db'
STATIC_DOMAIN_HASH_LIST = 'static_domain_hashes.txt'

def create_request(sub_url, data):
    return urllib2.Request(HONEY_SERVER_URL+sub_url,
                           urllib.urlencode(data))

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]

def register( *args ):
    h_string =  """
cmd: register
e.g. $ %s -register badger@honey.com 
""" % sys.argv[0]
    if len(args)<1:
        print h_string
        return ''
    username = args[0]
    req = create_request('register', {'username': username})
    return urllib2.urlopen(req).read()

def verify( *args ):    
    h_string =  """
cmd: verify
$ %s -verify <email> <token>
e.g. $ %s -verify badger@honey.com 'ThisIsTheToken007+3lL=' vault.hny
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''
    data = {'username' : args[0],
            'email_token' : args[1].strip("'")
            }
    req = create_request('verify', data)
    return urllib2.urlopen(req).read()


def write( *args ):    
    h_string =  """
cmd: write
$ %s -write <email> <token> <vault_file>
e.g. $ %s -write badger@honey.com 'ThisIsTheToken007+3lL='
""" % (sys.argv[0], sys.argv[0])
    if len(args)<3:
        print h_string
        return ''
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            'vault_c' : open(args[2]).read()
            }
    req = create_request('write', data)
    return urllib2.urlopen(req).read()


def read( *args ):    
    h_string =  """
cmd: read
$ %s -read <email> <token>
e.g. $ %s -v badger@honey.com 'ThisIsTheToken007+3lL='
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('read', data)
    return urllib2.urlopen(req).read()

def refresh( *args ):    
    h_string =  """
cmd: refresh
$ %s -refresh <email> <token>
e.g. $ %s -v badger@honey.com 'ThisIsTheToken007+3lL='
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('refresh', data)
    return urllib2.urlopen(req).read()


def get_static_domains( *args ):
    h_string =  """
cmd: static_domains
$ %s -getdomainhash <email> <token>
e.g. $ %s -v badger@honey.com 'ThisIsTheToken007+3lL='
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('getdomains', data)
    return urllib2.urlopen(req).read()

    
def default( *args ):
    print '\n'.join("%s - %s" % (k,v) for k,v in command_func_map.items())
    return "You are a moron!"


def add_pass( *args ):
    h_string =  """
cmd: add password
$ %s -addpass <master-password> <domain> <password>
e.g. $ %s -addpass AwesomeS@la google.com 'FckingAwesome!'
""" % (sys.argv[0], sys.argv[0])
    if len(args)<3:
        print h_string
        return ''
    
def get_pass( *args ):
    h_string =  """
cmd: get the saved password
$ %s -getpass <master-password> <domain>
e.g. $ %s -addpass AwesomeS@la google.com
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''
    mp = args[0]
    domain = hash_mp(args[1])
    index = json.load(open(STATIC_DOMAIN_HASH_LIST)).get(domain, -1)
    

def gen_pass( *args ):
    h_string =  """
cmd: generate random password
$ %s -genpass <master-password> <domain>
e.g. $ %s -addpass AwesomeS@la google.com
""" % (sys.argv[0], sys.argv[0])
    if len(args)<2:
        print h_string
        return ''

command_func_map = {
    '-register' : register,
    '-verify' : verify,
    '-write' : write,
    '-read' : read,
    '-refresh' : refresh,
    '-default' : default,
    '-getdomainhash' : get_static_domains,
    '-addpass' : add_pass,
    '-getpass' : get_pass,
    'genpass' : gen_pass,
}

if len(sys.argv)>1:
    cmd = sys.argv[1]
    print command_func_map.get(cmd, default)(*sys.argv[2:])
else:
    default( sys.argv[1:] )
