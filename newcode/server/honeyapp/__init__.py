import sys

sys.path.append('../')

from flask import Flask
from honeyvault_config import *

app = Flask(__name__)

app.secret_key = 'development key'

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'rchat@cs.wisc.edu'
app.config["MAIL_PASSWORD"] = '1233456'

from routes import mail

mail.init_app(app)

import intro_to_flask.routes
