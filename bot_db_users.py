import sqlite3

# pylint: disable=unused-wildcard-import
from init import *

#------actions with user-------

def create_user_in_db(user_id):
    """int -> unit"""
    """user_id - Telegram user id, integer"""
    global cursor, config

    cursor.execute(
        '''INSERT INTO users (user_id, action, watch_note_index) VALUES (?, "no_timezone", 0)''', (user_id,))


def user_exists_in_db(user_id):
    """int -> bool"""
    """user_id - Telegram user id, integer"""
    global cursor, config

    fetch = cursor.execute(
        '''SELECT EXISTS(SELECT * FROM users WHERE user_id = ? LIMIT 1)''', (user_id,), get="one")
    user_exists = (fetch[0] == 1)
    return user_exists


#------actions with timezone-------

def try_get_user_timezone(user_id):
    """int -> int option"""
    """Assumes user_id exists in the database; return the timezone offset (integer) or None if user hasn't set it yet"""
    global cursor, config

    fetch = cursor.execute(
        '''SELECT timezone FROM users WHERE user_id = ? LIMIT 1''', (user_id,), get="one")
    userdata = fetch[0]
    return userdata


def set_user_timezone(user_id, timezone):
    """int -> int -> unit"""
    global cursor, config

    cursor.execute(
        '''UPDATE users SET timezone = ? WHERE user_id = ?''', (timezone, user_id))
    cursor.execute(
        '''UPDATE users SET action = "menu" WHERE user_id = ?''', (user_id, ))


#------what is user doing-------

def get_user_action(user_id):
    """int -> string"""
    global cursor, config

    fetch = cursor.execute(
        '''SELECT action FROM users WHERE user_id = ? LIMIT 1''', (user_id,), get="one")
    action = fetch[0]
    return action


def set_user_action(user_id, action):
    """int -> string -> unit"""
    global db, cursor, config

    cursor.execute(
        '''UPDATE users SET action = ? WHERE user_id = ?''', (action, user_id))
    return


def edit_note_db(note_id, user_id):
    """int -> int -> unit"""
    global cursor
    cursor.execute(
        '''UPDATE users SET edit_note = ? WHERE user_id = ?''', (note_id, user_id))
    return


def get_edit_note_id(user_id):
    """int -> int"""
    global cursor
    return cursor.execute(
        '''SELECT edit_note FROM users WHERE user_id = ?''', (user_id, ), get="one")[0]



def get_watch_note_index(user_id):
    """int -> int"""
    global cursor
    return cursor.execute('''SELECT watch_note_index FROM users WHERE user_id = ?''', (user_id, ), get="one")[0]


def edit_watch_note_index(user_id, ind):
    """int -> int -> unit"""
    global cursor
    cursor.execute(
        '''UPDATE users SET watch_note_index = ? WHERE user_id = ?''', (ind, user_id))
    return