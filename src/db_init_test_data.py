import catalogapp
from datetime import datetime
from catalogapp.models import User, Cuisine, Item

if __name__ == '__main__':

    users = [{'name': 'TestUser 1', 'email': 'test1@example.com'},
             {'name': 'TestUser 2', 'email': 'test2@example.com'},
             {'name': 'TestUser 3', 'email': 'test3@example.org'},
             {'name': 'TestUser 4', 'email': 'test4@example.net'}]

    categories = [{'name': 'Chinese'},
                  {'name': 'Japanese'},
                  {'name': 'Dominican'},
                  {'name': 'Mexican'}]

    items = [{'user_id': 2, 'cuisine_id': 1, 'name': "General Tso's",
              'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 5,
              'created_at': datetime(2015, 1, 6)},
             {'user_id': 2, 'cuisine_id': 1, 'name': 'Chop Suey',
              'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 5,
              'created_at': datetime(2015, 9, 1)},
             {'user_id': 3, 'cuisine_id': 2, 'name': 'Raisin Bran Bread',
              'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 5,
              'created_at': datetime(2015, 1, 5)},
             {'user_id': 4, 'cuisine_id': 3, 'name': 'Tostones',
              'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 5,
              'created_at': datetime(2015, 1, 2)},
             {'user_id': 4, 'cuisine_id': 4, 'name': 'Salmon Burgers',
              'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 5,
              'created_at': datetime(2015, 3, 1)}, ]

    db = catalogapp.db
    db.create_all()

    for kwargs in users:
        print kwargs
        u = User(**kwargs)
        db.session.add(u)
        db.session.commit()

    for kwargs in categories:
        print kwargs
        m = Cuisine(**kwargs)
        db.session.add(m)
        db.session.commit()

    for kwargs in items:
        print kwargs
        t = Item(**kwargs)
        db.session.add(t)
        db.session.commit()
