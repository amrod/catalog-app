from inventoryapp import app, db, lm

from flask import render_template, redirect, url_for, request, jsonify, flash, session
from flask import abort
from flask_oauth import OAuth
from flask.ext.login import current_user, login_user, logout_user, login_required
from forms import NewRecipeForm, EditRecipeForm, NewCategoryForm, DeleteRecipeForm
from werkzeug.contrib.atom import AtomFeed
from werkzeug import secure_filename
from jinja2 import evalcontextfilter, Markup, escape

import models
from models import Category, Item

from oauth2client.client import verify_id_token, Error as Oauth2clientError

import json
import requests
import os
import re

from datetime import datetime

#JSON_CT = {'Content-Type': 'application/json'}
GOOGLE_ISS = ('accounts.google.com', 'https://accounts.google.com')
GOOGLE_WELL_KNOWN = 'https://accounts.google.com/.well-known/openid-configuration'
#GOOGLE_TOKEN_INFO ='https://www.googleapis.com/oauth2/v1/tokeninfo'
#GOOGLE_USER_INFO = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_REVOKE = 'https://accounts.google.com/o/oauth2/revoke'
GOOGLE_CLIENT_ID = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(open('./instance/client_secrets.json', 'r').read())['web']['client_secret']

lm.login_view = 'index'
lm.login_message_category = 'error'

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
        fmsg = make_flash_params(
            u'Current user is already connected.', 'error')

    if fmsg is None:
        # No errors up to this point, user can be authenticated
        session['name'] = jwt.get('name')
        session['picture'] = jwt.get('picture')
        session['email'] = jwt.get('email')
        session['token_expires'] = jwt.get('exp')
        session['access_token'] = resp['access_token']

        user = models.load_user(session)

        if user:
            # Mng logged in users with Flask-Login
            login_user(user, remember=True)
            fmsg = make_flash_params(
                u'You were signed in as %s.' % jwt.get('name'))
        else:
            reset_user_session_vars(session)
            fmsg = make_flash_params(
                u'Error registering user %s in the database.' % jwt.get('name'),
                'error')

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
        fmsg = make_flash_params(u'Failed to revoke token for given user.',
                                 'error')

    if fmsg:
        flash(**fmsg)

    return redirect(url_for('index'))


@app.route('/index')
@app.route('/')
def index():
    recipes = Item.query.all()  # order_by(Category.name.asc()).
    subtitle='All Recipes'
    return render_template('index.html', recipes=recipes, subtitle=subtitle)


@app.route('/category/<category_id>')
def category(category_id):
    recipes = Item.query.filter_by(category_id=category_id).all()
    category = Category.query.get(category_id)
    return render_template(
        'index.html', recipes=recipes, subtitle=category.name)


@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)
    photo = models.load_image_base64(recipe.photo)
    return render_template('recipe_detail.html', recipe=recipe, photo=photo)


@app.route('/recipe/new', methods=["GET", "POST"])
@login_required
def new_recipe():
    form = NewRecipeForm()
    form.category.choices = [(c.id, c.name)
                             for c in Category.query.order_by('name')]

    # Form-WTF implements CSRF using the Flask SECRET_KEY
    if form.validate_on_submit():
        filepath = None

        if form.photo.has_file():
            orig_name = secure_filename(current_user.email +
                                       form.photo.data.filename)

            try:
                fd, filepath = models.try_open_file(
                    app.config['UPLOAD_FOLDER'], orig_name)

            except OSError as e:
                flash("Somethig went wrong. Please contact support.")
                return redirect(url_for('new_recipe'))

            with os.fdopen(fd, 'w') as file_obj:
                form.photo.data.save(file_obj)

        new_recipe = models.Item(name=form.name.data,
                                 description=form.description.data,
                                 category_id=form.category.data,
                                 user_id=current_user.id,
                                 photo=filepath)

        db.session.add(new_recipe)
        db.session.commit()
        flash("New recipe created successfully!")

        return redirect(url_for('recipe_detail', recipe_id=new_recipe.id))

    return render_template('form_new_recipe.html', form=form)


@app.route('/recipe/new', methods=["GET", "POST"])
@login_required
def new_category():
    form = NewCategoryForm()

    # Form-WTF implements CSRF using the Flask SECRET_KEY
    if form.validate_on_submit():
        new_category = models.Category(name=form.name.data)

        db.session.add(new_category)
        db.session.commit()
        flash("New category created successfully!")
        return redirect(url_for('index'))

    return render_template('form_new_category.html', form=form)


@app.route('/recipe/<recipe_id>/edit', methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)

    form = EditRecipeForm(obj=recipe)
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by('name')]

    if recipe.user_id != current_user.id:
        flash('You do not have permission to edit this recipe.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    if form.validate_on_submit():
        recipe.name = form.name.data
        recipe.description = form.description.data
        recipe.category_id  = form.category.data
        recipe.updated_at = datetime.now().replace(microsecond=0)
        db.session.commit()

        flash('Record updated photo=filepath)successfully!')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    # Set current value if rendering form
    form.category.data = recipe.category_id

    return render_template('form_edit_recipe.html', form=form, recipe=recipe)


@app.route('/recipe/<recipe_id>/delete', methods=["GET", "POST"])
@login_required
def delete_recipe(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)
    form = DeleteRecipeForm()

    if recipe.user_id != current_user.id:
        flash('You do not have permission to delete this recipe.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    if form.validate_on_submit():
        db.session.delete(recipe)
        db.session.commit()

        flash('Recipe {} was deleted.'.format(recipe.name))
        return redirect(url_for('index'))

    return render_template('form_delete_recipe.html', form=form, recipe=recipe)

@app.route('/recipe/<recipe_id>/photo')
def recipe_photo(recipe_id):
    recipe = Item.query.get(recipe_id)
    if not recipe.photo:
        abort(404)

    photo = models.load_image_base64(recipe.photo)
    return render_template("photo.html", photo=photo)


@app.route('/recipe/JSON')
def get_all_recipes_json():
    recipes = Item.query.all()
    return jsonify(Recipes=[r.serialize for r in recipes])


@app.route('/recipe/<recipe_id>/JSON')
def get_recipe_json(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)
    return jsonify(Recipe=recipe.serialize)


@app.route('/category/<category_id>/JSON')
def get_category_recipes_json(category_id):
    category = Category.query.get_or_404(category_id)
    recipes = Item.query.filter_by(category_id=category_id).all()
    return jsonify(Recipes={category.name: [r.serialize for r in recipes]})


@app.route('/category/JSON')
def get_categories_json():
    categories = Category.query.all()
    return jsonify(Categories=[c.serialize for c in categories])

@app.route('/recipe/recent.atom')
def recent_feed():

    recipes = Item.query.order_by(Item.created_at.desc()).limit(15).all()

    feed = AtomFeed('Recent Recipes', feed_url=request.url, url=request.url_root)

    for recipe in recipes:

        feed.add(recipe.name, recipe.description,
                 url=url_for('recipe_detail', recipe_id=recipe.id, _external=True),
                 content_type='text/plain',
                 author=recipe.user.name,
                 updated=recipe.updated_at,
                 date_added=recipe.created_at)

    return feed.get_response()


# Helper functions

def reset_user_session_vars(session):
    # Reset the user's session variables
    session.pop('name', None)
    session.pop('picture', None)
    session.pop('email', None)
    session.pop('token_expires', None)
    session.pop('access_token', None)


def make_flash_params(message, category='message'):
    return {'message': message, 'category': category}

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """
    A nl2br (newline to <BR>) filter
    Source: http://flask.pocoo.org/snippets/28/
    """
    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result