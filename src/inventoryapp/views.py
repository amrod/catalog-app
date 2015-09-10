from inventoryapp import app
from inventoryapp import db
from inventoryapp import lm

from flask import render_template, redirect, url_for, request, jsonify, flash, session, make_response
from forms import NewMaskForm, EditMaskForm, AddCardsForm, TransferCardsForm, EmptyTrashForm
from flask_oauth import OAuth
from flask.ext.login import current_user, login_user, logout_user, login_required

import models
from models import User, Mask, Transaction

from oauth2client.client import verify_id_token, Error as Oauth2clientError

import json
import requests
from datetime import datetime

class M:
    pass

JSON_CT = {'Content-Type': 'application/json'}
GOOGLE_ISS = ('accounts.google.com', 'https://accounts.google.com')
GOOGLE_WELL_KNOWN = 'https://accounts.google.com/.well-known/openid-configuration'
GOOGLE_TOKEN_INFO ='https://www.googleapis.com/oauth2/v1/tokeninfo'
GOOGLE_USER_INFO = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_REVOKE = 'https://accounts.google.com/o/oauth2/revoke'
GOOGLE_CLIENT_ID = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_secret']

lm.login_view = 'index'

ginfo = requests.get(GOOGLE_WELL_KNOWN).json()

oauth = OAuth()

