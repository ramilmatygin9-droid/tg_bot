import telebot
from telebot import types
import random

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

# База данных (в памяти)
users = {}

def get_user(uid, name):
    if uid not in users:
        users[uid] = {"balance": 5000, "name": name, "wins": 0}
    return users[uid]

# Главное меню
def main_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💣 Сапёр (Бомба)", "👤 Профиль")
    markup.add("🎮 Другие игры", "🎁 Бонус")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, "🌕 Добро пожаловать! Ты в игре.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"👤 **Игрок:** {u['name']}\n💰 **Баланс:** {u['balance']} золота\n🏆 **Побед:** {u['wins']}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def bonus(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    u['balance'] += 1000
    bot.send_message(message.chat.id, "🎁 Ты получил ежедневный бонус: 1000 золота!")

@bot.message_handler(func=lambda m: m.text == "🎮 Другие игры")
def other_games(message):
    bot.send_message(message.chat.id, "⏳ Эти игры сейчас находятся **в разработке**...")

# РЕЖИМ БОМБЫ
@bot.message_handler(func=lambda m: m.text == "💣 Сапёр (Бомба)")
def bomb_start(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    if u['balance'] < 500:
        bot.send_message(message.chat.id, "❌ Недостаточно золота (нужно 500)!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"📦 Коробка {i}", callback_data=f"bomb_{i}") for i in range(1, 5)]
    markup.add(*btns)
    
    bot.send_message(message.chat.id, "💣 **Игра: Сапёр**\n\nВ одной из 4 коробок спрятана бомба. Угадай пустую, чтобы забрать приз!", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("bomb_"))
def bomb_logic(call):
    uid = call.from_user.id
    u = users[uid]
    
    bomb_pos = random.randint(1, 4)
    chosen = int(call.data.split("_")[1])
    
    if chosen == bomb_pos:
        u['balance'] -= 500
        bot.edit_message_text(f"💥 **БАБАХ!** Ты наткнулся на бомбу в коробке {chosen}!\n➖ 500 золота. Баланс: {u['balance']}", call.message.chat.id, call.message.id)
    else:
        u['balance'] += 1000
        u['wins'] += 1
        bot.edit_message_text(f"💎 **Удача!** Коробка {chosen} была пуста!\n➕ 1000 золота. Баланс: {u['balance']}", call.message.chat.id, call.message.id)

if __name__ == "__main__":
    bot.infinity_polling()
