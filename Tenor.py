import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
TOKEN = "8156857401:AAGxshuoGT-sV6hgMfpnFmQAHF7BsAjINjk" # Сбрось его в @BotFather!

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('dick_game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            size INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_size(user_id):
    conn = sqlite3.connect('dick_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT size FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_size(user_id, add_cm):
    conn = sqlite3.connect('dick_game.db')
    cursor = conn.cursor()
    # Если юзера нет - создаем, если есть - прибавляем размер
    cursor.execute('''
        INSERT INTO users (user_id, size) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET size = size + ?
    ''', (user_id, add_cm, add_cm))
    conn.commit()
    conn.close()

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("📏 Добро пожаловать в игру! Жми /grow, чтобы вырастить своего гиганта!")

@dp.message(Command("grow"))
async def cmd_grow(message: types.Message):
    user_id = message.from_user.id
    growth = random.randint(1, 10) # Прирост от 1 до 10 см
    
    update_size(user_id, growth)
    new_size = get_size(user_id)
    
    # Тот самый кастомный эмодзи (нужен ID)
    # Если хочешь обычный баклажан, просто ставь 🍆
    emoji = "<tg-emoji emoji-id='5368324170671202286'>🍆</tg-emoji>"
    
    await message.answer(
        f"📈 Растишка сработала! Твой прибор увеличился на **{growth} см**.\n"
        f"Теперь его длина: **{new_size} см** {emoji}",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    conn = sqlite3.connect('dick_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, size FROM users ORDER BY size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return await message.answer("Список пуст!")
    
    text = "<b>🏆 Топ гигантов:</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. ID {row[0]}: <b>{row[1]} см</b>\n"
    
    await message.answer(text, parse_mode=ParseMode.HTML)

# --- ЗАПУСК ---
async def main():
    init_db() # Создаем базу при запуске
    print("Бот запущен и готов к измерениям!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
