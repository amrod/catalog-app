apt-get -qqy update
apt-get -qqy install postgresql python-psycopg2
apt-get -qqy install python-sqlalchemy
apt-get -qqy install python-pip
pip install oauth2client
pip install requests
pip install httplib2
pip install werkzeug==0.8.3
pip install flask==0.9
pip install Flask-Login==0.1.3
pip install Flask-SQLAlchemy==2.0
pip install Flask-WTF
pip install Lask-OAuth

rm -f /vagrant/src/inventoryapp/cardinventory.db
(cd /vagrant/src/ && exec python db_setup.py)
