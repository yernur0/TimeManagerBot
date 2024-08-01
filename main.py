import config
import telebot
from datetime import datetime, timedelta
import threading
import sqlite3
from telebot import types

bot = telebot.TeleBot(config.token)

USER_STATES = {}

def init_db():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            event_datetime TEXT,
            event_desc TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            task_desc TEXT,
            priority INTEGER,
            deadline TEXT,
            parent_task_id INTEGER,
            FOREIGN KEY (parent_task_id) REFERENCES tasks (id)
        )
    ''')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="Добавить событие", callback_data="add_event"),
        types.InlineKeyboardButton(text="Показать события", callback_data="list_events"),
        types.InlineKeyboardButton(text="Добавить задачу", callback_data="add_task"),
        types.InlineKeyboardButton(text="Показать задачи", callback_data="list_tasks"),
        types.InlineKeyboardButton(text="Удалить событие", callback_data="remove_event"),
        types.InlineKeyboardButton(text="Удалить задачу", callback_data="remove_task"),
        types.InlineKeyboardButton(text="Помощь", callback_data="help"),
        types.InlineKeyboardButton(text="Спланировать день", callback_data="plan_day"),
        types.InlineKeyboardButton(text="Спланировать неделю", callback_data="plan_week")
    ]
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, "Привет! Я менеджер времени и календаря. Выберите действие:", reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help(message):
    help_text = (
        "/add_event - Добавить событие\n"
        "/list_events - Показать все события\n"
        "/remove_event - Удалить событие\n"
        "/add_task - Добавить задачу\n"
        "/list_tasks - Показать все задачи\n"
        "/remove_task - Удалить задачу\n"
        "/plan_day - Спланировать день\n"
        "/plan_week - Спланировать неделю"
    )
    bot.reply_to(message, help_text)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "add_event":
        show_date_picker(chat_id)
    elif call.data.startswith("date_"):
        date_str = call.data.split("_")[1]
        show_time_picker(chat_id, date_str)
    elif call.data.startswith("time_"):
        date_str, time_str = call.data.split("_")[1], call.data.split("_")[2]
        USER_STATES[chat_id] = {"action": "add_event", "date": date_str, "time": time_str}
        bot.send_message(chat_id, f"Вы выбрали {date_str} {time_str}. Введите описание события:")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    elif call.data == "manual_date":
        bot.send_message(chat_id, "Введите дату в формате YYYY-MM-DD:")
        USER_STATES[chat_id] = {"action": "manual_date"}
    elif call.data == "remove_event":
        bot.send_message(chat_id, "Введите ID события, которое хотите удалить:")
        USER_STATES[chat_id] = {"action": "remove_event"}
    elif call.data == "remove_task":
        bot.send_message(chat_id, "Введите ID задачи, которую хотите удалить:")
        USER_STATES[chat_id] = {"action": "remove_task"}
    elif call.data == "list_events":
        list_events(call.message)
    elif call.data == "add_task":
        bot.send_message(chat_id, "Отправьте описание задачи:")
    elif call.data == "list_tasks":
        list_tasks(call.message)
    elif call.data == "plan_day":
        plan_day(call.message)
    elif call.data == "plan_week":
        plan_week(call.message)
    elif call.data == "help":
        help(call.message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if chat_id in USER_STATES:
        state = USER_STATES[chat_id]
        if state["action"] == "add_event":
            event_desc = message.text
            date_str = state["date"]
            time_str = state["time"]
            process_event_description(message, date_str, time_str, event_desc)
            del USER_STATES[chat_id]
        elif state["action"] == "add_task":
            process_add_task(message)
            del USER_STATES[chat_id]
        elif state["action"] == "manual_date":
            handle_manual_date_input(message)
        elif state["action"] == "manual_time":
            handle_manual_time_input(message)
        elif state["action"] == "remove_event":
            process_remove_event(message)
            del USER_STATES[chat_id]
        elif state["action"] == "remove_task":
            process_remove_task(message)
            del USER_STATES[chat_id]
    else:
        bot.reply_to(message, "Не удалось обработать ваше сообщение. Пожалуйста, используйте команду из списка доступных команд.")

def show_date_picker(chat_id):
    today = datetime.now().date()
    keyboard = types.InlineKeyboardMarkup()
    
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        keyboard.add(types.InlineKeyboardButton(text=date_str, callback_data=f"date_{date_str}"))
    
    keyboard.add(types.InlineKeyboardButton(text="Введите дату вручную", callback_data="manual_date"))
    
    bot.send_message(chat_id, "Выберите дату:", reply_markup=keyboard)

def show_time_picker(chat_id, date_str):
    keyboard = types.InlineKeyboardMarkup()
    
    for hour in range(24):
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            keyboard.add(types.InlineKeyboardButton(text=time_str, callback_data=f"time_{date_str}_{time_str}"))
    
    bot.send_message(chat_id, "Выберите время:", reply_markup=keyboard)

def handle_manual_date_input(message):
    chat_id = message.chat.id
    date_str = message.text.strip()
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        bot.send_message(chat_id, "Теперь введите время в формате HH:MM:")
        USER_STATES[chat_id] = {"action": "manual_time", "date": date_str}
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Попробуйте снова в формате YYYY-MM-DD.")

def list_events(message):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, event_desc, event_datetime FROM events WHERE chat_id = ?', (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        event_list = "\n".join([f"ID {row[0]} - {datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')}: {row[1]}" for row in rows])
        bot.reply_to(message, f"Ваши события:\n{event_list}")
    else:
        bot.reply_to(message, "У вас нет событий.")

def handle_manual_time_input(message):
    chat_id = message.chat.id
    time_str = message.text.strip()
    date_str = USER_STATES[chat_id].get("date")
    
    try:
        datetime.strptime(time_str, "%H:%M")
        USER_STATES[chat_id] = {"action": "add_event", "date": date_str, "time": time_str}
        bot.send_message(chat_id, f"Вы выбрали {date_str} {time_str}. Введите описание события:")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат времени. Попробуйте снова в формате HH:MM.")

def process_event_description(message, date_str, time_str, event_desc):
    try:
        event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events WHERE event_datetime = ? AND chat_id = ?', (event_datetime, message.chat.id))
        if cursor.fetchone():
            bot.reply_to(message, "На это время уже назначено другое событие.")
        else:
            cursor.execute('INSERT INTO events (chat_id, event_datetime, event_desc) VALUES (?, ?, ?)', 
                           (message.chat.id, event_datetime, event_desc))
            conn.commit()
            bot.reply_to(message, f"Событие '{event_desc}' добавлено на {event_datetime.strftime('%Y-%m-%d %H:%M')}")
            schedule_notification(message.chat.id, event_datetime, event_desc)
        
        conn.close()
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}\nФормат команды: /add_event Дата Время Описание")

def process_remove_event(message):
    try:
        event_id = int(message.text.strip())
        
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM events WHERE chat_id = ? AND id = ?', (message.chat.id, event_id))
        if cursor.rowcount > 0:
            bot.reply_to(message, f"Событие с ID {event_id} удалено.")
        else:
            bot.reply_to(message, "Событие с таким ID не найдено.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}\nФормат команды: /remove_event ID")

def process_add_task(message):
    try:
        task_desc = message.text.strip()
        bot.send_message(message.chat.id, "Введите приоритет задачи (от 1 до 5):")
        USER_STATES[message.chat.id] = {"action": "add_task_priority", "task_desc": task_desc}
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}\nФормат команды: /add_task Описание")

def process_add_task_priority(message):
    try:
        priority = int(message.text.strip())
        if priority < 1 or priority > 5:
            raise ValueError("Приоритет должен быть от 1 до 5.")
        
        task_desc = USER_STATES[message.chat.id]["task_desc"]
        bot.send_message(message.chat.id, "Введите срок выполнения задачи в формате YYYY-MM-DD:")
        USER_STATES[message.chat.id] = {"action": "add_task_deadline", "task_desc": task_desc, "priority": priority}
    except ValueError as e:
        bot.reply_to(message, f"Ошибка: {e}\nВведите корректный приоритет (от 1 до 5).")

def process_add_task_deadline(message):
    try:
        deadline = message.text.strip()
        datetime.strptime(deadline, "%Y-%m-%d")
        
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO tasks (chat_id, task_desc, priority, deadline) VALUES (?, ?, ?, ?)', 
                       (message.chat.id, USER_STATES[message.chat.id]["task_desc"], USER_STATES[message.chat.id]["priority"], deadline))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, "Задача добавлена.")
        del USER_STATES[message.chat.id]
    except ValueError:
        bot.reply_to(message, "Неверный формат даты. Попробуйте снова в формате YYYY-MM-DD.")

def process_remove_task(message):
    try:
        task_id = int(message.text.strip())
        
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE chat_id = ? AND id = ?', (message.chat.id, task_id))
        if cursor.rowcount > 0:
            bot.reply_to(message, f"Задача {task_id} удалена.")
        else:
            bot.reply_to(message, "Задача с таким ID не найдена.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}\nФормат команды: /remove_task ID")

def list_tasks(message):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, task_desc, priority, deadline FROM tasks WHERE chat_id = ? ORDER BY id', (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        task_list = "\n".join([f"ID {row[0]} - Задача: {row[1]} - Приоритет: {row[2]}, Срок выполнения: {row[3]}" for row in rows])
        bot.reply_to(message, f"Ваши задачи:\n{task_list}")
    else:
        bot.reply_to(message, "У вас нет задач.")

def schedule_notification(chat_id, event_datetime, event_desc):
    delay = (event_datetime - datetime.now()).total_seconds()
    if delay > 0:
        timer = threading.Timer(delay, send_notification, args=[chat_id, event_desc])
        timer.start()

def send_notification(chat_id, event_desc):
    bot.send_message(chat_id, f"Напоминание: {event_desc}")

@bot.message_handler(commands=['plan_day'])
def plan_day(message):
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    tomorrow_start = today_start + timedelta(days=1)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT event_datetime, event_desc FROM events WHERE chat_id = ? AND event_datetime BETWEEN ? AND ? ORDER BY event_datetime', 
                   (message.chat.id, today_start, tomorrow_start))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        event_list = "\n".join([f"{datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')}: {row[1]}" for row in rows])
        bot.reply_to(message, f"Ваш план на сегодня:\n{event_list}")
    else:
        bot.reply_to(message, "На сегодня нет запланированных событий.")

@bot.message_handler(commands=['plan_week'])
def plan_week(message):
    now = datetime.now()
    week_start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT event_datetime, event_desc FROM events WHERE chat_id = ? AND event_datetime BETWEEN ? AND ? ORDER BY event_datetime', 
                   (message.chat.id, week_start, week_end))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        event_list = "\n".join([f"{datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%a %H:%M')}: {row[1]}" for row in rows])
        bot.reply_to(message, f"Ваш план на неделю:\n{event_list}")
    else:
        bot.reply_to(message, "На эту неделю нет запланированных событий.")

if __name__ == "__main__":
    init_db()
    bot.polling(none_stop=True)
