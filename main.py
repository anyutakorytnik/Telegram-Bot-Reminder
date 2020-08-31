import sys
import threading

# pylint: disable=unused-wildcard-import
from init import *
from bot_db_notes import *
from bot_text_parsing import *


def fail_message(chat_id):
    """int -> unit"""
    global config, bot
    bot.send_message(chat_id, config["fail_message"])


def menu_markup():
    """unit -> markup"""
    markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True)
    addKey = telebot.types.KeyboardButton(text=config["add_key"])
    listKey = telebot.types.KeyboardButton(text=config["list_key"])
    markup.add(addKey, listKey)
    return markup


def cancel_markup():
    """unit -> markup"""
    markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True)
    cancel = telebot.types.KeyboardButton(text=config["cancel_key"])
    markup.add(cancel)
    return markup


def list_markup():
    """unit -> markup"""
    markup = telebot.types.InlineKeyboardMarkup()
    right_key = telebot.types.InlineKeyboardButton(
        text="<", callback_data="left")
    left_key = telebot.types.InlineKeyboardButton(
        text=">", callback_data="right")
    edit_key = telebot.types.InlineKeyboardButton(
        text="Edit", callback_data="edit")
    delete_key = telebot.types.InlineKeyboardButton(
        text="Delete", callback_data="delete")
    markup.add(right_key, left_key)
    markup.add(edit_key, delete_key)
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "left")
def left_action(call):
    # message.from_user.id != call.message.from_user.id
    # message.from_user.id == call.message.chat.id
    ind = get_watch_note_index(call.message.chat.id) - 1
    size = len(get_list_of_notes(call.message.chat.id))
    if size == 1:
        return
    if ind < 0:
        ind = size - 1
    edit_watch_note_index(call.message.chat.id, ind)
    msg = list_from_menu(call.message)
    bot.edit_message_text(msg, chat_id=call.message.chat.id, \
     message_id=call.message.message_id, reply_markup=list_markup())


@bot.callback_query_handler(func=lambda call: call.data == "right")
def right_action(call):
    ind = get_watch_note_index(call.message.chat.id) + 1
    size = len(get_list_of_notes(call.message.chat.id))
    if size == 1:
        return
    if ind >= size:
        ind = 0
    edit_watch_note_index(call.message.chat.id, ind)
    msg = list_from_menu(call.message)
    bot.edit_message_text(msg, chat_id=call.message.chat.id, \
     message_id=call.message.message_id, reply_markup=list_markup())


@bot.callback_query_handler(func=lambda call: call.data == "edit")
def edit_action(call):
    bot.edit_message_text(config["edit_note_text"], chat_id=call.message.chat.id, \
     message_id=call.message.message_id)
    ind = get_watch_note_index(call.message.chat.id)
    notes = get_list_of_notes(call.message.chat.id)
    edit_note_db(notes[ind][0], call.message.chat.id)
    set_user_action(call.message.chat.id, "add_message_request")


@bot.callback_query_handler(func=lambda call: call.data == "delete")
def delete_action(call):
    ind = get_watch_note_index(call.message.chat.id)
    notes = get_list_of_notes(call.message.chat.id)
    delete_note_from_db(notes[ind][0])
    if len(notes) == 1:
        bot.edit_message_text(config["no_notes"], chat_id=call.message.chat.id, \
     message_id=call.message.message_id)
        bot.send_message(
            call.message.chat.id, config["menu"], reply_markup=menu_markup())
        return
    edit_watch_note_index(call.message.chat.id, ind - 1)
    right_action(call)


def no_timezone_handler(message):
    """message -> unit"""
    user = message.from_user
    tz = try_get_user_timezone(user.id)
    if tz is None:
        tz = try_parse_timezone(message.text)
        if tz is None:
            fail_message(message.chat.id)
            return
        set_user_timezone(user.id, tz)
        bot.send_message(
            message.chat.id, config["acceptable_timezone_message"], reply_markup=menu_markup())


def list_from_menu(message):
    """message -> string"""
    global config
    
    user_id = message.chat.id
    notes = get_list_of_notes(user_id)
    if len(notes) == 0:
        return ''
    ind = get_watch_note_index(user_id)
    _, date, msg = notes[ind]
    timezone = try_get_user_timezone(user_id)
    date_dt = datetime.datetime.fromisoformat(date)
    date_dt += datetime.timedelta(minutes=timezone)
    message = "Date: " + \
        str(date_dt) + '\n' + "Description: " + msg
    return message


