import telebot
from telebot import types
import time
import random

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

users = {}

def get_user(uid, name):
    if uid not in users:
        users[uid] = {"balance": 5000, "name": name}
    return users[uid]

def main_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🎯 Игры", "👤 Профиль")
    markup.add("💣 Сапёр (Бомбы)", "🎁 Бонус")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, "💎 Добро пожаловать в игровой клуб!", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"👤 **Игрок:** {u['name']}\n💰 **Баланс:** {u['balance']} золота", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def bonus(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    u['balance'] += 1000
    bot.send_message(message.chat.id, "💵 +1000 золота в карман!")

# РАЗДЕЛ ИГР С АНИМАЦИЕЙ
@bot.message_handler(func=lambda m: m.text == "🎯 Игры")
def games_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏀 Баскетбол", callback_data="play_basketball"),
        types.InlineKeyboardButton("⚽️ Футбол", callback_data="play_football"),
        types.InlineKeyboardButton("🎯 Дартс", callback_data="play_darts"),
        types.InlineKeyboardButton("🎲 Кубик", callback_data="play_dice"),
        types.InlineKeyboardButton("🎰 Казино (В разработке)", callback_data="dev")
    )
    bot.send_message(message.chat.id, "Выбери игру (ставка 500):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("play_"))
def play_animated(call):
    uid = call.from_user.id
    u = get_user(uid, call.from_user.first_name)
    
    if u['balance'] < 500:
        bot.answer_callback_query(call.id, "❌ Мало золота!")
        return

    u['balance'] -= 500
    game = call.data.split("_")[1]
    
    # Эмодзи анимации
    emoji = {"basketball": "🏀", "football": "⚽", "darts": "🎯", "dice": "🎲"}[game]
    
    msg = bot.send_dice(call.message.chat.id, emoji=emoji)
    val = msg.dice.value
    
    time.sleep(4) # Ждем пока мяч/дротик долетит

    # Условия выигрыша (у каждого эмодзи свои победные значения)
    win = False
    if game == "basketball" and val >= 4: win = True
    if game == "football" and val >= 3: win = True
    if game == "darts" and val == 6: win = True
    if game == "dice" and val >= 4: win = True

    if win:
        u['balance'] += 1200
        bot.send_message(call.message.chat.id, f"✅ КРАСАВА! Выиграл 1200! Баланс: {u['balance']}")
    else:
        bot.send_message(call.message.chat.id, f"❌ Мимо! Баланс: {u['balance']}")

# РЕЖИМ БОМБЫ
@bot.message_handler(func=lambda m: m.text == "💣 Сапёр (Бомбы)")
def bomb_start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"📦 {i}", callback_data=f"b_{i}") for i in range(1, 5)]
    markup.add(*btns)
    bot.send_message(message.chat.id, "Угадай, в какой коробке НЕТ бомбы (Ставка 500):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("b_"))
def bomb_logic(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    if u['balance'] < 500: return
    
    bomb = random.randint(1, 4)
    choice = int(call.data.split("_")[1])
    
    if choice == bomb:
        u['balance'] -= 500
        bot.edit_message_text(f"💥 БА-БАХ! Там была бомба! Баланс: {u['balance']}", call.message.chat.id, call.message.id)
    else:
        u['balance'] += 1000
        bot.edit_message_text(f"💎 Пусто! Ты забрал 1000 золота. Баланс: {u['balance']}", call.message.chat.id, call.message.id)

@bot.callback_query_handler(func=lambda call: call.data == "dev")
def dev(call):
    bot.answer_callback_query(call.id, "⏳ Эта игра ещё в разработке!", show_alert=True)

bot.infinity_polling()
