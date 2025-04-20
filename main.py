import telebot
from telebot import types
import datetime
import json

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
bot = telebot.TeleBot('your bot token')

# --- Работа с расписанием (JSON) ---
SCHEDULE_FILE = 'schedule.json' # Имя файла для хранения расписания

try:
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        schedule = json.load(f)
except FileNotFoundError:
    schedule = {}

def save_schedule():
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=4, ensure_ascii=False)


# --- Обработчики команд и кнопок ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Расписание на сегодня 📚")
    item2 = types.KeyboardButton("Расписание на неделю 📅")
    item3 = types.KeyboardButton("Мой следующий урок ➡️") # Добавлена кнопка
    markup.add(item1, item2, item3) # Добавлена кнопка в разметку

    bot.send_message(message.chat.id, 'Привет! Что хочешь узнать?', reply_markup=markup)


@bot.message_handler(regexp="Расписание на сегодня 📚")
def today_schedule(message):
    today = datetime.datetime.now().strftime("%A").lower()
    group = get_user_group(message.chat.id) # !!! Получение группы пользователя
    if not group:
        bot.send_message(message.chat.id, "Ваша группа не установлена. Обратитесь к администратору.")
        return

    today_lessons = schedule.get(group, {}).get(today, [])
    schedule_text = create_schedule_message(today.capitalize(), today_lessons)
    bot.send_message(message.chat.id, schedule_text)


def create_schedule_message(day_name, lessons):
    if lessons:
        schedule_text = f"Расписание на {day_name}:\n"
        for lesson in lessons:
            schedule_text += f"- {lesson}\n"
    else:
        schedule_text = f"На {day_name} занятий нет."
    return schedule_text


@bot.message_handler(regexp="Расписание на неделю 📅")
def week_schedule(message):
    group = get_user_group(message.chat.id) # !!! Получение группы пользователя
    if not group:
        bot.send_message(message.chat.id, "Ваша группа не установлена. Обратитесь к администратору.")
        return

    group_schedule = schedule.get(group, {})
    week_text = ""
    for day, lessons in group_schedule.items():
        week_text += create_schedule_message(day.capitalize(), lessons) + "\n\n"

    bot.send_message(message.chat.id, week_text or "Расписание на неделю пустое.")



@bot.message_handler(regexp="Мой следующий урок ➡️")
def next_lesson(message):
    now = datetime.datetime.now()
    group = get_user_group(message.chat.id) # !!! Получение группы пользователя
    if not group:
        bot.send_message(message.chat.id, "Ваша группа не установлена. Обратитесь к администратору.")
        return


    group_schedule = schedule.get(group, {})
    next_lesson_info = find_next_lesson(now, group_schedule)

    if next_lesson_info:
        bot.send_message(message.chat.id, f"Твой следующий урок:\n{next_lesson_info['lesson']} в {next_lesson_info['time'].strftime('%A %H:%M')}")
    else:
        bot.send_message(message.chat.id, "Ближайших уроков не найдено.")


def find_next_lesson(now, group_schedule):
    next_lesson_info = None

    for day, lessons in group_schedule.items():
        try:
            day_offset = (list(group_schedule).index(day) - list(group_schedule).index(now.strftime("%A").lower())) % 7

            for lesson_str in lessons:

                try:
                    lesson_time_str = lesson_str.split()[-1]
                    lesson_time = datetime.datetime.strptime(lesson_time_str, "%H:%M-%H:%M").time()
                    lesson_datetime = datetime.datetime.combine(now.date() + datetime.timedelta(days=day_offset), lesson_time)


                    if lesson_datetime > now and (next_lesson_info is None or lesson_datetime < next_lesson_info["time"]):
                        next_lesson_info = {
                            "time": lesson_datetime,
                            "lesson": lesson_str
                        }
                except ValueError:
                    # Обработка некорректного формата времени, например, запись "праздник"
                    pass # Или можно вывести предупреждение, если нужно


        except ValueError: # Обрабатываем случай, если день недели не найден
            pass # Игнорируем, если день не указан в расписании


    return next_lesson_info




# --- Работа с пользователями и группами (JSON) ---
USERS_FILE = 'users.json'

try:
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def get_user_group(user_id):
    user_id = str(user_id) # Преобразуем user_id в строку
    if user_id in users:
        return users[user_id]
    else:
        return None # Возвращаем None, если пользователь не найден

@bot.message_handler(commands=['setgroup'])
def set_group_command(message):
    if len(message.text.split()) > 1:
        group_name = message.text.split(maxsplit=1)[1]
        user_id = str(message.chat.id) # Преобразуем user_id в строку
        users[user_id] = group_name
        save_users()
        bot.reply_to(message, f"Ваша группа установлена: {group_name}")
    else:
        bot.reply_to(message, "Пожалуйста, укажите название группы: /setgroup <название_группы>")


# ... (остальной код админ-панели)
USERS_FILE = 'users.json'

try:
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def get_user_group(user_id):
    return users.get(str(user_id)) # user_id храним как строку


@bot.message_handler(commands=['setgroup'])
def set_group(message):
    # Проверяем, есть ли аргумент команды (название группы)
    if len(message.text.split()) > 1:
        group = message.text.split(maxsplit=1)[1]
        users[str(message.chat.id)] = group
        save_users()
        bot.reply_to(message, f"Ваша группа установлена на: {group}")
    else:
        bot.reply_to(message, "Пожалуйста, укажите название группы: /setgroup <название_группы>")




# --- Админ-панель ---
ADMIN_ID = 123456789 # !!! ЗАМЕНИТЕ НА ВАШ ID !!!

def admin_only(func): # Декоратор для функций, доступных только администратору
    def wrapper(message):
        if message.chat.id == ADMIN_ID:
            return func(message)
        else:
            bot.reply_to(message, "Эта команда доступна только администратору.")
    return wrapper

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text == "Добавить занятие ➕")
@admin_only
def add_lesson(message):
    bot.send_message(message.chat.id, "Введите информацию о занятии в формате:\n<группа> <день_недели> <название> <время>\nНапример:\n group1 monday Математика 10:00-11:00")
    bot.register_next_step_handler(message, process_add_lesson)

def process_add_lesson(message):
    try:
        group, day, name, time = message.text.split(maxsplit=3)
        day = day.lower() # Приводим день недели к нижнему регистру

        if group not in schedule:
            schedule[group] = {}

        if day not in schedule[group]:
            schedule[group][day] = []

        schedule[group][day].append(f"{name} {time}")
        save_schedule()
        bot.send_message(message.chat.id, "Занятие добавлено!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте еще раз.")

@bot.message_handler(commands=['admin'])
@admin_only
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Добавить занятие ➕", "Изменить занятие 🔄", "Удалить занятие ➖")
    bot.send_message(message.chat.id, "Админ-панель:", reply_markup=markup)


# ... (реализация команд добавления, изменения и удаления занятий)


# --- Обработка ошибок ---
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # ... (обработка неизвестных команд и сообщений)


# --- Запуск бота ---
    if __name__ == '__main__':
        try:
         bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка бота: {e}")

bot.polling(none_stop=True)
