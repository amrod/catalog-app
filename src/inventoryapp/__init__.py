from flask import Flask
app = Flask(__name__, instance_relative_config=True)

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask.ext.login import LoginManager
lm = LoginManager()
lm.init_app(app)

import inventoryapp.views
from models import User

app.config.from_object('config')
app.config.from_pyfile('config.py')
