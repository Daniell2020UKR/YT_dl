import os, asyncio, pymongo, akira_lang, tempfile, shutil, threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import AddContactRequest
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from youtube_dl import YoutubeDL
from akira_db import *
from http.server import BaseHTTPRequestHandler, HTTPServer

akira = '0.2-alpha'

def log(text): print(f'[Akira] {text}')

def get_args(event):
    args = event.text.split(' ')
    args.pop(0)
    return args

def get_lang(chat):
    global chat_data
    if db_find(chat_data, f'{chat.id}_lang'): return db_find(chat_data, f'{chat.id}_lang')['value']
    else: return 'en'

log(f'Starting {akira}...')
log('Getting credentials...')
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
mdb_host = os.getenv('MDB_HOST')
if not api_id or not api_hash or not mdb_host:
    log('Seems like some environment variables are not set. Make sure that API_ID, API_HASH and MDB_HOST are set.')
    exit()

log('Connecting to MongoDB server...')
mdb_server = pymongo.MongoClient(mdb_host)['akira']
cred_data = mdb_server['cred']
user_data = mdb_server['user']
chat_data = mdb_server['chat']

log('Creating client entity...')
client = TelegramClient(StringSession(db_find(cred_data, 'authkey')['value']), api_id, api_hash).start()

log('Removing credentials from memory for security...')
api_id = None
api_hash = None
mdb_host = None
del os.environ['API_ID'], os.environ['API_HASH'], os.environ['MDB_HOST']
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
mdb_host = os.getenv('MDB_HOST')
if api_id or api_hash or mdb_host:
    log('Credentials are still accessible.')
    exit()

log('Creating functions...')
@client.on(events.NewMessage(pattern=r'\.start'))
async def akira_start(event):
    chat = await event.get_chat()
    await event.reply(akira_lang.translations[get_lang(chat)]['akira_start'])

@client.on(events.NewMessage(pattern=r'\.help'))
async def akira_help(event):
    chat = await event.get_chat()
    await event.reply(akira_lang.translations[get_lang(chat)]['akira_help'])

@client.on(events.NewMessage(pattern=r'\.version'))
async def akira_version(event):
    chat = await event.get_chat()
    await event.reply(akira_lang.translations[get_lang(chat)]['akira_version'] + akira)

@client.on(events.NewMessage(pattern=r'\.changelog'))
async def akira_changelog(event):
    chat = await event.get_chat()
    await event.reply(akira_lang.translations[get_lang(chat)]['akira_changelog'])

@client.on(events.NewMessage(pattern=r'\.donate'))
async def akira_donate(event):
    chat = await event.get_chat()
    await event.reply(akira_lang.translations[get_lang(chat)]['akira_donate'])

@client.on(events.NewMessage(pattern=r'\.setlang'))
async def akira_setlang(event):
    chat = await event.get_chat()
    args = get_args(event)
    if args:
        if args[0] in akira_lang.translations.keys():
            if db_find(chat_data, f'{chat.id}_lang'):
                db_update(chat_data, f'{chat.id}_lang', args[0])
                await event.reply(akira_lang.translations[get_lang(chat)]['akira_newlang'])
            else:
                db_insert(chat_data, f'{chat.id}_lang', args[0])
                await event.reply(akira_lang.translations[get_lang(chat)]['akira_newlang'])
        else:
            await event.reply(akira_lang.translations[get_lang(chat)]['akira_nolang'])
    else:
        await event.reply(akira_lang.translations[get_lang(chat)]['akira_noargs'])

