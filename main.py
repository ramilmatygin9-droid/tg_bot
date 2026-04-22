import telebot
from telebot import types
import time

# Твой токен
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

# Временная база данных пользователей
users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {"balance": 1000, "games": 0}
    return users[uid]

@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Игры", "👤 Профиль")
    markup.add("⚙️ Настройки")
    
    bot.send_message(message.chat.id, 
                     f"👋 Привет, {message.from_user.first_name}!\n"
                     f"Твой баланс: {user['balance']} 💰\n\n"
                     f"Выбирай раздел в меню ниже:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, 
                     f"🆔 Твой ID: {message.from_user.id}\n"
                     f"💰 Баланс: {user['balance']} золота\n"
                     f"🕹 Игр сыграно: {user['games']}")

@bot.message_handler(func=lambda m: m.text == "🎮 Игры")
def games_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎲 Бросить кубик (ставка 100)", callback_data="dice"))
    bot.send_message(message.chat.id, "Выбирай игру:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "dice")
def play_dice(call):
    user = get_user(call.from_user.id)
    if user['balance'] < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно золота!")
        return

    user['balance'] -= 100
    user['games'] += 1
    
    msg = bot.send_dice(call.message.chat.id)
    value = msg.dice.value
    time.sleep(3) # Ждем, пока кубик докрутится
    
    if value >= 4:
        user['balance'] += 250
        bot.send_message(call.message.chat.id, f"🎉 Выпало {value}! Ты выиграл 250 золота!")
    else:
        bot.send_message(call.message.chat.id, f"😢 Выпало {value}. Повезет в следующий раз!")

if __name__ == "__main__":
    print("Бот оживает...")
    bot.infinity_polling()
