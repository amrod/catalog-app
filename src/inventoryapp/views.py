from inventoryapp import app
from inventoryapp import db
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from forms import NewMaskForm, EditMaskForm, AddCardsForm, TransferCardsForm, EmptyTrashForm
from models import User, Mask
import json
from rauth import OAuth2Service

from flask.ext.login import current_user, login_user, login_required

class M:
    pass

GOOGLE_CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('client_secrets.json', 'r').read())['web']['client_secret']




service = OAuth2Service(name='google',
                        client_id=GOOGLE_CLIENT_ID,
                        client_secret=GOOGLE_CLIENT_SECRET,
                        authorize_url='https://accounts.google.com/o/oauth2/auth',
                        access_token_url='https://accounts.google.com/o/oauth2/token',
                        base_url='https://www.google.com/accounts/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user is not None and current_user.is_authenticated():
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/gconnect')
def gconnect():
    if not current_user.is_anonymous():
        return redirect(url_for('index'))

    # _external=True to generate an absolute URL (to be called by provider
    redir_url = url_for('oauth_redirect', _external=True)
    print redir_url

    auth_url = service.get_authorize_url(scope='email',
                                         response_type='code',
                                         redirect_uri=redir_url)
    print auth_url
    return redirect(auth_url)

@app.route('/oauth_redirect')
def oauth_redirect():
    if not current_user.is_anonymous():
        return redirect(url_for('index'))

    if 'code' not in request.args:
        return None, None, None

    oauth_session = service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': url_for('oauth_redirect', _external=True)},
            decoder = json.loads)

    print oauth_session
    print dir(oauth_session)

    #answer = oauth_session.get('https://www.googleapis.com/oauth2/v3/token')
    #answer = oauth_session.get('')

    print "****JSON response:%s" % dir(service)
    print service.access_token_response

    name = answer['name']
    email  = answer['email']

    if email is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))

    user = User.query.filter_by(email=email).first()

    # If user does not exist, create it
    if not user:
        user = User(name=name , email=email)
        db.session.add(user)
        db.session.commit()

    # Log in the user with Flask-Login and remember them for their next visit
    login_user(user, remember=True)
    return redirect(url_for('index'))


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





