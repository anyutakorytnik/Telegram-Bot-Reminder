import asyncio
import json
import sqlite3
import telebot
import threading
import os.path


def create_db():
    db = sqlite3.connect('mydb.db')
    cursor = db.cursor()
    cursor.execute(
        '''CREATE TABLE users(
            user_id INT NOT NULL, 
            timezone INT, 
            action TEXT, 
            edit_note INT, 
            watch_note_index INT,
            PRIMARY KEY (user_id), 
            FOREIGN KEY (edit_note) REFERENCES notes (note_id))'''
    )
    cursor.execute(
        '''CREATE TABLE notes(
            note_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INT NOT NULL, 
            datetime TEXT NOT NULL, 
            message TEXT, 
            FOREIGN KEY (user_id) REFERENCES users (user_id))'''
    )

    db.close()


class LockableCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lock = threading.Lock()

    def execute(self, sql, *args, get=None):
        self.lock.acquire()

        try:
            self.cursor.execute(sql, *args)

            if get == 'all':
                result = self.cursor.fetchall()
            elif get == 'one':
                result = self.cursor.fetchone()
        except Exception as exception:
            raise exception

        finally:
            self.lock.release()
            if get:
                return result


class Db:
    def __init__(self, filename):
        self.filename = filename

    def connect(self):
        self.connection = sqlite3.connect(
            self.filename, check_same_thread=False, isolation_level=None)  # Will create db if nonexistent
        self.cs = LockableCursor(self.connection.cursor())


with open("config.json", encoding='utf-8') as json_file:
    config = json.load(json_file)

with open("token") as token_file:
    token_str = token_file.read()

if not os.path.exists(config["db_file"]):
    create_db()

db = Db(config["db_file"])
db.connect()
cursor = db.cs

# Event-loop из семи *****
event_loop = asyncio.get_event_loop()

bot = telebot.TeleBot(token_str)
