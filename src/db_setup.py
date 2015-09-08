import inventoryapp
from inventoryapp.models import User

if __name__ == '__main__':
    """Create database and insert special/internal 'trash' user to hold trashed cards."""

    db = inventoryapp.db
    db.create_all()
    trash = User('trash', '0', 't@t')
    db.session.add(trash)
    db.session.commit()