from catalogapp import lm
from flask.ext.login import UserMixin
from flask import url_for
from datetime import datetime
import hashlib
import os
import errno
import random
import sys
import base64

from . import db, app


class User(UserMixin, db.Model):
    '''
    Describes a User of the application.
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(250), nullable=True)
    picture_url = db.Column(db.String(2083))

    items = db.relationship('Item', backref='user', lazy='dynamic')

    def __init__(self, name, email, picture_url=None):
        self.name = name
        self.email = email
        self.picture_url = picture_url

    @property
    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'email': self.email,
                'picture_url': self.picture_url}


class Cuisine(db.Model):
    '''
    Describes a style of cuisine to which recipes belong.
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    items = db.relationship('Item', backref='category', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    @property
    def serialize(self):
        '''
        Returns the object's attributes in an easy to serialize format.
        '''
        return {'id': self.id,
                'name': self.name}


class Item(db.Model):
    '''
    Describes a recipe item.
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    photo = db.Column(db.String(40), nullable=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __init__(self, name, description, user_id, category_id,
                 created_at=None, photo=None):
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now().replace(microsecond=0)
        self.updated_at = self.created_at
        self.user_id = user_id
        self.category_id = category_id
        self.photo = photo or ''

    @property
    def serialize(self):
        '''
        Returns the object's attributes in an easy to serialize format.
        '''
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'date_added': self.created_at,
                'user_id': self.user_id,
                'cuisine_id': self.category_id,
                'photo_url': url_for('recipe_photo',
                                     recipe_id=self.id, _external=True)}

# Helper functions

@lm.user_loader
def load_user_from_id(id):
    '''
    Handler for LoginManager's user_loader. Retrieves the User object
    corresponding to id.
    :param id: ID of use to retrieve.
    :return: User object corresponding to id.
    '''
    return User.query.get(int(id))


def get_user(email):
    '''
    Retrieves a user categoryith the given email from the database
    :param email: user's email address.
    :return: models.User object or None if user was not found.
    '''
    try:
        user = db.session.query(User).filter_by(email=email).one()
        return user
    except Exception as err:
        app.logger.error(err)
        return None


def create_user(session):
    '''
    Creates a user based on the information stored in the session dictionary.
    :param session: dictionary of session variables.
    :return: models.User object or None if it could not be created.
    '''
    try:
        user = User(name=session.get('name'),
                    email=session.get('email'),
                    picture_url=session.get('picture'))

        db.session.add(user)
        db.session.commit()
        return user

    except Exception as err:
        app.logger.error(err)
        return None


def load_user(session):
    '''
    Loads a use from the database using information stored in the session dictionary.
    :param session: dictionary of session variables.
    :return: the user object retrieved or created.
    '''
    user = get_user(session.get('email'))

    if not user:
        user = create_user(session)

    if not user:
        return user

    updated = False
    if user.name != session.get('name'):
        user.name = session.get('name')
        updated = True

    if user.picture_url != session.get('picture'):
        user.picture_url = session.get('picture')
        updated = True

    if updated:
        db.session.commit()

    return user


def try_open_file(target_dir, basename=None):
    '''
    Attempts to create a file in the filesystem avoiding race condition.
    :param target_dir: the target directory where tho save the file
    :basename: a seed name for the file.
    :return: a tuple containing file descriptor as returned by os.open()
    and the file's relative path.
    '''
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    if not basename:
        basename = ''

    basename = scramble_name(str(random.randint(0, sys.maxsize)) + basename)
    dest = os.path.join(target_dir, basename)

    try:
        fh = os.open(dest, flags)
    except OSError as e:
        if e.errno == errno.EEXIST:  # Failed as the file already exists.
            try_open_file(target_dir, basename)
        else:  # Something unexpected went wrong so reraise the exception.
            raise
    else:  # No exception, so the file must have been created successfully.
        return fh, dest


def scramble_name(basename):
    '''
    Computes SHA-1 of the given filename.
    :param basename: the string to hash.
    :return: the SH-1 hash
    '''
    ext = os.path.splitext(basename)[1]
    return hashlib.sha1(basename).hexdigest() + ext


def load_image_base64(p):
    '''
    Encodes the contents of the image file p and returns the encoded string.
    :param p: path to the file to encode
    :return: encoded value
    '''
    try:
        with open(p, "rb") as img:
            img_str = base64.b64encode(img.read()).decode()

        return img_str
    except (EnvironmentError, TypeError) as e:
        return u''


def delete_file(p):
    '''
    Removes file p from the file system.
    :param p: path to the file to be deleted.
    :return: None
    '''
    try:
        os.remove(p)
    except EnvironmentError:
        pass
