#from inventoryapp import app
from flask import current_app as app
from flask_oauth import OAuth
from flask import render_template, redirect, url_for, request, jsonify, flash, session

import requests
import json


GOOGLE_WELL_KNOWN = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_CLIENT_ID = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_secret']

def get_google_info():
    r = requests.get(GOOGLE_WELL_KNOWN)
    return r.json()

ginfo = get_google_info()

oauth = OAuth()

google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    request_token_url=None,
    access_token_url=ginfo['token_endpoint'],
    authorize_url=ginfo['authorization_endpoint'],
    request_token_params={'scope': 'email',
                          'response_type': 'code'},
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET)

@app.route('/login')
def login():
    res =  google.authorize(callback=url_for('oauth_authorized', _external=True))
    return res

@google.tokengetter
def get_google_token(token=None):
    return session.get('google_token')

@app.route('/authorized')
@google.authorized_handler
def oauth_authorized(resp):

    next_url = request.args.get('next') or url_for('index')

    if resp is None:

        flash(u'Request to sign in was denied by the user.')
        return redirect(next_url)

    session['google_token'] = (resp['access_token'], '')
    session['google_token_expires'] = resp['expires_in']

    print "*** response id_token:"
    print resp['id_token']


    flash('You were signed in')
    return redirect(next_url)