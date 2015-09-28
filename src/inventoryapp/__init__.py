from flask import Flask
app = Flask(__name__, instance_relative_config=True)

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask.ext.login import LoginManager
lm = LoginManager()
lm.init_app(app)

from flask_wtf.csrf import CsrfProtect
import inventoryapp.views

app.config.from_object('config')
app.config.from_pyfile('config.py')
CsrfProtect(app)
