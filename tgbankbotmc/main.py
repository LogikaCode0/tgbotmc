import telebot
import datetime
import json
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "Token"
ADMIN_ID = 813373727  # Замените на ID создателя бота

bot = telebot.TeleBot(TOKEN)
users_data = {}  # Хранение данных о времени старта работы
banned_users = set()  # Множество для хранения забаненных пользователей
PAY_RATE = 5  # AR в час
MAX_HOURS = 12  # Максимально допустимое время работы
all_users = set()  # Множество для хранения пользователей, которые начали работу
# Флаг для ожидания ввода текста новости и сообщений пользователям
waiting_for_message = False
target_user_id = None  # ID пользователя, которому будет отправлено сообщение

# Путь к файлу для хранения забаненных пользователей
BANNED_USERS_FILE = "banned_users.json"

# Создание клавиатуры с кнопками
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("Начать работу"), KeyboardButton("Завершить работу"))
main_keyboard.add(KeyboardButton("Статус"), KeyboardButton("Отчет"))
main_keyboard.add(KeyboardButton("Связь с админом"))

admin_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.add(KeyboardButton("Статистика"))
admin_keyboard.add(KeyboardButton("Начать работу"), KeyboardButton("Завершить работу"))
admin_keyboard.add(KeyboardButton("Статус"))
admin_keyboard.add(KeyboardButton("Проверить ID пользователя"))
admin_keyboard.add(KeyboardButton("Отправить сообщение пользователю"))

# Загрузка списка заблокированных пользователей из файла
def load_banned_users():
    global banned_users
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, 'r') as f:
            try:
                banned_users = set(json.load(f))
            except json.JSONDecodeError:
                print("Ошибка при чтении списка забаненных пользователей, создаем новый список.")
                banned_users = set()

# Сохранение списка заблокированных пользователей в файл
def save_banned_users():
    with open(BANNED_USERS_FILE, 'w') as f:
        json.dump(list(banned_users), f)

# Загрузка данных при старте
load_banned_users()

@bot.message_handler(commands=['start'])
def start(message):
    # Добавляем пользователя в список всех пользователей, которые нажали start
    all_users.add(message.from_user.id)

    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Добро пожаловать, админ!", reply_markup=admin_keyboard)
    else:
        bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=main_keyboard)

# Обработчик кнопки "Отправить сообщение пользователю"
@bot.message_handler(func=lambda message: message.text == "Отправить сообщение пользователю" and message.from_user.id == ADMIN_ID)
def request_user_id(message):
    global waiting_for_message, target_user_id
    bot.reply_to(message, "Введите ID пользователя, которому хотите отправить сообщение.")
    waiting_for_message = True
    target_user_id = None

# Обработчик ввода ID пользователя
@bot.message_handler(func=lambda message: waiting_for_message and target_user_id is None and message.from_user.id == ADMIN_ID)
def receive_user_id(message):
    global target_user_id
    try:
        target_user_id = int(message.text)
        bot.reply_to(message, "Введите текст сообщения, которое хотите отправить.")
    except ValueError:
        bot.reply_to(message, "Ошибка! Введите корректный ID пользователя.")

# Обработчик ввода текста сообщения
@bot.message_handler(func=lambda message: waiting_for_message and target_user_id is not None and message.from_user.id == ADMIN_ID)
def send_user_message(message):
    global waiting_for_message, target_user_id
    user_message = message.text
    waiting_for_message = False  # Сбрасываем флаг ожидания

    try:
        bot.send_message(target_user_id, f"✉️ Сообщение от администратора:\n\n{user_message}")
        bot.reply_to(message, f"Сообщение отправлено пользователю {target_user_id}.")
    except Exception:
        bot.reply_to(message, "Ошибка! Не удалось отправить сообщение пользователю.")

# Создание глобальной переменной для отслеживания состояния ожидания ID
waiting_for_user_id_check = False

# Обработчик кнопки "Проверить ID пользователя"
@bot.message_handler(func=lambda message: message.text == "Проверить ID пользователя" and message.from_user.id == ADMIN_ID)
def request_check_id(message):
    global waiting_for_user_id_check
    bot.reply_to(message, "Введите ID пользователя, которого хотите проверить.")
    waiting_for_user_id_check = True  # Устанавливаем флаг, что мы ждем ввод ID

