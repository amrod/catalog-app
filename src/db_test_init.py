import inventoryapp
from inventoryapp.models import User

if __name__ == '__main__':

    users = [{'name': 'TestUser 1', 'email': 'test1@example.com'},
             {'name': 'TestUser 2', 'email': 'test2@example.com'},
             {'name': 'TestUser 3', 'email': 'test3@example.org'},
             {'name': 'TestUser 4', 'email': 'test4@example.net'}]

    masks = [{'name': 'CARD1', 'form_factor': '2FF', 'quantity': 10, 'user_id': 1},
             {'name': 'CARD2', 'form_factor': '3FF', 'quantity': 40, 'user_id': 2},
             {'name': 'CARD3', 'form_factor': '4FF', 'quantity': 70, 'user_id': 3},
             {'name': 'CARD4', 'form_factor': 'NANO', 'quantity': 20, 'user_id': 4}]

    txs = [{'user_id': 1,'mask_id': 0, 'description': 'New cards', 'source': 'loc1', 'destination': 'loc2', 'quantity': 20, 'date': '2015/1/6'},
           {'user_id': 2,'mask_id': 1, 'description': 'Development', 'source': 'loc1', 'destination': 'loc2', 'quantity': 30, 'date': '2015/9/1'},
           {'user_id': 3,'mask_id': 2, 'description': 'New cards', 'source': 'loc1', 'destination': 'loc2', 'quantity': 50, 'date': '2015/1/5'},
           {'user_id': 4,'mask_id': 3, 'description': 'New cards', 'source': 'loc1', 'destination': 'loc2', 'quantity': 10, 'date': '2015/1/2'},
           {'user_id': 4,'mask_id': 3, 'description': 'New cards', 'source': 'loc1', 'destination': 'loc2', 'quantity': 80, 'date': '2015/3/1'},]

    db = inventoryapp.db
    db.create_all()

    data = masks + users + txs
    for kwargs in data:
        u = User(**kwargs)
        db.session.add(u)
        db.session.commit()

