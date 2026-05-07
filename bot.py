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

# Эмодзи и Premium ID
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
ERROR_EMOJI_ID = "5240241223632954241"
SKUPSHIK_ID = "5452136652111620778" 
GIFT_ID = "5792071541084659564"

# Медали
MEDAL_1 = "5440539497383087970" 
MEDAL_2 = "5447203607294265305" 
MEDAL_3 = "5453902265922376865" 

# Кристаллы (ID из твоих дампов)
CRYSTAL_BLUE = "6269061400568532047"    # Голубой (Обычный)
CRYSTAL_RED = "6269242583763913842"     # Красный (Редкий)
CRYSTAL_RAINBOW = "626938354888535501"  # Радужный (Очень редкий)

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
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], 
            "last_bonus": data[3], "blue": data[4], "red": data[5], "rain": data[6]}

# --- АДМИН-БОТ (УПРАВЛЕНИЕ ПРОМО) ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer(
        "🛠 <b>Панель управления промокодами</b>\n\n"
        "• /add КОД СУММА ВРЕМЯ (напр. 10m, 1h, 1d)\n"
        "• /del КОД - Удалить\n"
        "• /list - Все коды", parse_mode="HTML"
    )

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
            if 'm' in time_str: delta = timedelta(minutes=amount)
            elif 'd' in time_str: delta = timedelta(days=amount)
            else: delta = timedelta(hours=amount)
            expire = (datetime.now() + delta).strftime("%Y-%m-%d %H:%M:%S")
        
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Код <b>{code}</b> на {reward} монет создан! (До: {expire})", parse_mode="HTML")
    except: await message.answer("Ошибка! Формат: /add START 5000 1h")

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    text = "🎫 <b>Список кодов:</b>\n\n" + "\n".join([f"• <code>{p[0]}</code> | {p[1]}💰 | До: {p[2]}" for p in promos])
    await message.answer(text if promos else "Кодов нет.", parse_mode="HTML")

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
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f"⛏ <b>Копаем...</b> (Ждать {wait_time}с)", parse_mode="HTML")
    await asyncio.sleep(wait_time)
    
    luck = random.random()
    found_text = ""
    # Шансы выпадения кристаллов
    if luck < 0.02: # 2% Радужный
        db_query("UPDATE players SET rain_cry = rain_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_RAINBOW}'>🌈</tg-emoji> <b>Радужный кристалл!</b>"
    elif luck < 0.10: # 10% Красный
        db_query("UPDATE players SET red_cry = red_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_RED}'>🔴</tg-emoji> <b>Красный кристалл!</b>"
    elif luck < 0.30: # 30% Голубой
        db_query("UPDATE players SET blue_cry = blue_cry + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        found_text = f"\n<tg-emoji emoji-id='{CRYSTAL_BLUE}'>🔵</tg-emoji> <b>Голубой кристалл!</b>"

    reward = int(random.randint(200, 500) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    await message.answer(f"💰 Найдено: <b>{reward}</b> монет{found_text}", parse_mode="HTML")

@dp_main.message(Command("inv"))
async def inv_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = (f"🎒 <b>Твой инвентарь:</b>\n\n"
            f"🔵 Голубые: {p['blue']} шт.\n"
            f"🔴 Красные: {p['red']} шт.\n"
            f"🌈 Радужные: {p['rain']} шт.\n\n"
            f"Продать всё скупщику — /sell")
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("sell"))
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    total_price = (p['blue'] * 1000) + (p['red'] * 5000) + (p['rain'] * 25000)
    
    if total_price == 0:
        await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя нет кристаллов!")
        return

    db_query("UPDATE players SET balance = balance + ?, blue_cry = 0, red_cry = 0, rain_cry = 0 WHERE user_id = ?", 
             (total_price, message.from_user.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> <b>Скупщик купил всё за {total_price} монет!</b>", parse_mode="HTML")

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_users = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ богатых майнеров:</b>\n\n"
    medals = {1: f'<tg-emoji emoji-id="{MEDAL_1}">🥇</tg-emoji>', 2: f'<tg-emoji emoji-id="{MEDAL_2}">🥈</tg-emoji>', 3: f'<tg-emoji emoji-id="{MEDAL_3}">🥉</tg-emoji>'}
    for i, user in enumerate(top_users, 1):
        rank = medals.get(i, f"<b>{i}.</b>")
        text += f"{rank} @{user[0] if user[0] else user[2]} — <b>{user[1]}</b> 💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f"<tg-emoji emoji-id='{BALANCE_ID}'>💳</tg-emoji> Баланс: <b>{p['balance']}</b>", parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if promo:
        reward, expire_at = promo
        p = get_player(message.from_user.id)
        if expire_at != "NEVER" and datetime.now() > datetime.strptime(expire_at, "%Y-%m-%d %H:%M:%S"):
            await message.reply("🚫 Срок промокода истек!")
            return
        if code in p["used_promos"]: 
            await message.reply("❌ Ты уже использовал этот код!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (reward, ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ Промокод активирован! +{reward} монет.")

async def main():
    init_db()
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