# Обработчик ввода ID пользователя для проверки
@bot.message_handler(func=lambda message: message.text.isdigit() and waiting_for_user_id_check and message.from_user.id == ADMIN_ID)
def check_user_id(message):
    global waiting_for_user_id_check
    user_id = int(message.text)
    try:
        # Получаем информацию о пользователе по ID
        user = bot.get_chat(user_id)
        user_name = user.username if user.username else user.first_name
        bot.reply_to(message, f"Пользователь с ID {user_id} - {user_name}")
    except Exception:
        bot.reply_to(message, "Не удалось найти информацию о пользователе с этим ID.")
    
    # Сбрасываем флаг после получения ответа
    waiting_for_user_id_check = False

@bot.message_handler(func=lambda message: message.text == "Начать работу")
def start_work(message):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        bot.reply_to(message, "Вы заблокированы и не можете начать работу.")
        return
    
    if user_id in users_data:
        bot.reply_to(message, "Вы уже начали работу! Завершите её перед новым стартом.")
    else:
        users_data[user_id] = datetime.datetime.now()
        bot.reply_to(message, "Вы начали работу! Таймер запущен.")
        bot.send_message(ADMIN_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) начал работу.")

@bot.message_handler(func=lambda message: message.text == "Завершить работу")
def stop_work(message):
    user_id = message.from_user.id
    if user_id not in users_data:
        bot.reply_to(message, "Вы ещё не начинали работу. Используйте 'Начать работу'.")
        return
    
    start_time = users_data.pop(user_id)
    end_time = datetime.datetime.now()
    worked_hours = (end_time - start_time).total_seconds() / 3600
    worked_hours = min(worked_hours, MAX_HOURS)  # Ограничение по времени
    earnings = round(worked_hours * PAY_RATE, 2)
    
    bot.reply_to(message, f"Вы отработали {worked_hours:.2f} часов и заработали {earnings} AR.")
    bot.send_message(ADMIN_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) закончил работу.\nЗаработано: {earnings} AR.")

@bot.message_handler(func=lambda message: message.text == "Статус")
def work_status(message):
    user_id = message.from_user.id
    if user_id in users_data:
        start_time = users_data[user_id]
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed_time = min(elapsed_time, MAX_HOURS)
        bot.reply_to(message, f"Вы работаете уже {elapsed_time:.2f} часов.")
    else:
        bot.reply_to(message, "Вы не начали работу. Используйте 'Начать работу'.")
        
# Флаг ожидания сообщения пользователем
waiting_for_admin_message = {}

@bot.message_handler(func=lambda message: message.text == "Связь с админом" or 
                      (message.from_user.id in waiting_for_admin_message and waiting_for_admin_message[message.from_user.id]))
def contact_admin(message):
    user_id = message.from_user.id

    if user_id in banned_users:
        bot.reply_to(message, "Вы заблокированы и не можете связаться с админом.")
        return

    # Если пользователь только нажал кнопку "Связь с админом"
    if message.text == "Связь с админом":
        waiting_for_admin_message[user_id] = True
        bot.reply_to(message, "Введите ваше сообщение для администратора:")
    else:
        # Если пользователь уже вводит сообщение после нажатия кнопки
        user_name = message.from_user.username if message.from_user.username else message.from_user.full_name
        bot.send_message(ADMIN_ID, f"📩 Сообщение от пользователя @{user_name} ({user_id}):\n\n{message.text}")
        bot.reply_to(message, "Ваше сообщение отправлено администратору!")
        
        waiting_for_admin_message[user_id] = False  # Сброс флага

