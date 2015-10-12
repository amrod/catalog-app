import random
import string

DEBUG = False
SQLALCHEMY_ECHO = False
BCRYPT_LEVEL = 12  # Configuration for the Flask-Bcrypt extension
SECRET_KEY = ''.join(random.choice(string.ascii_letters +  string.digits) for x in xrange(32))
UPLOAD_FOLDER = 'uploads'
SQLALCHEMY_DATABASE_URI = 'sqlite:///recipecatalog.db'
