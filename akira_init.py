import os, pymongo
from telethon import TelegramClient
from telethon.sessions import StringSession
from akira_db import *

def log(text): print(f'[Akira] {text}')

log('Getting credentials...')
api_id = os.getenv('API_ID') or ''
api_hash = os.getenv('API_HASH') or ''
mdb_host = os.getenv('MDB_HOST') or ''
if not api_id or not api_hash or not mdb_host:
    log('Seems like some environment variables are not set. Make sure that API_ID, API_HASH and MDB_HOST are set.')
    exit()

log('Connecting to MongoDB server...')
mdb_server = pymongo.MongoClient(mdb_host)['akira']
cred_data = mdb_server['cred']

if db_find(cred_data, 'authkey'):
    log('Database is already initialized.')
else:
    log('Initializing database...')
    client = TelegramClient(StringSession(), api_id, api_hash).start()
    db_insert(cred_data, 'authkey', client.session.save())
    log('Database initialized.')
