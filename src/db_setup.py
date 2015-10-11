import inventoryapp

if __name__ == '__main__':
    """Create database"""

    db = inventoryapp.db
    db.create_all()
    db.session.commit()
