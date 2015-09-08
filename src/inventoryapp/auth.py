from flask_oauth import OAuth
from flask import session


GOOGLE_CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('client_secrets.json', 'r').read())['web']['client_secret']