google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    request_token_url=None,
    access_token_url=ginfo['token_endpoint'],
    authorize_url=ginfo['authorization_endpoint'],
    request_token_params={'scope': 'openid email profile',
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
    return session.get('access_token')

@app.route('/authorized')
@google.authorized_handler
def oauth_authorized(resp):

    next_url = url_for('index')

    if resp is None:

        flash(u'Request to sign in was denied by the user.', 'error')
        return redirect(next_url)

    # print resp

    try:
        jwt = verify_id_token(resp['id_token'], GOOGLE_CLIENT_ID)
    except Oauth2clientError as err:
        flash(u'Invalid token.', 'error')
        return redirect(next_url)

    fmsg = None

    # Verify that the access token is valid for this app.
    if jwt.get('aud') != GOOGLE_CLIENT_ID:
        fmsg = make_flash_params(u"Token's client ID does not match app's.", 'error')

    if jwt.get('iss') not in GOOGLE_ISS:
        fmsg = make_flash_params(u"Invalid token issuer.", 'error')

    # Check is user is already signed in.
    stored_token = session.get('access_token')
    stored_gplus_id = session.get('gplus_id')

    if stored_token is not None and jwt.get('sub') == stored_gplus_id:
        fmsg = make_flash_params(u'Current user is already connected.', 'error')

    if fmsg is None:
        # No errors up to this point, user can be authenticated
        session['name'] = jwt.get('name')
        session['picture'] = jwt.get('picture')
        session['email'] = jwt.get('email')
        session['token_expires'] = jwt.get('exp')
        session['access_token'] = resp['access_token']

        user = models.load_user(session)

        if user:
            login_user(user, remember=True)  # To manage logged in users with Flask-Login
            fmsg = make_flash_params(u'You were signed in as %s.' % jwt.get('name'))
        else:
            reset_user_session_vars(session)
            fmsg = make_flash_params(u'Error registering user %s in the database.' % jwt.get('name'), 'error')

    flash(**fmsg)
    return redirect(next_url)

@app.route('/logout')
@login_required
def logout():

    access_token = session.get('access_token')
    result = None
    fmsg = None

    if access_token is None:
        fmsg = make_flash_params(u'Current user not connected.')
    else:
        params = {'token': access_token}
        result = requests.get(GOOGLE_REVOKE, params=params)

    if result and result.status_code == requests.codes.ok:
        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()

        reset_user_session_vars(session)
        logout_user()  # To manage logged in users with Flask-Login

        fmsg = make_flash_params(u'Successfully disconnected.')

    elif result:
        # For whatever reason, the given token was invalid.
        fmsg = make_flash_params(u'Failed to revoke token for given user.', 'error')

    if fmsg:
        flash(**fmsg)

    return redirect(url_for('index'))

def reset_user_session_vars(session):
    # Reset the user's session variables
    session.pop('name', None)
    session.pop('picture', None)
    session.pop('email', None)
    session.pop('token_expires', None)
    session.pop('access_token', None)

def make_flash_params(message, category='message'):
    return {'message': message, 'category': category}

@app.route('/inventory')
@app.route('/')
def index():
    # masks = db.session.query(models.Mask).order_by(db.asc(models.Mask.name))
    masks = Mask.query.order_by(Mask.name.asc()).all()
    return render_template('inventory.html', masks=masks)

@app.route('/mask/<int:mask_id>')
def mask_detail(mask_id):

    txs = Transaction.query.filter_by(mask_id=mask_id)
    mask = Mask.query.get_or_404(mask_id)
    return render_template('mask_detail.html', mask=mask, transactions=txs)

@app.route('/mask/new', methods=["GET", "POST"])
@login_required
def new_mask():
    form = NewMaskForm()

    if form.validate_on_submit():
        print "Creating new mask"
        new_mask = models.Mask(name=form.mask_name.data,
                               form_factor=form.form_factor.data,
                               quantity=form.quantity.data,
                               user_id=current_user.id)
        print "new mask created"
        db.session.add(new_mask)
        db.session.commit()
        flash("New mask created successfully!")
        return redirect(url_for('index'))

    return render_template('new_mask.html', form=form)

@app.route('/mask/<int:mask_id>/edit', methods=["GET", "POST"])
@login_required
def edit_mask(mask_id):
    form = EditMaskForm()

    mask = Mask.query.get_or_404(mask_id)

    if mask.user_id != current_user.id:
        flash('You do not have permission to edit this mask.', 'error')
        return redirect(url_for('mask_detail', mask_id=mask_id))

    if form.validate_on_submit():
        mask.form_factor = form.form_factor.data
        mask.name = form.mask_name.data
        db.session.commit()
        flash('Record updated successfully!')
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('edit_mask.html', form=form, mask=mask)

@app.route('/mask/<int:mask_id>/add', methods=["GET", "POST"])
@login_required
def add_cards(mask_id):
    form = AddCardsForm()

    mask = Mask.query.get_or_404(mask_id)

    if mask.user_id != current_user.id:
        flash('You do not have permission to add cards for this mask.', 'error')
        return redirect(url_for('mask_detail', mask_id=mask_id))

    if form.validate_on_submit():
        mask.quantity += form.quantity.data
        dt = datetime.now().replace(microsecond=0)
        trans = Transaction(desc='New cards',
                            src=mask.user.name,
                            dest=mask.name,
                            qty=form.quantity.data,
                            date=dt,
                            mask_id=mask_id,
                            user_id=mask.user_id)

        db.session.add(trans)
        db.session.commit()

        flash('%s cards added to %s successfully!' % (form.quantity.data, mask.name))
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('add_cards.html', form=form, mask=mask)

@app.route('/mask/<int:mask_id>/transfer', methods=["GET", "POST"])
@login_required
def transfer_cards(mask_id):
    form = TransferCardsForm()

    trash = User.query.filter_by(name='trash').first()
    if not trash:
        msg = 'No trash bin has defined. Please contact you system administrator.'
        app.logger.error(msg)
        flash(msg, 'error')
        return redirect(url_for('mask_detail', mask_id=mask_id))

    form.destination.choices = [(trash.id, trash.name)]
    mask = Mask.query.get_or_404(mask_id)

    if mask.user_id != current_user.id:
        flash('You do not have permission to transfer cards from this mask.', 'error')
        return redirect(url_for('mask_detail', mask_id=mask_id))

    if form.validate_on_submit():
        mask.quantity += form.quantity.data
        dt = datetime.now().replace(microsecond=0)
        trans = Transaction(desc=form.reason.data,
                            src=mask.user.name,
                            dest=trash.name,
                            qty=form.quantity.data,
                            date=dt,
                            mask_id=mask_id,
                            user_id=mask.user_id)

        db.session.add(trans)
        db.session.commit()

    if form.validate_on_submit():
        print "Cards Transferred"
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('transfer_cards.html', form=form, mask=mask)

@app.route('/trash/empty', methods=["GET", "POST"])
@login_required
def empty_trash():

    form = EmptyTrashForm()
    if form.validate_on_submit():
        print "Trash emptied"
        return redirect(url_for('index'))

    return render_template('empty_trash.html', form=form)