@bot.message_handler(func=lambda message: message.text == "Статистика" and message.from_user.id == ADMIN_ID)
def admin_stats(message):
    if not users_data:
        bot.send_message(ADMIN_ID, "Сейчас никто не работает.")
        return
    
    # Подсчитываем количество работающих пользователей
    working_users_count = len(users_data)
    
    stats_message = f"Сейчас работают {working_users_count} человек(а):\n"
    
    for user_id, start_time in users_data.items():
        # Получаем объект пользователя по его ID
        user = bot.get_chat(user_id)
        
        # Проверяем, есть ли у пользователя username
        username = user.username if user.username else "Без username"
        
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed_time = min(elapsed_time, MAX_HOURS)
        stats_message += f"Пользователь: @{username} ({user_id}) — {elapsed_time:.2f} часов\n"
    
    bot.send_message(ADMIN_ID, stats_message)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Только администратор может блокировать пользователей.")
        return

    # Проверка, был ли передан ID пользователя для бана
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Пожалуйста, укажите ID пользователя для блокировки. Пример: /ban 123456789")
        return

    user_id_to_ban = int(message.text.split()[1])

    banned_users.add(user_id_to_ban)  # Добавляем пользователя в список забаненных
    save_banned_users()  # Сохраняем изменения в файл
    bot.reply_to(message, f"Пользователь с ID {user_id_to_ban} был заблокирован и не может начать работу.")
    bot.send_message(ADMIN_ID, f"Пользователь с ID {user_id_to_ban} был заблокирован и не может начать работу.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Только администратор может разбанивать пользователей.")
        return

    # Проверка, был ли передан ID пользователя для разбана
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Пожалуйста, укажите ID пользователя для разблокировки. Пример: /unban 123456789")
        return

    user_id_to_unban = int(message.text.split()[1])

    if user_id_to_unban in banned_users:
        banned_users.remove(user_id_to_unban)  # Убираем пользователя из списка забаненных
        save_banned_users()  # Сохраняем изменения в файл
        bot.reply_to(message, f"Пользователь с ID {user_id_to_unban} был разбанен и теперь может работать.")
        bot.send_message(ADMIN_ID, f"Пользователь с ID {user_id_to_unban} был разбанен и теперь может работать.")
    else:
        bot.reply_to(message, "Этот пользователь не заблокирован.")

# Флаг для отслеживания, нажал ли пользователь кнопку "Отчет"
waiting_for_video = {}

# Обработчик кнопки "Отчет"
@bot.message_handler(func=lambda message: message.text == "Отчет")
def request_report(message):
    user_id = message.from_user.id

    if user_id in banned_users:
        bot.reply_to(message, "Вы заблокированы и не можете отправлять отчет.")
        return

    waiting_for_video[user_id] = True  # Помечаем, что ждем видео
    bot.reply_to(message, "Пожалуйста, отправьте видео для отчета. Видео без нажатия на кнопку не принимаются!")

# Обработка видео (только если пользователь нажал "Отчет")
@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id

    # Проверяем, был ли пользователь в списке ожидающих видео
    if user_id not in waiting_for_video or not waiting_for_video[user_id]:
        bot.reply_to(message, "Вы не нажали кнопку 'Отчет'. Пожалуйста, нажмите 'Отчет' перед отправкой видео.")
        return

    # Проверка, заблокирован ли пользователь
    if user_id in banned_users:
        bot.reply_to(message, "Вы заблокированы и не можете отправить отчет.")
        return

    # Сбрасываем флаг ожидания видео
    waiting_for_video[user_id] = False

    # Получаем имя пользователя или его username
    user_name = message.from_user.username if message.from_user.username else message.from_user.full_name

    # Информируем пользователя
    bot.reply_to(message, "Ваше видео принято и передано админу. Ожидайте ответа!")

    # Пересылаем видео админу
    bot.send_message(ADMIN_ID, f"Видео от @{message.from_user.username} ({user_id}):")
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

# Отклонение всех остальных типов контента
@bot.message_handler(
    content_types=[
        'photo', 'audio', 'document', 'sticker', 'voice', 'location',
        'contact', 'animation', 'video_note', 'poll', 'dice'
    ]
)
def handle_invalid_content(message):
    bot.reply_to(message, "Я принимаю только видео. Пожалуйста, отправьте видео, иначе ваш отчет не будет принят.")

if __name__ == "__main__":
    bot.polling(none_stop=True)