import telebot
from telebot import types
import time
import random

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

# База данных игроков
users = {}

def get_user(uid, name):
    if uid not in users:
        users[uid] = {"balance": 5000, "name": name}
    return users[uid]

# ГЛАВНОЕ МЕНЮ (Кнопки в сообщении)
def main_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎰 Игры", callback_data="menu_games"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
        types.InlineKeyboardButton("💣 Бомба", callback_data="menu_bomb"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="menu_bonus"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="menu_dev"),
        types.InlineKeyboardButton("🆘 Помощь", callback_data="menu_dev")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, "💎 **Добро пожаловать в игру!**\nВыбирай действие на кнопках ниже:", 
                     reply_markup=main_inline_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    
    if call.data == "menu_profile":
        text = f"👤 **ПРОФИЛЬ**\n\n💰 Баланс: {u['balance']} золота\n🆔 ID: `{call.from_user.id}`"
        bot.edit_message_text(text, call.message.chat.id, call.message.id, reply_markup=main_inline_menu(), parse_mode="Markdown")
    
    elif call.data == "menu_games":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏀 Баскетбол", callback_data="g_basketball"),
            types.InlineKeyboardButton("⚽️ Футбол", callback_data="g_football"),
            types.InlineKeyboardButton("🎯 Дартс", callback_data="g_darts"),
            types.InlineKeyboardButton("🎲 Кубик", callback_data="g_dice"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="menu_back")
        )
        bot.edit_message_text("🕹 **Выбери игру (Ставка 500):**", call.message.chat.id, call.message.id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "menu_bomb":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(f"📦 {i}", callback_data=f"bomb_{i}") for i in range(1, 5)]
        markup.add(*btns, types.InlineKeyboardButton("⬅️ Назад", callback_data="menu_back"))
        bot.edit_message_text("💣 **РЕЖИМ БОМБА**\nУгадай пустую коробку:", call.message.chat.id, call.message.id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "menu_bonus":
        u['balance'] += 1000
        bot.answer_callback_query(call.id, "🎁 Бонус 1000 золота получен!", show_alert=True)
        bot.edit_message_text(f"💎 Баланс обновлен! Теперь у тебя {u['balance']} 💰", call.message.chat.id, call.message.id, reply_markup=main_inline_menu())

    elif call.data == "menu_back":
        bot.edit_message_text("💎 **Главное меню:**", call.message.chat.id, call.message.id, reply_markup=main_inline_menu())

    elif call.data == "menu_dev":
        bot.answer_callback_query(call.id, "🛠 В разработке...", show_alert=True)

# ЛОГИКА ИГР (Мячи, Дартс и т.д.)
@bot.callback_query_handler(func=lambda call: call.data.startswith("g_"))
def play_game(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    if u['balance'] < 500:
        bot.answer_callback_query(call.id, "❌ Нет золота!", show_alert=True)
        return

    u['balance'] -= 500
    game = call.data.split("_")[1]
    emoji_map = {"basketball": "🏀", "football": "⚽", "darts": "🎯", "dice": "🎲"}
    
    msg = bot.send_dice(call.message.chat.id, emoji=emoji_map[game])
    time.sleep(4)

    if msg.dice.value >= 3:
        u['balance'] += 1200
        bot.send_message(call.message.chat.id, f"✅ **Победа!** +1200 💰\nБаланс: {u['balance']}", reply_markup=main_inline_menu())
    else:
        bot.send_message(call.message.chat.id, f"❌ **Проигрыш!**\nБаланс: {u['balance']}", reply_markup=main_inline_menu())

# ЛОГИКА БОМБЫ
@bot.callback_query_handler(func=lambda call: call.data.startswith("bomb_"))
def bomb_logic(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    if random.choice([True, False]):
        u['balance'] += 1000
        bot.edit_message_text(f"💎 **Пусто!** Ты выиграл 1000! Баланс: {u['balance']}", call.message.chat.id, call.message.id, reply_markup=main_inline_menu())
    else:
        u['balance'] -= 500
        bot.edit_message_text(f"💥 **БОМБА!** Баланс: {u['balance']}", call.message.chat.id, call.message.id, reply_markup=main_inline_menu())

bot.infinity_polling()
