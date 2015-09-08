from inventoryapp import app
from flask.ext.login import UserMixin, LoginManager

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    picture = db.Column(db.String(250))
    cards = db.relationship('Mask', backref='user', lazy='dynamic')

    def __init__(self, name, email):
        self.name = name
        self.email = email

class Mask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    form_factor = db.Column(db.String(32), nullable=False)
    # cards = db.relationship('UserCard', backref='mask', lazy='dynamic')
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    cards = db.relationship('Transaction', backref='mask', lazy='dynamic')

    def __init__(self, name, form_factor, quantity):
        self.name = name
        self.form_factor = form_factor
        self.quantity = quantity

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(64), nullable=False)
    destination = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    mask_id = db.Column(db.Integer, db.ForeignKey('mask.id'), primary_key=True)


# Initialize Flask-Login extension
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


