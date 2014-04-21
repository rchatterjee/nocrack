from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random
from Crypto.Util import Counter
from Crypto import Random
import binascii
import re, datetime, sys, os, json
BASE_DIR = os.getcwd()  
sys.path.append(BASE_DIR)
from honeyvault_config import SECURITY_PARAM, HONEY_VAULT_ENCODING_SIZE, SECURITY_PARAM_IN_BASE64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///honeyserver.db'
db = SQLAlchemy(app)

PRIVATE_HONEY_ENC_KEY = b"trha0Hmu@!$"
PRIVATE_SALT = b"lukkaitlabon"[:8]
EMAIL_REG = re.compile( r"""
[a-z0-9!#$%&'*+?^_~-]+(?:\.[a-z0-9!#$%&'*+?^_`{|}~-]+)*
@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?
""", re.MULTILINE )

DEBUG = 1   # set it to 0 in production

b2a_base64 = lambda x: binascii.b2a_base64(x)[:-1]

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:32]

def do_crypto_setup():
    key = PBKDF1(PRIVATE_HONEY_ENC_KEY, PRIVATE_SALT, 16, 100, SHA256)
    ctr = Counter.new(8*SECURITY_PARAM, initial_value=long(254))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes

global_saltgen_aes = do_crypto_setup()
global_randfl = Random.new()

def isEmail(username):
    return (EMAIL_REG.match(username) is None)

def isBlocked(ip):
    return True

def get_public_salt(username):
    return global_saltgen_aes.encrypt(hash_mp(username))

class IPs(db.Model):
    ip = db.Column(db.String(25), primary_key=True)
    lastaccessed = db.Column(db.DateTime, default=datetime.datetime.now())
    isblocked = db.Column(db.Boolean, default=False) 

class tempUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True) # email-id is username
    email_token = db.Column(db.String(SECURITY_PARAM_IN_BASE64), nullable=False)

    def __init__(self, username):
        self.username = username
        self.email_token = b2a_base64(global_randfl.read(SECURITY_PARAM))
        print self.email_token
    
    def save(self):
        db.session.add(self)
        db.session.commit()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True) # email-id is username
    salt_pub = db.Column(db.String(SECURITY_PARAM_IN_BASE64), nullable=False)
    salt_sec = db.Column(db.String(SECURITY_PARAM_IN_BASE64), nullable=False)
    bearer_token = db.Column(db.String(SECURITY_PARAM_IN_BASE64), nullable=False)
    vault_c  = db.Column(db.String(int(HONEY_VAULT_ENCODING_SIZE*6)))
            
    def __init__(self, username):
        self.username = username
        self.salt_pub = b2a_base64(get_public_salt(username))
        self.salt_sec = b2a_base64(global_randfl.read(SECURITY_PARAM))
        self.bearer_token = b2a_base64(global_randfl.read(SECURITY_PARAM))
        self.vault_c  = b2a_base64(global_randfl.read(int(HONEY_VAULT_ENCODING_SIZE*1.4)))
        
    def __repr__(self):
        return '<User %r - <%r>>' % (self.username, self.bearer_token)

    def refresh_token(self):
        self.bearer_token = b2a_base64(global_randfl.read(SECURITY_PARAM))
        
    def save(self):
        db.session.add(self)
        db.session.commit()

def authUser(username, bearer_token):
    u = User.query.filter_by(username=username).first()
    if u and u.bearer_token == bearer_token:
        return u
    return None

def Register(username):
    if not username or not isEmail(username):
        print "<%s> is not a valid Email!" % (username)
        return "Sorry Not Valid Email"
    u = tempUser.query.filter_by(username=username).first()
    if not u:
        u = tempUser(username=username)
    u.save()
    return u.email_token

def ValidateEmail(username, email_token):
    u = tempUser.query.filter_by(username=username).first()
    if u and u.email_token == email_token:
        U = User.query.filter_by(username=username).first()
        if U:
            U.refresh_token();
        else:
            U = User(username=username)

        db.session.delete(u)
        U.save()
        return U.bearer_token 
    else:
        return "Wrong Token"

def WriteVault(username, bearer_token, vault_c):
    u = authUser(username, bearer_token)
    if u:
        u.vault_c = vault_c
        u.save()
        return "Done!"
    return "ERROR: Write is not allowed!"

# mp_hash = hash(mp, slat_pub)
def ReadVault(username, bearer_token):
    u = authUser(username, bearer_token)
    if u:
        return u.vault_c
    return 'ERROR: Read is not allowed!'

def RefreshToken(username, bearer_token):
    u = authUser(username, bearer_token)
    if u:
        u.refresh_token()
        u.save()
        return u.bearer_token
    return 'Not Permitted!'

def GetWebsiteMapping(username, bearer_token):
    u = authUser(username, bearer_token)
    if u:
        try:
            domain_list = [x.strip() for x in open(STATIC_DOMAIN_LIST)]
        except:
            domain_list = [x.strip() for x in open('server/' + STATIC_DOMAIN_LIST)]
        website_map = dict([(hash_mp(d),i) for i,d in enumerate(domain_list)])
        return website_map
    return "Sorry! Get an account first."

@app.route("/")
def hello():
    return "<h1>Hello Honey!</h1>"

@app.route("/register", methods=['POST'])
def register():
    username = request.form.get('username', '')
    return Register(username)

@app.route('/verify', methods=['POST'])
def validate_email():
    username = request.form.get('username', '')
    email_token = request.form.get('email_token', '')
    return ValidateEmail(username, email_token)

@app.route('/write', methods=['POST'])
def write_vault():
    username = request.form.get('username', '')
    bearer_token = request.form.get('token', '')
    vault_c  = request.form.get('vault_c', '')
    return WriteVault(username, bearer_token, vault_c)

@app.route('/read', methods=['POST'])
def read_vault():
    username = request.form.get('username', '')
    bearer_token  = request.form.get('token', '')
    return ReadVault(username, bearer_token)

@app.route('/refresh', methods=['POST'])
def refresh_token():
    username = request.form.get('username', '')
    bearer_token  = request.form.get('token', '')
    return RefreshToken(username, bearer_token)

@app.route('/getdomains', methods=['POST'])
def get_domain_mapping():
    username = request.form.get('username', '')
    bearer_token  = request.form.get('token', '')
    return json.dumps(GetWebsiteMapping(username, bearer_token))

if __name__ == "__main__":
    import os
    if not os.path.exists('honeyserver.db'):
        db.create_all()
    app.run(debug=True)
