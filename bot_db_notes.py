import sqlite3

# pylint: disable=unused-wildcard-import
from init import *
from bot_db_users import *

def create_note_with_date(user_id, date):
    """int -> datetime -> unit"""
    global db, cursor, config

    cursor.execute(
        '''INSERT INTO notes (user_id, datetime) VALUES (?, ?)''', (user_id, date))
    fetch = cursor.execute(
        '''SELECT last_insert_rowid() FROM notes''', get="one")
    note_id = fetch[0]
    cursor.execute(
        '''UPDATE users SET edit_note = ? WHERE user_id = ?''', (note_id, user_id))
    return


def load_notes_from_db():
    """unit -> tuple[]"""
    global cursor
    return cursor.execute('''SELECT * FROM notes WHERE message IS NOT NULL''', get="all")



def add_text(message):
    """message -> unit"""
    global cursor
    note_id = get_edit_note_id(message.from_user.id)
    cursor.execute(
        '''UPDATE notes SET message = ? WHERE note_id = ?''', (message.text, note_id))


def get_note_by_id(note_id):
    """int -> tuple"""
    global cursor
    return cursor.execute('''SELECT * FROM notes WHERE note_id = ?''', (note_id,), get="one")


def delete_note_from_db(note_id):
    """int -> unit"""
    global cursor
    cursor.execute('''DELETE FROM notes WHERE note_id == ?''', (note_id, ))


def get_list_of_notes(user_id):
    """int -> tuple[]"""
    global cursor
    return cursor.execute(
        '''SELECT note_id, datetime, message FROM notes WHERE user_id = ? ORDER BY datetime ASC''', (user_id,), get="all")



def edit_note_text(note_id, text):
    """int -> string -> unit"""
    global cursor
    cursor.execute(
        '''UPDATE notes SET message = ? WHERE note_id = ?''', (text, note_id))
    return
