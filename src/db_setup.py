import inventoryapp
from inventoryapp.models import User

if __name__ == '__main__':
    """Create database and insert special/internal 'trash' user to hold trashed cards."""

    db = inventoryapp.db
    db.create_all()
    trash = User(name='trash', picture_url='', email='t@t')
    db.session.add(trash)
    db.session.commit()


