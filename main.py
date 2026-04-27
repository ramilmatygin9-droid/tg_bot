import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Твой токен уже здесь
TOKEN = "8693763218:AAGoc7Y2xTFZeXsaZ_mzksRkFUhOnA3Zj10"
# Ссылка на твое Mini App (замени на свою рабочую ссылку GitHub/Vercel)
WEB_APP_URL = "https://your-site-url.com" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Работа с Базой Данных (SQLite) ---
def init_db():
    conn = sqlite3.connect("game_base.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER, level INTEGER)''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("game_base.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, level FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return data
    return (1000, 1) # Стартовый капитал 1000 и 1 уровень

# --- Обработчики команд ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    balance, level = get_user_data(user_id)
    
    # Сохраняем нового игрока, если его нет
    conn = sqlite3.connect("game_base.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, level) VALUES (?, ?, ?)", 
                   (user_id, balance, level))
    conn.commit()
    conn.close()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕹 ИГРАТЬ (Mini App)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💎 Мой Профиль", callback_data="my_profile")]
    ])

    await message.answer(
        f"🔥 **Добро пожаловать в Case Clicker!**\n\n"
        f"💰 Твой баланс: {balance} монет\n"
        f"⭐ Твой уровень: {level}\n\n"
        f"Нажимай кнопку ниже, чтобы открыть крутую рулетку с кейсами!",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "my_profile")
async def profile_callback(callback: types.CallbackQuery):
    balance, level = get_user_data(callback.from_user.id)
    await callback.answer() # Убираем "часики" с кнопки
    await callback.message.answer(
        f"👤 **Профиль {callback.from_user.first_name}:**\n"
        f"💵 Баланс: {balance} 💰\n"
        f"📊 Уровень: {level}\n"
        f"🏆 Статус: {'Шейх' if balance > 10000 else 'Игрок'}",
        parse_mode="Markdown"
    )

async def main():
    init_db() # Создаем базу данных при запуске
    print("✅ Бот запущен! Ошибок нет.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
