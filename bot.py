import asyncio
import logging
import random
import sqlite3
import time
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"
ERROR_EMOJI_ID = "5240241223632954241"
SKUPSHIK_ID = "5452136652111620778" 

# Медали
MEDAL_1_ID = "5440539497383087970" 
MEDAL_2_ID = "5447203607294265305" 
MEDAL_3_ID = "5453902265922376865" 

# Кристаллы
CRYSTAL_BLUE = "6269061400568532047"    
CRYSTAL_RED = "6269242583763913842"     
CRYSTAL_RAINBOW = "626938354888535501"  

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, 
                   username TEXT, last_bonus INTEGER DEFAULT 0,
                   blue_cry INTEGER DEFAULT 0, red_cry INTEGER DEFAULT 0, rain_cry INTEGER DEFAULT 0)''')
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, blue_cry, red_cry, rain_cry FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username) VALUES (?, 0, 1, '', ?)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "blue": 0, "red": 0, "rain": 0}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus": data[3], "blue": data[4], "red": data[5], "rain": data[6]}

# --- АДМИН-БОТ (СТАРЫЕ ТЕКСТЫ) ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления</b>\n\nКоманды:\n/add КОД СУММА ВРЕМЯ (30m, 1h, 1d)\n/del КОД\n/list", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code, reward, time_str = args[1].upper(), int(args[2]), args[3].lower()
        if time_str == "0":
            expire = "NEVER"
        else:
            amount = int(re.search(r'\d+', time_str).group())
            delta = timedelta(minutes=amount) if 'm' in time_str else timedelta(days=amount) if 'd' in time_str else timedelta(hours=amount)
            expire = (datetime.now() + delta).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод <b>{code}</b> создан!\n💰 Награда: {reward}\n⏰ Истекает: {expire}", parse_mode="HTML")
    except: await message.answer("Ошибка! /add START 5000 1h")

# --- ИГРОВОЙ БОТ ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: pass
    
    luck = random.random()
    found_text = ""
    if luck < 0.02:
        db_query("UPDATE players SET rain_cry = rain_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_RAINBOW}'>🌈</tg-emoji> <b>Найдено: Радужный кристалл!</b>"
    elif luck < 0.10:
        db_query("UPDATE players SET red_cry = red_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_RED}'>🔴</tg-emoji> <b>Найдено: Красный кристалл!</b>"
    elif luck < 0.30:
        db_query("UPDATE players SET blue_cry = blue_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_BLUE}'>🔵</tg-emoji> <b>Найдено: Голубой кристалл!</b>"

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Найдено: <b>{reward}</b> монет{found_text}', parse_mode="HTML")

@dp_main.message(Command("inv"))
async def inv_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = (f"🎒 <b>Твой инвентарь:</b>\n\n"
            f"🔵 Голубые: {p['blue']} шт.\n"
            f"🔴 Красные: {p['red']} шт.\n"
            f"🌈 Радужные: {p['rain']} шт.\n\n"
            f"Продать всё — /sell")
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("sell"))
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    total = (p['blue'] * 1000) + (p['red'] * 5000) + (p['rain'] * 25000)
    if total == 0:
        await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя нет кристаллов!")
        return
    db_query("UPDATE players SET balance = balance + ?, blue_cry = 0, red_cry = 0, rain_cry = 0 WHERE user_id = ?", (total, message.from_user.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> <b>Скупщик купил всё за {total} монет!</b>", parse_mode="HTML")

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ майнеров:</b>\n\n"
    for i, u in enumerate(top, 1):
        icon = {1:f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>', 2:f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>', 3:f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'}.get(i, f"<b>{i}.</b>")
        text += f"{icon} @{u[0] if u[0] else u[2]} — <b>{u[1]}</b>\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b>\n\nКопай руду через /mine', reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

async def main():
    init_db()
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
