import inventoryapp
from inventoryapp.models import User

if __name__ == '__main__':
    """Create database"""

    db = inventoryapp.db
    db.create_all()
    db.session.commit()


