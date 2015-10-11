from inventoryapp import lm
from flask.ext.login import UserMixin
from datetime import datetime

from . import db, app


class User(UserMixin, db.Model):
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

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    items = db.relationship('Item', backref='category', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    @property
    def serialize(self):
        return {'id': self.id,
                'name': self.name}

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __init__(self, name, description, user_id, category_id, date_added=None):
        self.name = name
        self.description = description
        self.date_added = date_added or datetime.now().replace(microsecond=0)
        self.user_id = user_id
        self.category_id = category_id

    @property
    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'date_added': self.date_added,
                'user_id': self.user_id,
                'category_id': self.category_id}

@lm.user_loader
def load_user_from_id(id):
    return User.query.get(int(id))

def get_user(email):
    try:
        user = db.session.query(User).filter_by(email=email).one()
        return user
    except Exception as err:
        app.logger.error(err)
        return None

def create_user(session):
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


