from inventoryapp import app
from inventoryapp import db
from flask import render_template, redirect, url_for, request, jsonify, flash, session, make_response
from forms import NewMaskForm, EditMaskForm, AddCardsForm, TransferCardsForm, EmptyTrashForm
from models import User, Mask

from oauth2client.client import verify_id_token
import json
import requests

from flask_oauth import OAuth
from flask.ext.login import current_user, login_user, login_required

class M:
    pass

JSON_CT = {'Content-Type': 'application/json'}
GOOGLE_WELL_KNOWN = 'https://accounts.google.com/.well-known/openid-configuration'
GOOGLE_TOKEN_INFO ='https://www.googleapis.com/oauth2/v1/tokeninfo'
GOOGLE_USER_INFO = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_CLIENT_ID = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_secret']

ginfo = requests.get(GOOGLE_WELL_KNOWN).json()

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
    return session.get('access_token')

@app.route('/authorized')
@google.authorized_handler
def oauth_authorized(resp):

    next_url = request.args.get('next') or url_for('index')

    if resp is None:

        flash(u'Request to sign in was denied by the user.')
        return redirect(next_url)


    jwt = verify_id_token(resp['id_token'], GOOGLE_CLIENT_ID)

    r = requests.get(GOOGLE_TOKEN_INFO, params={'access_token': resp['access_token']}).json()

    fmsg = None
    # This is not a valid token.
    if r.get('error') is not None:
        fmsg = u'Error authenticating user.'

    # Verify that the access token is used for the intended user.
    if r['user_id'] != jwt.get('sub'):
        fmsg = u"Error: Token's user ID doesn't match given user ID."
        # response = make_response(json.dumps(s), 401, JSON_CT)
        # return response

    # Verify that the access token is valid for this app.
    if r.get('issued_to') != GOOGLE_CLIENT_ID:
        fmsg = u"Error: Token's client ID does not match app's."
        # response = make_response(json.dumps(s), 401, JSON_CT)
        # return response

    # Check is user is already signed in.
    stored_token = session.get('access_token')
    stored_gplus_id = session.get('gplus_id')
    if stored_token is not None and jwt.get('sub') == stored_gplus_id:
        fmsg = u'Current user is already connected.'
        # response = make_response(json.dumps(s), 200, JSON_CT)
        # return response

    if fmsg is not None:
        data = get_google_user_info(resp['access_token'])
        session['username'] = data['name']
        session['picture'] = data['picture']
        session['email'] = data['email']

        session['access_token'] = resp['access_token']
        session['access_token'] = resp['expires_in']
        fmsg = u'You were signed in.'

    flash(fmsg)
    return redirect(next_url)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user is not None and current_user.is_authenticated():
#         return redirect(url_for('index'))
#     return render_template('login.html')



def get_google_user_info(access_token):
    params = {'access_token': access_token, 'alt': 'json'}
    r = requests.get(GOOGLE_USER_INFO, params=params)
    return r.json()

@app.route('/inventory')
@app.route('/')
def index():
    # masks = [{'id': 1, 'name': 'G242', 'quantity': 20},
    #          {'id': 2, 'name': 'STM008', 'quantity': 50}]

    masks = db.session.query(Mask).order_by(db.asc(Mask.name))
    return render_template('inventory.html', masks=masks)

@app.route('/mask/<int:mask_id>')
def mask_detail(mask_id):

    mask = M()
    mask.id = 1
    mask.name = 'G242'
    txs = [{'id': 1, 'description': 'New cards', 'from': 'loc1', 'to': 'loc2', 'quantity': 20, 'date': '2015/1/6', 'user': 'Juan Perez'},
           {'id': 2, 'description': 'Development', 'from': 'loc1', 'to': 'loc2', 'quantity': 30, 'date': '2015/9/1', 'user': 'Amaury Rodriguez'},
           {'id': 3, 'description': 'New cards', 'from': 'loc1', 'to': 'loc2', 'quantity': 50, 'date': '2015/1/5', 'user': 'Boris S.'},
           {'id': 4, 'description': 'New cards', 'from': 'loc1', 'to': 'loc2', 'quantity': 10, 'date': '2015/1/2', 'user': 'Amaury Rodriguez'},
           {'id': 5, 'description': 'New cards', 'from': 'loc1', 'to': 'loc2', 'quantity': 80, 'date': '2015/3/1', 'user': 'Amaury Rodriguez'},]

    return render_template('mask_detail.html', mask=mask, transactions=txs)


@app.route('/mask/new', methods=["GET", "POST"])
@login_required
def new_mask():
    form = NewMaskForm()

    if form.validate_on_submit():
        print "Creating new mask"
        new_mask = Mask(name=form.name.data,
                        form_factor=form.form_factor.data,
                        quantity=form.quantity.data)
        print "new mask created"
        db.session.add(new_mask)
        db.session.commit()
        flash("New mask successfully created")
        return redirect(url_for('index'))

    return render_template('new_mask.html', form=form)

@app.route('/mask/<int:mask_id>/edit', methods=["GET", "POST"])
def edit_mask(mask_id):
    form = EditMaskForm()

    mask = M()
    mask.id = 1
    mask.name = 'G242'

    if form.validate_on_submit():
        print "Mask edited"
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('edit_mask.html', form=form, mask=mask)

@app.route('/mask/<int:mask_id>/add', methods=["GET", "POST"])
def add_cards(mask_id):
    form = AddCardsForm()

    mask = M()
    mask.id = 1
    mask.name = 'G242'

    if form.validate_on_submit():
        print "Cards Added"
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('add_cards.html', form=form, mask=mask)

@app.route('/mask/<int:mask_id>/transfer', methods=["GET", "POST"])
def transfer_cards(mask_id):

    users = [(1, 'Amaury Rodriguez'), (2, 'Arthur L.'), (3, 'Boris S.'), (4, 'Bill M.')]
    mask = M()
    mask.id = 1
    mask.name = 'G242'

    form = TransferCardsForm()
    form.destination.choices = users

    if form.validate_on_submit():
        print "Cards Transferred"
        return redirect(url_for('mask_detail', mask_id=mask_id))

    return render_template('transfer_cards.html', form=form, mask=mask)

@app.route('/trash/empty', methods=["GET", "POST"])
def empty_trash():

    form = EmptyTrashForm()
    if form.validate_on_submit():
        print "Trash emptied"
        return redirect(url_for('index'))

    return render_template('empty_trash.html', form=form)





