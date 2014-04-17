import os, sys
import urllib, urllib2
import binascii

HONEY_SERVER_URL = "http://localhost:5000/"

def create_request(sub_url, data):
    return urllib2.Request(HONEY_SERVER_URL+sub_url,
                           urllib.urlencode(data))

def register( *args ):
    h_string =  """
cmd: register
e.g. $ %s -g badger@honey.com 
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
$ %s -v <email> <token>
e.g. $ %s -v badger@honey.com 'ThisIsTheToken007+3lL=' vault.hny
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
$ %s -v <email> <token> <vault_file>
e.g. $ %s -v badger@honey.com 'ThisIsTheToken007+3lL='
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
$ %s -v <email> <token>
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
$ %s -v <email> <token>
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

def default( *args ):
    print '\n'.join("%s - %s" % (k,v) for k,v in command_func_map.items())
    return "You are a moron!"

command_func_map = {
    '-g' : register,
    '-v' : verify,
    '-w' : write,
    '-r' : read,
    '-s' : refresh,
    '-h' : default
}

if len(sys.argv)>1:
    cmd = sys.argv[1]
    print command_func_map.get(cmd, default)(*sys.argv[2:])
else:
    default( sys.argv[1:] )
