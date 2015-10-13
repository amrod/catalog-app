from catalogapp import app, db, lm

import flask
from flask_oauth import OAuth
from flask.ext.login import current_user, login_user, logout_user, login_required
from forms import NewRecipeForm
from forms import EditRecipeForm
from forms import CuisineForm
from forms import DeleteRecipeForm

from werkzeug.contrib.atom import AtomFeed
from werkzeug import secure_filename
from jinja2 import evalcontextfilter, Markup, escape

import models
from models import Cuisine, Item

from oauth2client.client import verify_id_token
from oauth2client.client import Error as Oauth2clientError

import json
import requests
import os
import re

from datetime import datetime

GOOGLE_ISS = ('accounts.google.com', 'https://accounts.google.com')
GOOGLE_WELL_KNOWN = 'https://accounts.google.com/.well-known/openid-configuration'
GOOGLE_REVOKE = 'https://accounts.google.com/o/oauth2/revoke'
GOOGLE_CLIENT_ID = json.loads(
    open('./instance/client_secrets.json', 'r').read())['web']['client_id']
GOOGLE_CLIENT_SECRET = json.loads(
    open('./instance/client_secrets.json', 'r').read())['web']['client_secret']

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
                          access_token_params={
                              'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)


@app.route('/login')
def login():
    res = google.authorize(
        callback=flask.url_for('oauth_authorized', _external=True))
    return res


@google.tokengetter
def get_google_token(token=None):
    return flask.session.get('access_token')


@app.route('/authorized')
@google.authorized_handler
def oauth_authorized(resp):
    """
    Handles authentication after the user has authorized via Google. Sets up session
    variables with user's information. Creates a local user entry if necessary.
    :param resp:
    :return:
    """
    next_url = flask.url_for('index')

    if resp is None:

        flask.flash(u'Request to sign in was denied by the user.', 'error')
        return flask.redirect(next_url)

    # Verify signed JSON Web Token and retrieve deserialized JSON in the JWT
    try:
        jwt = verify_id_token(resp['id_token'], GOOGLE_CLIENT_ID)
    except Oauth2clientError as err:
        flask.flash(u'Invalid token.', 'error')
        return flask.redirect(next_url)

    fmsg = None

    # Verify that the access token is valid for this app.
    if jwt.get('aud') != GOOGLE_CLIENT_ID:
        fmsg = make_flash_params(
            u"Token's client ID does not match app's.", 'error')

    if jwt.get('iss') not in GOOGLE_ISS:
        fmsg = make_flash_params(u"Invalid token issuer.", 'error')

    # Check is user is already signed in.
    stored_token = flask.session.get('access_token')
    stored_gplus_id = flask.session.get('gplus_id')
    if stored_token is not None and jwt.get('sub') == stored_gplus_id:
        fmsg = make_flash_params(
            u'Current user is already connected.', 'error')

    if fmsg is None:
        # No errors up to this point, user can be authenticated
        flask.session['name'] = jwt.get('name')
        flask.session['picture'] = jwt.get('picture')
        flask.session['email'] = jwt.get('email')
        flask.session['token_expires'] = jwt.get('exp')
        flask.session['access_token'] = resp['access_token']

        # Get or create user
        user = models.load_user(flask.session)

        if user:
            # Mng logged in users with Flask-Login
            login_user(user, remember=True)
            fmsg = make_flash_params(
                u'You were signed in as %s.' % jwt.get('name'))
        else:
            reset_user_session_vars(flask.session)
            fmsg = make_flash_params(
                u'Error registering user %s in the database.' % jwt.get(
                    'name'),
                'error')

    flask.flash(**fmsg)
    return flask.redirect(next_url)


@app.route('/logout')
@login_required
def logout():
    '''
    Removes the users's data from the session and logs the user out.
    '''

    access_token = flask.session.get('access_token')
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

        reset_user_session_vars(flask.session)  # Clear session variable
        logout_user()  # To manage logged in users with Flask-Login

        fmsg = make_flash_params(u'Successfully disconnected.')

    elif result:
        # For whatever reason, the given token was invalid.
        fmsg = make_flash_params(u'Failed to revoke token for given user.',
                                 'error')

    if fmsg:
        flask.flash(**fmsg)

    return flask.redirect(flask.url_for('index'))


@app.route('/index')
@app.route('/')
def index():
    '''
    Renders the home page with a list of all recipes.
    :return: The rendered page.
    '''
    recipes = Item.query.all()  # order_by(Cuisine.name.asc()).
    subtitle = 'All Recipes'
    return flask.render_template('index.html', recipes=recipes, subtitle=subtitle,
                           stats=get_stats())


@app.route('/cuisine/<cuisine_id>')
def cuisine(cuisine_id):
    '''
    Renders the home page with a list all recipes filtered by cuisine cuisine_id.
    :param cuisine_id: ID of the cuisine to filter by.
    :return: The rendered page.
    '''
    recipes = Item.query.filter_by(cuisine_id=cuisine_id).all()
    cuisine = Cuisine.query.get(cuisine_id)
    return flask.render_template('index.html', recipes=recipes,
                           subtitle=cuisine.name, stats=get_stats())


@app.route('/cuisines')
def cuisines():
    '''
    Renders the home page with a list all cuisines.
    :return: The rendered page.
    '''
    cuisines = Cuisine.query.all()
    subtitle = 'All Cuisines'
    return flask.render_template('index.html', cuisines=cuisines,
                           subtitle=subtitle, stats=get_stats())


@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    '''
    Renders a recipe detail page for the recipe matching recipe_id.
    :param recipe_id: ID of the recipe to display.
    :return: The rendered page.
    '''
    recipe = Item.query.get_or_404(recipe_id)
    photo = models.load_image_base64(recipe.photo)
    return flask.render_template('recipe_detail.html', recipe=recipe, photo=photo,
                           stats=get_stats())


@app.route('/recipe/new', methods=["GET", "POST"])
@login_required
def new_recipe():
    '''
    Renders a recipe creation page with forms.
    :return: The rendered page.
    '''
    form = NewRecipeForm()
    form.cuisine.choices = [(c.id, c.name)
                             for c in Cuisine.query.order_by('name')]

    # Form-WTF implements CSRF using the Flask SECRET_KEY
    if form.validate_on_submit():

        try:
            filepath = save_photo(form)

        except OSError as e:
            flask.flash("Something went wrong. Please contact support.")
            return flask.redirect(flask.url_for('new_recipe'))

        new_recipe = models.Item(name=form.name.data,
                                 description=form.description.data,
                                 cuisine_id=form.cuisine.data,
                                 user_id=current_user.id,
                                 photo=filepath)

        db.session.add(new_recipe)
        db.session.commit()
        flask.flash("New recipe created successfully!")

        return flask.redirect(flask.url_for('recipe_detail', recipe_id=new_recipe.id))

    return flask.render_template('form_new_recipe.html', form=form,
                           stats=get_stats())


@app.route('/cuisine/new', methods=["GET", "POST"])
@login_required
def new_cuisine():
    form = CuisineForm()

    # Form-WTF implements CSRF using the Flask SECRET_KEY
    if form.validate_on_submit():
        new_cuisine = models.Cuisine(name=form.name.data)

        db.session.add(new_cuisine)
        db.session.commit()
        flask.flash("New cuisine created successfully!")
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('form_new_cuisine.html', form=form,
                           stats=get_stats())


@app.route('/recipe/<recipe_id>/edit', methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)

    form = EditRecipeForm(obj=recipe)
    form.cuisine.choices = [(c.id, c.name)
                             for c in Cuisine.query.order_by('name')]

    if recipe.user_id != current_user.id:
        flask.flash('You do not have permission to edit this recipe.', 'error')
        return flask.redirect(flask.url_for('recipe_detail', recipe_id=recipe_id))

    if form.validate_on_submit():

        try:
            filepath = save_photo(form)

        except OSError as e:
            flask.flash("Something went wrong. Please contact support.")
            return flask.redirect(flask.url_for('edit_recipe'))

        recipe.name = form.name.data
        recipe.description = form.description.data
        recipe.cuisine_id = form.cuisine.data
        recipe.updated_at = datetime.now().replace(microsecond=0)
        if filepath:
            recipe.photo = filepath
        db.session.commit()

        flask.flash('Record updated successfully!')
        return flask.redirect(flask.url_for('recipe_detail', recipe_id=recipe_id))

    # Set current value if rendering form
    form.cuisine.data = recipe.cuisine_id
    photo = models.load_image_base64(recipe.photo)

    return flask.render_template('form_edit_recipe.html', form=form, recipe=recipe,
                           photo=photo, stats=get_stats())


@app.route('/recipe/<recipe_id>/delete', methods=["GET", "POST"])
@login_required
def delete_recipe(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)
    form = DeleteRecipeForm()

    if recipe.user_id != current_user.id:
        flask.flash('You do not have permission to delete this recipe.', 'error')
        return flask.redirect(flask.url_for('recipe_detail', recipe_id=recipe_id))

    # Form-WTF implements CSRF using the Flask SECRET_KEY
    if form.validate_on_submit():
        models.delete_file(recipe.photo)
        db.session.delete(recipe)
        db.session.commit()

        flask.flash('Recipe {} was deleted.'.format(recipe.name))
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('form_delete_recipe.html', form=form, recipe=recipe,
                           stats=get_stats())


@app.route('/recipe/<recipe_id>/photo/delete', methods=["GET", "POST"])
@login_required
def delete_photo(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)

    if recipe.user_id != current_user.id:
        flask.flash(
            'You do not have permission to delete this recipe photo.', 'error')
        return flask.redirect(flask.url_for('recipe_detail', recipe_id=recipe_id))

    models.delete_file(recipe.photo)
    recipe.photo = None
    db.session.commit()

    return flask.redirect(flask.url_for('edit_recipe', recipe_id=recipe.id))


@app.route('/recipe/<recipe_id>/photo')
def recipe_photo(recipe_id):
    recipe = Item.query.get(recipe_id)
    if not recipe.photo:
        flask.abort(404)

    photo = models.load_image_base64(recipe.photo)
    return flask.render_template("photo.html", photo=photo, stats=get_stats())


@app.route('/recipe/JSON')
def get_all_recipes_json():
    recipes = Item.query.all()
    return flask.jsonify(Recipes=[r.serialize for r in recipes])


@app.route('/recipe/<recipe_id>/JSON')
def get_recipe_json(recipe_id):
    recipe = Item.query.get_or_404(recipe_id)
    return flask.jsonify(Recipe=recipe.serialize)


@app.route('/cuisine/<cuisine_id>/JSON')
def get_cuisine_recipes_json(cuisine_id):
    cuisine = Cuisine.query.get_or_404(cuisine_id)
    recipes = Item.query.filter_by(cuisine_id=cuisine_id).all()
    return flask.jsonify(Recipes={cuisine.name: [r.serialize for r in recipes]})


@app.route('/cuisine/JSON')
def get_categories_json():
    categories = Cuisine.query.all()
    return flask.jsonify(Categories=[c.serialize for c in categories])


@app.route('/recipe/recent.atom')
def recent_feed():

    recipes = Item.query.order_by(Item.created_at.desc()).limit(15).all()

    feed = AtomFeed(
        'Recent Recipes', feed_url=flask.request.url, url=flask.request.url_root)

    for recipe in recipes:

        feed.add(recipe.name, recipe.description,
                 url=flask.url_for(
                     'recipe_detail', recipe_id=recipe.id, _external=True),
                 content_type='text/plain',
                 author=recipe.user.name,
                 updated=recipe.updated_at,
                 date_added=recipe.created_at)

    return feed.get_response()


# Helper functions

def reset_user_session_vars(session):
    '''Resets the user's session variables'''
    session.pop('name', None)
    session.pop('picture', None)
    session.pop('email', None)
    session.pop('token_expires', None)
    session.pop('access_token', None)


def save_photo(form):
    orig_name = secure_filename(current_user.email + form.photo.data.filename)
    filepath = None

    if form.photo.has_file():
        fd, filepath = models.try_open_file(
            app.config['UPLOAD_FOLDER'], orig_name)

        with os.fdopen(fd, 'w') as file_obj:
            form.photo.data.save(file_obj)

    return filepath


def make_flash_params(message, category='message'):
    return {'message': message, 'category': category}


def get_stats():
    '''Get counts of database items.'''
    stats = {
        'recipes': Item.query.count(),
        'cuisines': Cuisine.query.count()
    }
    return stats


@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """
    A nl2br (newline to <BR>) filter
    Source: http://flask.pocoo.org/snippets/28/
    """
    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){1,}')

    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
