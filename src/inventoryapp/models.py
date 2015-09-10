from inventoryapp import lm
from flask.ext.login import UserMixin

from . import db, app


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=True)
    picture_url = db.Column(db.String(2083))

    cards = db.relationship('Mask', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    def __init__(self, name, email, picture_url=None):
        self.name = name
        self.email = email
        self.picture_url = picture_url


class Mask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    form_factor = db.Column(db.String(32), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    cards = db.relationship('Transaction', backref='mask', lazy='dynamic')

    def __init__(self, name, form_factor, quantity, user_id):
        self.name = name
        self.form_factor = form_factor
        self.quantity = quantity
        self.user_id = user_id

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(64), nullable=False)
    destination = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    mask_id = db.Column(db.Integer, db.ForeignKey('mask.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


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


