def db_insert(db, name, data):
    if db_find(db, name):
        raise Exception('Key is already in database.')
    else:
        db.insert_one({'name': name, 'value': data})

def db_update(db, name, data):
    if not db_find(db, name):
        raise Exception('Key is not in database.')
    else:
        db.update_one({'name': name}, {'$set': {'name': name, 'value': data}})

def db_delete(db, name):
    if not db_find(db, name):
        raise Exception('Key is not in database.')
    else:
        db.delete_one({'name': name})

def db_find(db, name):
    return db.find_one({'name': name})
