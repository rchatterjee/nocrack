from flask.ext.sqlalchemy import SQLAlchemy
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Random import random, Random
from Crypto.Util import Counter
from Crypto import Random
from binascii import hexlify
import re, datetime
from flask import Flask, request

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

PRIVATE_HONEY_ENC_KEY = b"trha0Hmu@!$"
PRIVATE_SALT = b"lukkaitlabon"
EMAIL_REG = re.compile( r'''
[a-z0-9!#$%&\'*+?^_~-]+(?:\.[a-z0-9!#$%&\'*+?^_`{|}~-]+)*
@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?
''', re.MULTILINE )

def hash_mp(mp):
    h = SHA256.new()
    h.update(mp)
    return h.hexdigest()[:16]

def do_crypto_setup():
    key = PBKDF1(PRIVATE_HONEY_ENC_KEY, PRIVATE_SALT, 16, 100, SHA256)
    ctr = Counter.new(128, initial_value=long(254))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes

global_saltgen_aes = do_crypto_setup()
global_randfl = Random.new()

def get_public_salt(username):
    return global_saltgen_aes.encrypt(hash_mp(username))

class IPs(db.Model):
    ip = db.Column(db.String(25), primary_key=True)
    lastaccessed = db.Column(db.Datetime, null=True, default=datetime.now())
    isblocked = db.Column(db.Boolean, default=False) 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True) # email-id is username
    salt_pub = db.Column(db.String(128), null=False)
    salt_sec = db.Column(db.String(128), null=False)
    token    = db.Column(db.String(128), null=False)
    vault_c  = db.Column(db.LargeBinary(HONEY_VAULT_ENCODING_SIZE))
            
    def __init__(self, username):
        self.username = username
        self.salt_pub = get_public_salt(username)
        self.salt_sec = global_randfl.read(16)
        self.vault_c  = global_randfl.read(HONEY_VAULT_ENCODING_SIZE)
        self.token    = global_randfl.read(128)
        
    def __repr__(self):
        return '<User %r>' % self.username

    def save(self):
        db.session.add(self)
        db.session.commit()

def isEmail(username):
    return EMAIL_REG.match(username)

def isBlocked(ip):
    return True

def GetToken(username):
    if not isEmail(username):
        pass
    u = User(username=username)
    u.save()
    return u.token

def Insert(username, token, mp_hash, vault=None):
    u = User.query.filter_by(username=username)
    if u and u.token == token:
        if not vault:
            vault = global_randfl.read(HONEY_VAULT_ENCODING_SIZE)
            key = PBKDF1(mp_hash, u.salt_sec, 16, 100, SHA256)
            ctr = Counter.new(128, initial_value=long(254))
            aes = AES.new(key, AES.MODE_CTR, counter=ctr)
        u.vault = aes.encrypt(vault)
        u.save()

def GetPubSalt(username):
    return get_public_salt(username)


def GetWebsiteMapping():
    website_map = {
        'account.google.com' : 1
        'yahoo.com' : 2,
        'facebook.com': 3
        }
    return json.encode( website_map );

# mp_hash = hash(mp, slat_pub)
def Retrieve(username, mp_hash):
    u = User.query.filter_by(username=username)
    if u:
        key = PBKDF1(mp_hash, u.salt_sec, 16, 100, SHA256)
        ctr = Counter.new(128, initial_value=long(254))
        aes = AES.new(key, AES.MODE_CTR, counter=ctr)
        return aes.decrypt(u.vault_c)


@app.route("/")
def hello():
    return "<h1>Hello Honey!</h1>"

@app.route("/gettoken", methods=['GET'])
def get_token(username):
    username = request.args.get('username', '')
    print GetToken(username)

@app.route('/insert', methods=['POST'])
def insert():
    username = request.form.get('username', '')
    token    = binascii.a2b_base64(request.form.get('token', ''))
    mp_hash  = binascii.a2b_base64(request.form.get('mp_hash', ''))
    vault_c  = binascii.a2b_base64(request.form.get('vault_c', '')) 
    Insert(username, token, mp_hash, vault_c)

@app.route('/retrive', methods=['GET'])
def retrive():
    username = request.args.get('username', '')
    mp_hash  = binascii.a2b_base64(request.form.get('mp_hash', ''))
    print binascii.b2a_base64(Retrieve(username, mp_hash))


if __name__ == "__main__":
    app.run(debug=True)
