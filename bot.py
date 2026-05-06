import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA"
OWNER_ID = 8462392581 

# Premium IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
ERROR_EMOJI_ID = "5240241223632954241"
MEDAL_1_ID = "5440539497383087970"
MEDAL_2_ID = "5447203607294265305"
MEDAL_3_ID = "5453902265922376865"

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- СТАРАЯ БАЗА (БЕЗ ИЗМЕНЕНИЙ) ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, last_bonus_time TEXT, username TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute(query, params)
    res = cur.fetchone() if fetchone else (cur.fetchall() if fetchall else None)
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id, username=None):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus_time FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, 0, 1, '', None, ?)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus_time": None}
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus_time": data[3]}

# --- КЛАВИАТУРА ИЗ САМОЙ ПЕРВОЙ ВЕРСИИ ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⛏ Копать"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="🎁 Бонус")]
    ], resize_keyboard=True)

# --- ИСПРАВЛЕННЫЙ ТОП С ПРЕМИУМ МЕДАЛЯМИ ---
@dp_main.message(F.text == "🏆 Топ")
@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    if not top_players:
        await message.answer("В шахте пока никого нет...")
        return

    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    for i, player in enumerate(top_players, 1):
        username, balance, user_id = player
        name = f"@{username}" if username else f"ID: {user_id}"
        
        # Назначаем новые медали
        if i == 1: medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2: medal = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3: medal = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        else: medal = f"<b>{i}.</b>"
            
        text += f"{medal} {name} — <b>{balance}</b> монет\n"
    await message.answer(text, parse_mode="HTML")

# --- КОПАНИЕ С ПРЕМИУМ КИРКОЙ ---
@dp_main.message(F.text == "⛏ Копать")
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    wait_time = random.randint(3, 7) # Старая быстрая задержка
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>', parse_mode="HTML")
    
    await asyncio.sleep(wait_time)
    
    reward = random.randint(100, 500)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Ты накопал <b>{reward}</b> монет!', parse_mode="HTML")

# --- БАЛАНС И БОНУС ---
@dp_main.message(F.text == "💰 Баланс")
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'Твой баланс: <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp_main.message(F.text == "🎁 Бонус")
async def bonus_cmd(message: types.Message):
    reward = 500
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await message.answer(f"🎁 Ты получил ежедневный бонус <b>{reward}</b> монет!", parse_mode="HTML")

# --- СТАРТ ---
@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Старый добрый Майнер запущен!</b>', 
                         reply_markup=main_kb(), parse_mode="HTML")

# --- ОБРАБОТКА ПРОМОКОДОВ ---
@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    code = message.text.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if not promo:
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Код неверный!', parse_mode="HTML")
    else:
        await message.reply("✅ Бонус начислен!")

async def main():
    init_db()
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
