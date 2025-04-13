import telebot
from telebot import types
import datetime
import json # Для работы с JSON

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN')

# --- Работа с расписанием (JSON) ---

try:
    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule = json.load(f)
except FileNotFoundError:
    schedule = {} # Создаем пустой словарь, если файл не найден


def save_schedule():
    with open('schedule.json', 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=4, ensure_ascii=False)


# Пример структуры данных в JSON (schedule.json):
# {
#     "group1": {
#         "monday": ["Математика 10:00-11:00", "Физика 11:15-12:15"],
#         "tuesday": ["Химия 9:00-10:00", "Биология 10:15-11:15"],
#         # ...
#     },
#     "group2": {
#         # ... расписание для другой группы
#     }
# }



# --- Обработчики команд и кнопок ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Расписание на сегодня 📚")
    item2 = types.KeyboardButton("Расписание на неделю 📅")
    # Добавьте другие кнопки по необходимости
    markup.add(item1, item2)

    bot.send_message(message.chat.id, 'Привет! Что хочешь узнать?', reply_markup=markup)



@bot.message_handler(regexp="Расписание на сегодня 📚")
def today_schedule(message):
    # 1. Получаем текущий день недели
    today = datetime.datetime.now().strftime("%A").lower() # например, "monday"

    # 2 & 3. Получаем расписание из JSON (предполагаем, что пользователь принадлежит к "group1")
    group_schedule = schedule.get("group1", {}) # Здесь нужно определить группу пользователя!
    today_lessons = group_schedule.get(today, [])

    # 4. Формируем сообщение
    if today_lessons:
        schedule_text = f"Расписание на сегодня ({today.capitalize()}):\n"
        for lesson in today_lessons:
            schedule_text += f"- {lesson}\n"
    else:
        schedule_text = "На сегодня занятий нет."

    # 5. Отправляем сообщение
    bot.send_message(message.chat.id, schedule_text)


# Аналогично реализуйте обработчик для "Расписание на неделю"
@bot.message_handler(regexp="Мой следующий урок ➡️")
def next_lesson(message):
    # 1. Определяем текущее время
    now = datetime.datetime.now()
    # 2. Определяем группу пользователя (замените на ваш способ)
    group = "group1" # !!! ЗАМЕНИТЕ НА РЕАЛЬНЫЙ СПОСОБ ОПРЕДЕЛЕНИЯ ГРУППЫ !!!
    # 3. Получаем расписание группы
    group_schedule = schedule.get(group, {})

    next_lesson_info = None
    for day, lessons in group_schedule.items():
        # Определяем день недели относительно текущего дня
        day_offset = (list(group_schedule.keys()).index(day) - list(group_schedule.keys()).index(now.strftime("%A").lower())) % 7


        for lesson_str in lessons:
            lesson_time_str = lesson_str.split()[-1] # Выделяем время из строки
            try:
                lesson_time = datetime.datetime.strptime(lesson_time_str, "%H:%M-%H:%M").time()
                lesson_datetime = datetime.datetime.combine(now.date() + datetime.timedelta(days=day_offset), lesson_time)


                if lesson_datetime > now and (next_lesson_info is None or lesson_datetime < next_lesson_info["time"]):
                    next_lesson_info = {
                        "time": lesson_datetime,
                        "lesson": lesson_str
                    }

            except ValueError:
                bot.send_message(message.chat.id, "Ошибка в формате времени в расписании.")
                return


    if next_lesson_info:
        bot.send_message(message.chat.id, f"Твой следующий урок:\n{next_lesson_info['lesson']} в {next_lesson_info['time'].strftime('%A %H:%M')}")
    else:
        bot.send_message(message.chat.id, "Ближайших уроков не найдено.")

# --- Админ-панель (упрощенная) ---
admin_id = 123456789 # !!! ЗАМЕНИТЕ НА ID АДМИНИСТРАТОРА !!!

@bot.message_handler(commands=['add_lesson'])
def add_lesson(message):
    if message.from_user.id == admin_id:
        # Логика добавления урока (группа, день, время, название)
        # ... (реализация добавления урока в schedule)
        save_schedule()
        bot.reply_to(message, "Урок добавлен.")

@bot.message_handler(commands=['remove_lesson'])
def remove_lesson(message):
    if message.from_user.id == admin_id:
        # Логика удаления урока
        # ... (реализация удаления урока из schedule)
        save_schedule()
        bot.reply_to(message, "Урок удален.")



# --- Все расписание с фильтрацией ---

@bot.message_handler(regexp="Все расписание 🎓")
def all_schedule(message):
    markup = types.InlineKeyboardMarkup()
    for group in schedule:
        markup.add(types.InlineKeyboardButton(text=group, callback_data=f"group:{group}"))
    bot.send_message(message.chat.id, "Выберите группу:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("group:"))
def show_group_schedule(call):
    group = call.data.split(":")[1]
    group_schedule = schedule.get(group, {})
    schedule_text = f"Расписание для группы {group}:\n"
    for day, lessons in group_schedule.items():
        schedule_text += f"\n{day.capitalize()}:\n"
        for lesson in lessons:
            schedule_text += f"- {lesson}\n"
    bot.send_message(call.message.chat.id, schedule_text)


bot.polling(none_stop=True)