@client.on(events.NewMessage(pattern=r'\.y2a'))
async def akira_yt2a(event):
    chat = await event.get_chat()
    args = get_args(event)
    if args:
        temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())
        dargs = {'format': 'bestaudio[ext=m4a][filesize<?250M]', 'outtmpl': f'{temp_dir}/audio-%(id)s.%(ext)s', 'writethumbnail': True}
        sent_message = await event.reply(akira_lang.translations[get_lang(chat)]['akira_downloading'])
        try:
            audio_info = YoutubeDL(dargs).extract_info(args[0])
            id = audio_info['id']
            if os.path.exists(f'{temp_dir}/audio-{id}.webp'):
                thumbext = 'webp'
            else:
                thumbext = 'jpg'
        except:
            await event.reply(akira_lang.translations[get_lang(chat)]['akira_audio_download_error'])
            await sent_message.delete()
            shutil.rmtree(temp_dir)
            return
        await sent_message.edit(akira_lang.translations[get_lang(chat)]['akira_uploading'])
        try:
            await client.send_file(
                chat,
                file=open(f'{temp_dir}/audio-{id}.m4a', 'rb'),
                thumb=open(f'{temp_dir}/audio-{id}.{thumbext}', 'rb'),
                reply_to=event.message,
                attributes=[DocumentAttributeAudio(
                    title=audio_info['title'],
                    performer=audio_info['artist'],
                    voice=True,
                    duration=audio_info['duration']
                )]
            )
        except:
            await event.reply(akira_lang.translations[get_lang(chat)]['akira_audio_upload_error'])
            await sent_message.delete()
            shutil.rmtree(temp_dir)
            return
        await sent_message.delete()
        shutil.rmtree(temp_dir)
    else:
        await event.reply(akira_lang.translations[get_lang(chat)]['akira_noargs'])

@client.on(events.NewMessage(pattern=r'\.y2v'))
async def akira_yt2v(event):
    chat = await event.get_chat()
    args = get_args(event)
    if args:
        temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())
        dargs = {'format': 'bestvideo[ext=mp4][filesize<?250M]+bestaudio[ext=m4a][filesize<?250M]', 'outtmpl': f'{temp_dir}/video-%(id)s.%(ext)s', 'writethumbnail': True}
        sent_message = await event.reply(akira_lang.translations[get_lang(chat)]['akira_downloading'])
        try:
            video_info = YoutubeDL(dargs).extract_info(args[0])
            id = video_info['id']
            if os.path.exists(f'{temp_dir}/video-{id}.webp'):
                thumbext = 'webp'
            else:
                thumbext = 'jpg'
        except:
            await event.reply(akira_lang.translations[get_lang(chat)]['akira_audio_download_error'])
            await sent_message.delete()
            shutil.rmtree(temp_dir)
            return
        await sent_message.edit(akira_lang.translations[get_lang(chat)]['akira_uploading'])
        try:
            await client.send_file(
                chat,
                file=open(f'{temp_dir}/video-{id}.mp4', 'rb'),
                thumb=open(f'{temp_dir}/video-{id}.{thumbext}', 'rb'),
                reply_to=event.message,
                attributes=[DocumentAttributeVideo(
                    duration=video_info['duration'],
                    w=video_info['width'],
                    h=video_info['height'],
                    round_message=False,
                    supports_streaming=True
                )]
            )
        except:
            await event.reply(akira_lang.translations[get_lang(chat)]['akira_audio_upload_error'])
            await sent_message.delete()
            shutil.rmtree(temp_dir)
            return
        await sent_message.delete()
        shutil.rmtree(temp_dir)
    else:
        await event.reply(akira_lang.translations[get_lang(chat)]['akira_noargs'])

if os.getenv('PORT'):
    log('Heroku detected, binding PORT...')
    def heroku_binder():
        class Binder(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('Akira on Heroku!'.encode('utf-8'))
        HTTPServer(('0.0.0.0', int(os.getenv('PORT'))), Binder).serve_forever()
    threading.Thread(target=heroku_binder).start()

@client.on(events.NewMessage(pattern='/yt2a'))
async def akira_donate(event):
    await event.reply('The /yt2a is deprecated, please use .yt2a')

@client.on(events.NewMessage(pattern='/start'))
async def akira_donate(event):
    await event.reply('The /start is deprecated, please use .start')


log('Started.')
client.run_until_disconnected()
