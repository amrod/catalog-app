#!/usr/bin/env bash
apt-get -qqy update
apt-get -qqy install postgresql python-psycopg2
apt-get -qqy install python-sqlalchemy
apt-get -qqy install python-pip
apt-get -qqy install python-dev 
apt-get -qqy install libffi-dev 
apt-get -qqy install libssl-dev 

pip install oauth2client==1.5.1
pip install requests==2.2.1
pip install httplib2==0.9.2
pip install werkzeug==0.8.3
pip install flask==0.9
pip install Flask-Login==0.1.3
pip install Flask-SQLAlchemy==2.0
pip install Flask-WTF==0.12
pip install Flask-OAuth==0.12
pip install PyOpenSSL

rm -f /vagrant/src/inventoryapp/cardinventory.db
(cd /vagrant/src/ && exec python db_setup.py)
