import os, sys
import urllib, urllib2
import binascii
from Crypto.Hash import SHA256
from urlparse import urlparse
from publicsuffix import PublicSuffixList
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
from dte.honey_vault import HoneyVault
import json#, unittest

HONEY_SERVER_URL = "http://localhost:5000/"
VAULT_FILE  = 'static/vault.db'
STATIC_DOMAIN_HASH_LIST = 'static_domain_hashes.txt'
b2a_base64 = lambda x: binascii.b2a_base64(x)[:-1]

def create_request(sub_url, data):
    return urllib2.Request(HONEY_SERVER_URL+sub_url,
                           urllib.urlencode(data))

def get_exact_domain( url ):
    psl = PublicSuffixList()
    url = url.strip()
    u = urlparse(url)
    h = u.hostname
    if not h:
        h = url
    return psl.get_public_suffix(h)

def get_exact_domains( urllist ):
    return [get_exact_domain(url) 
            for url in urllist]
     
def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]


# ---------------- Client command line functions ------------------
def register( *args ):
    h_string =  """
register
./honey_client -register <email-id>
$ ./honey_client -register badgeremail@wisc.edu
"""
    if len(args)<1:
        return h_string
    username = args[0]
    req = create_request('register', {'username': username})
    return urllib2.urlopen(req).read()


def verify( *args ):    
    h_string =  """
verify your email id. token you will get in your email after '-register'
./honey_client -verify <email> <token>
$ ./honey_client -verify badger@honey.com 'ThisIsTheToken007+3lL=' vault.hny
"""
    if len(args)<2:
        return h_string
    data = {'username' : args[0],
            'email_token' : args[1].strip("'")
            }
    req = create_request('verify', data)
    return urllib2.urlopen(req).read()


def write( *args ):    
    h_string =  """
write/upload your vault on the server
./honey_client -write <email> <token> <vault_file>
$ ./honey_client -write badger@honey.com 'ThisIsTheToken007+3lL='
"""
    if len(args)<3:
        return h_string
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            'vault_c' : b2a_base64(open(args[2]).read())
            }
    print data['token']
    print data['vault_c'][:10]
    req = create_request('write', data)
    return urllib2.urlopen(req).read()


def read( *args ):    
    h_string =  """
read your vault from the server.
./honey_client -read <email> <token>
$ ./honey_client -v badger@honey.com 'ThisIsTheToken007+3lL='
"""
    if len(args)<2:
        return h_string
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('read', data)
    d = urllib2.urlopen(req).read()
    if not d.startswith('ERROR'):
        open(VAULT_FILE, 'wb').write(binascii.a2b_base64(d))
        return "Saved in %s" % VAULT_FILE
    else:
        return d

def refresh( *args ):    
    h_string =  """
refresh your token. If you dont have access to the account 
for some reason (adversary has changed the token) reregister yourself.
It will refresh the token and you will get back your vault.
./honey_client -refresh <email> <last-token>
e.g. ./honey_client -v badger@honey.com 'ThisIsTheToken007+3lL='
"""
    if len(args)<2:
        return h_string
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('refresh', data)
    return urllib2.urlopen(req).read()


def get_static_domains( *args ):
    h_string =  """
get the mapping of domains to index. Advanced level command!
./honey_client -getdomainhash <email> <token>
e.g. ./honey_client -v badger@honey.com 'ThisIsTheToken007+3lL='
"""
    if len(args)<2:
        return h_string
    data = {'username' : args[0],
            'token' : args[1].strip("'"),
            }
    req = create_request('getdomains', data)
    return urllib2.urlopen(req).read()


def add_pass( *args ):
    h_string =  """
Add password to your vault. It will automatically initialize the vault.
If you get some error, just delete the static/vault.db (if you dont have any password)
Or download a copy from the server. 
./honey_client -addpass <master-password> <domain> <password>
e.g. ./honey_client -addpass AwesomeS@la google.com 'AmzingP@ss'
"""
    if len(args)<3:
        return h_string
    mp = args[0]
    domain_pw_map = {get_exact_domain(k):v
                     for k,v in zip(args[1::2], args[2::2])}
    hv = HoneyVault(VAULT_FILE, mp)
    hv.add_password(domain_pw_map)
    y = raw_input(""" Check the following sample decoded password and make sure your master
password is correct. Otherwise you might accidentally spoile your whole
vault. CAREFUL.  SAMPLE PASSWORDS:\n---> %s Are all of the correct to the best of
your knowledge! (y/n)""" % \
                      '\n---> '.join(hv.get_sample_decoding()))    
    if y.lower() == 'y':
        hv.save()
        return """
Successfully saved your vault.  Now when you are sure the update is correct upload the vault to the server. 
we are not doing automatically because I DONT BELEIVE MYSELF"""
    else:
        return "As you wish my lord!"

