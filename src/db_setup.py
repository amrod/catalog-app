import catalogapp

if __name__ == '__main__':
    """Create database"""

    db = catalogapp.db
    db.create_all()
    db.session.commit()
