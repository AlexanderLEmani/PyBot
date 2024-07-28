import telebot
import re
from collections import defaultdict
import datetime

# Ваш ключ API от Telegram
API_KEY = '7471180829:AAGCZh46l8fp8WHsu17Sf9irRdNR_HYZhkU'
bot = telebot.TeleBot(API_KEY)

# Словарь для хранения чаевых для каждого дня и официанта
tips_dict = defaultdict(lambda: defaultdict(float))
# Множество для хранения обработанных временных меток
processed_times = set()
# Переменная для хранения количества официантов
waiters_count = 0
# Переменная для хранения состояния бота
current_state = None
COMMISSION_RATE = 0.04


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Давай сюда свои копейки, бедолага")  # Отладочное сообщение


# Команда /total для подсчета чаевых
@bot.message_handler(commands=['total'])
def handle_total(message):
    print("/total command received")  # Отладочное сообщение
    # Используем текущую дату
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"Checking total for {date}")  # Отладочное сообщение

    # Проверим все ключи в словаре для отладки
    print(f"Current keys in tips_dict: {list(tips_dict.keys())}")  # Отладочное сообщение

    if date in tips_dict:
        print(f"Found tips for {date}: {tips_dict[date]}")  # Отладочное сообщение
        total_tips = sum(tips_dict[date].values())
        total_tips_after_commission = total_tips * (1 - COMMISSION_RATE)
        response = [
            f"Общая сумма чаевых за {date}: {total_tips:.2f} грн",
            f"Сумма после вычета комиссии (4%): {total_tips_after_commission:.2f} грн"
        ]

        for waiter, tips in tips_dict[date].items():
            tips_after_commission = tips * (1 - COMMISSION_RATE)
            response.append(
                f"Официант №{waiter}: {tips:.2f} грн (после вычета комиссии: {tips_after_commission:.2f} грн)")

        bot.reply_to(message, "\n".join(response))
    else:
        print(f"No tips found for {date}")  # Отладочное сообщение
        bot.reply_to(message, "Нет данных о чаевых за сегодня.")


# Команда /reset для обнуления чаевых
@bot.message_handler(commands=['reset'])
def reset_tips(message):
    print("/reset command received")  # Отладочное сообщение
    # Используем текущую дату
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if date in tips_dict:
        del tips_dict[date]
        bot.reply_to(message, f"Чаевые за {date} обнулены.")
        print(f"Tips for {date} have been reset.")  # Отладочное сообщение
    else:
        bot.reply_to(message, "Нет данных о чаевых за сегодня.")
        print(f"No tips found for {date} to reset.")  # Отладочное сообщение


# Команда /divide для деления чаевых
@bot.message_handler(commands=['divide'])
def ask_waiters_count(message):
    global current_state
    current_state = 'ASK_WAITERS_COUNT'
    bot.reply_to(message, "Сколько целых официантов сегодня на смене?")
    print("/divide command received")  # Отладочное сообщение


# Обработка ответа пользователя с количеством официантов
@bot.message_handler(func=lambda message: current_state == 'ASK_WAITERS_COUNT')
def handle_waiters_count(message):
    global waiters_count, current_state
    try:
        waiters_count = int(message.text)
        current_state = None
        bot.reply_to(message, f"На смене {waiters_count} человек. Подсчитываю чаевые...")
        calculate_tips(message)
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите корректное число.")


def calculate_tips(message):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if date in tips_dict:
        total_tips = sum(tips_dict[date].values())
        total_tips_after_commission = total_tips * (1 - COMMISSION_RATE)
        tips_per_waiter = total_tips_after_commission / waiters_count
        bot.reply_to(message, f"Общая сумма чаевых за {date}: {total_tips_after_commission:.2f} грн\n"
                              f"Каждый официант получает: {tips_per_waiter:.2f} грн")
        print(f"Tips calculated for {waiters_count} waiters")  # Отладочное сообщение
    else:
        bot.reply_to(message, "Нет данных о чаевых за сегодня.")
        print(f"No tips found for {date} to divide.")  # Отладочное сообщение


# Обработка сообщений с информацией о чаевых
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    if message.text.startswith('/'):
        return

    text = message.text
    print(f"Received message: {text}")  # Отладочное сообщение

    # Регулярное выражение для поиска времени получения чаевых, чаевых и номера официанта в сообщении
    time_match = re.search(r'\d{2}:\d{2}:\d{2} \d{2}\.\d{2}\.\d{4}', text)
    tips_match = re.search(r'Чайові:\s*([\d,]+\.?\d*)\s*грн', text)
    waiter_match = re.search(r'Офіціант:\s*(\d+)', text)

    if time_match and tips_match and waiter_match:
        message_time = time_match.group(0)
        tips = float(tips_match.group(1).replace(',', '.'))
        waiter = int(waiter_match.group(1))

        if message_time in processed_times:
            bot.reply_to(message, "Эти чаевые уже были добавлены.")
            print("Duplicate message detected. Skipping.")  # Отладочное сообщение
            return

        # Используем текущую дату
        date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Сохраняем чаевые в словарь
        tips_dict[date][waiter] += tips
        processed_times.add(message_time)  # Сохраняем временную метку сообщения

        bot.reply_to(message, f"Чаевые добавлены: {tips} грн для официанта №{waiter}")
        print(f"Added tips: {tips} грн for waiter #{waiter} on {date}")  # Отладочное сообщение
        print(f"Current tips_dict: {dict(tips_dict)}")  # Отладочное сообщение
        print(f"Processed times: {processed_times}")  # Отладочное сообщение
    else:
        bot.reply_to(message, "Сообщение не содержит валидных данных о чаевых.")
        print("Message does not contain valid tips data.")  # Отладочное сообщение


if __name__ == '__main__':
    print("Bot is starting...")  # Отладочное сообщение
    bot.polling(none_stop=True)