def get_pass( *args ):
    h_string =  """
get the saved password for a domain
./honey_client -getpass <master-password> <domain>
e.g. ./honey_client -getpass AwesomeS@la google.com
"""
    if len(args)<2:
        return h_string
    mp = args[0]
    hv = HoneyVault(VAULT_FILE, mp)
    return json.dumps(hv.get_password(get_exact_domains(args[1:])), indent=4)


def import_vault( *args ):
    h_string =  """
import existing vault, in given format
./honey_client -import <master-password> <vault_file>
e.g. ./honey_client -import AwesomeS@la vault_file.csv
vault file:
# domain,username?,password
google.com,rahulc@gmail.com,abc234
fb.com,rchatterjee,aadhf;123l
"""
    if len(args)<2:
        return h_string
    mp = args[0]
    vault_fl = args[1]
    g = lambda l: (l[0],l[-1])
    domain_pw_map = dict([ g(a.strip().split()) 
                           for a in open(vault_fl) if a[0] != '#'])
    hv = HoneyVault(VAULT_FILE, mp)
    hv.add_password(domain_pw_map)
    y = raw_input("""
Check the following sample decoded passwords and make sure your master password
 is correct. Otherwise you might accidentally spoile your whole vault. CAREFUL.
 Ignore if this is the first time you are using this.  SAMPLE PASSWORDS: %s Are
 all of the correct to the best of your knowledge! (y/n)""" % \
                      ','.join(hv.get_sample_decoding())
                  )    
    if y.lower() == 'y':
        hv.save()
        print """
Successfully saved your vault. 
Now when you are sure the update is correct upload the vault to the 
server. we are not doing automatically because I dont beleive myself
"""
    

def export_vault( *args ):
    h_string =  """
export the vault, 
NOTE: this might generate some extra password which does not belong to you.
Dont panic, those are randomly generated for security purpose. 
Also for s2 part we need the cache, if it is not complete you will miss
some in the export file, though the passwords are there in the vault.
./honey_client -export <master-password>
e.g. ./honey_client -export AwesomeS@la
"""
    if len(args)<2:
        return h_string
    mp = args[0]
    domain = hash_mp(get_exact_domains(args[1]))
    index = json.load(open(STATIC_DOMAIN_HASH_LIST)).get(domain, -1)
    

def gen_pass( *args ):
    h_string =  """
generate random password
./honey_client -genpass <master-password> <domain>
e.g. ./honey_client -addpass AwesomeS@la google.com
"""
    if len(args)<2:
        return h_string
    mp = args[0]
    domain_list = args[1:]
    hv = HoneyVault(VAULT_FILE, mp)
    return json.dumps(hv.gen_password(mp, domain_list), indent=4)

def get_all_pass( *args ):
    h_string =  """
Prints all the password in the vault
./honey_client -getall <master-password> 
e.g. ./honey_client -getall AwesomeS@la
"""
    if len(args)<1:
        return h_string
    mp = args[0]
    hv = HoneyVault(VAULT_FILE, mp)
    return '\n'.join(str(s) for s in hv.get_all_pass())

def default( *args ):
    print "That was not a correct set of argument(s). The allowed set of arguments are following"
    print '\n'.join("%s : %s" % (k,v().split('\n')[1]) 
                    for k,v in command_func_map.items() 
                    if k != '-help' )
    return "Write any of the option to know about their requirements!"
    
        
command_func_map = {
    '-register': register,
    '-verify': verify,
    '-write': write,
    '-read': read,
    '-refresh': refresh,
    '-help': default,
    '-getdomainhash': get_static_domains,
    '-addpass': add_pass,
    '-getpass': get_pass,
    '-genpass': gen_pass,
    '-import': import_vault,
    '-export': export_vault,
#    '-test': unittest.main,
    '-getall': get_all_pass
}

    

if __name__ == "__main__":
    if len(sys.argv)>1:
        cmd = sys.argv[1]
        print command_func_map.get(cmd, default)(*sys.argv[2:])
    else:
        default( sys.argv[1:] )
