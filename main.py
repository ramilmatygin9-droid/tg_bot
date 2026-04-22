import telebot
from telebot import types
import time
import random

# ТОКЕН
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

# База данных игроков в памяти
users = {}

def get_user(uid, name):
    if uid not in users:
        users[uid] = {"balance": 5000, "name": name}
    return users[uid]

# ТВОЁ МЕНЮ (кнопки в чате)
def main_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("🎰 Игры")
    btn2 = types.KeyboardButton("👤 Профиль")
    btn3 = types.KeyboardButton("💣 Бомба")
    btn4 = types.KeyboardButton("🎁 Бонус")
    btn5 = types.KeyboardButton("⚙️ Настройки")
    btn6 = types.KeyboardButton("🆘 Помощь")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, "💎 **Добро пожаловать!**\n\nТвой начальный баланс: 5000 💰\nВыбирай игру в меню ниже:", 
                     reply_markup=main_kb(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"👤 **ПРОФИЛЬ**\n\n💰 Баланс: {u['balance']} золота\n🆔 Твой ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎰 Игры")
def games_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏀 Баскетбол", callback_data="g_basketball"),
        types.InlineKeyboardButton("⚽️ Футбол", callback_data="g_football"),
        types.InlineKeyboardButton("🎯 Дартс", callback_data="g_darts"),
        types.InlineKeyboardButton("🎲 Кубик", callback_data="g_dice")
    )
    bot.send_message(message.chat.id, "🕹 **Выбери игру:**\n_(Ставка: 500 золота)_", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("g_"))
def play_game(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    if u['balance'] < 500:
        bot.answer_callback_query(call.id, "❌ Недостаточно золота!", show_alert=True)
        return

    u['balance'] -= 500
    game = call.data.split("_")[1]
    emoji_map = {"basketball": "🏀", "football": "⚽", "darts": "🎯", "dice": "🎲"}
    
    # Отправляем анимированный эмодзи
    msg = bot.send_dice(call.message.chat.id, emoji=emoji_map[game])
    time.sleep(4) # Ждем, пока анимация закончится

    # Логика выигрыша (если значение больше 3 — победа)
    if msg.dice.value >= 3:
        u['balance'] += 1200
        bot.send_message(call.message.chat.id, f"✅ **Победа!**\nВыигрыш: 1200 💰\nБаланс: {u['balance']}")
    else:
        bot.send_message(call.message.chat.id, f"❌ **Проигрыш!**\nБаланс: {u['balance']}")

@bot.message_handler(func=lambda m: m.text == "💣 Бомба")
def bomb_game(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    if u['balance'] < 500:
        bot.send_message(message.chat.id, "❌ Нужно минимум 500 золота!")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"📦 Коробка {i}", callback_data=f"bomb_{i}") for i in range(1, 5)]
    markup.add(*btns)
    bot.send_message(message.chat.id, "💣 **РЕЖИМ САПЁР**\nУгадай пустую коробку. Если там бомба — ты проиграл!", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("bomb_"))
def bomb_logic(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    bomb_pos = random.randint(1, 4)
    choice = int(call.data.split("_")[1])
    
    if choice == bomb_pos:
        u['balance'] -= 500
        bot.edit_message_text(f"💥 **БА-БАХ!** В коробке {choice} была мина!\nБаланс: {u['balance']}", call.message.chat.id, call.message.id)
    else:
        u['balance'] += 1000
        bot.edit_message_text(f"💎 **ЧИСТО!** Ты нашел сокровища!\nБаланс: {u['balance']}", call.message.chat.id, call.message.id)

@bot.message_handler(func=lambda m: m.text in ["⚙️ Настройки", "🆘 Помощь"])
def in_dev(message):
    bot.send_message(message.chat.id, "🛠 **Раздел в разработке**\nПриходи позже, мы еще кодим это меню!")

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def get_bonus(message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    u['balance'] += 1000
    bot.send_message(message.chat.id, "🎁 **Ежедневный бонус!**\nТы получил 1000 золота!")

if __name__ == "__main__":
    bot.infinity_polling()