def add_date_request_handler(message):
    """message -> unit"""
    global config, bot

    if message.text == "CANCEL":
        # bot.delete_message(message.chat.id, message.message_id)
        set_user_action(message.from_user.id, "menu")
        bot.send_message(
            message.chat.id, config["note_deleted"], reply_markup=menu_markup())
        return

    date = try_parse_datetime(message.text)
    if date is None:
        fail_message(message.chat.id)
        return
    timezone = try_get_user_timezone(message.from_user.id)
    date -= datetime.timedelta(minutes=timezone)
    create_note_with_date(message.from_user.id, date)
    set_user_action(message.from_user.id, "add_message_request")
    bot.send_message(
        message.chat.id, config["add_message_request"], reply_markup=None)


def add_message_request_handler(message):
    """message -> unit"""
    global config, bot

    if message.text == "CANCEL":
        # bot.delete_message(message.chat.id, message.message_id)
        note_id = get_edit_note_id(message.from_user.id)
        delete_note_from_db(note_id)
        set_user_action(message.from_user.id, "menu")
        bot.send_message(
            message.chat.id, config["note_deleted"], reply_markup=menu_markup())
        return

    add_text(message)
    note_id = get_edit_note_id(message.from_user.id)
    _, user_id, sched_time, message_text = get_note_by_id(note_id)
    schedule_message(datetime.datetime.fromisoformat(
        sched_time), note_id)

    edit_note_db(None, message.from_user.id)
    bot.send_message(
        message.chat.id, config["success"], reply_markup=menu_markup())
    set_user_action(message.from_user.id, "menu")


def menu_handler(message):
    """message -> unit"""
    global config
    user_id = message.from_user.id

    if message.text == config["add_key"]:
        # bot.delete_message(message.chat.id, message.message_id)
        set_user_action(user_id, "add_date_request")
        bot.send_message(
            message.chat.id, config["add_date_request"], reply_markup=cancel_markup())
    elif message.text == config["list_key"]:
        # bot.delete_message(message.chat.id, message.message_id)
        msg = list_from_menu(message)
        if msg == '':
            bot.send_message(
                    message.chat.id, config["no_notes"], reply_markup=menu_markup())
            return
        bot.send_message(message.chat.id, config["welcome_list"], reply_markup=cancel_markup())
        bot.send_message(message.chat.id, msg, reply_markup=list_markup())
    elif message.text == config["cancel_key"]:
        # bot.delete_message(message.chat.id, message.message_id - 2)
        # bot.delete_message(message.chat.id, message.message_id - 1)
        # bot.delete_message(message.chat.id, message.message_id)
        edit_watch_note_index(message.from_user.id, 0)
        set_user_action(message.from_user.id, "menu")
        bot.send_message(
            message.chat.id, config["menu"], reply_markup=menu_markup())
        return


def cancel_handler():
    pass

@bot.message_handler(commands=['start'])
def welcome(message):
    global config
    if message.chat.type != "private":
        return
    user = message.from_user
    if user_exists_in_db(user.id):
        bot.send_message(message.chat.id, config["hello_again_message"], reply_markup=menu_markup())
    else:
        create_user_in_db(user.id)
        bot.send_message(message.chat.id, config["start_message"])

@bot.message_handler(content_types=['text'])
def handle_message(message):
    global config
    if message.chat.type != "private":
        return
    
    user = message.from_user
    if not user_exists_in_db(user.id):
        create_user_in_db(user.id)

    cur_action = get_user_action(user.id)
    if cur_action == "menu":
        menu_handler(message)
    elif cur_action == "add_date_request":
        add_date_request_handler(message)
    elif cur_action == "add_message_request":
        add_message_request_handler(message)
    elif cur_action == "no_timezone":
        no_timezone_handler(message)


def schedule_message(sched_time, note_id):
    """datitime -> integer -> unit"""
    global bot, event_loop
    delta = sched_time - datetime.datetime.utcnow()
    if delta.total_seconds() < 0:
        event_loop.call_soon_threadsafe(conditonal_send_message, note_id)
        return
    loop_time = event_loop.time() + delta.total_seconds()
    event_loop.call_soon_threadsafe(
        event_loop.call_at, loop_time, conditonal_send_message, note_id)


def conditonal_send_message(note_id):
    """integer -> unit"""
    global bot
    msg = get_note_by_id(note_id)
    if msg is not None:
        tz = try_get_user_timezone(msg[1])
        dt = dateutil.parser.parse(msg[2]) + datetime.timedelta(minutes=tz)
        bot.send_message(int(msg[1]), str(dt) + '\n' + msg[3])
        delete_note_from_db(note_id)


async def process_notes():
    """unit -> unit"""
    notes = load_notes_from_db()
    for note in notes:
        note_id, user_id, sched_time, message_text = \
            note[0], note[1], datetime.datetime.fromisoformat(note[2]), note[3]
        schedule_message(sched_time, note_id)


threading.Thread(target=bot.polling, daemon=True,
                 kwargs={"none_stop": True}).start()
event_loop.create_task(process_notes())
# event_loop.set_debug(enabled=True)
event_loop.run_forever()
