import asyncio
import logging
import random
import sqlite3
import time
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
MEDAL_1_ID = "5440539497383087970" 
MEDAL_2_ID = "5447203607294265305" 
MEDAL_3_ID = "5453902265922376865" 

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, username TEXT, last_bonus INTEGER DEFAULT 0)''')
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username) VALUES (?, 0, 1, '', ?)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus": data[3]}

# --- АДМИН-БОТ (УПРАВЛЕНИЕ ПРОМО) ---

@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления промокодами</b>\n\n• <code>/add КОД СУММА ЧАСЫ</code>\n• <code>/del КОД</code>\n• <code>/list</code>", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code, reward, hours = args[1].upper(), int(args[2]), int(args[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод <b>{code}</b> создан!", parse_mode="HTML")
    except: await message.answer("Ошибка! /add CODE 5000 24")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        code = message.text.split()[1].upper()
        db_query("DELETE FROM promo_codes WHERE code = ?", (code,), commit=True)
        await message.answer(f"🗑 Удален: {code}")
    except: await message.answer("Ошибка! /del CODE")

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    text = "🎫 <b>Промокоды:</b>\n" + "\n".join([f"• {p[0]} | {p[1]}💰" for p in promos])
    await message.answer(text if promos else "Пусто.", parse_mode="HTML")

# --- ИГРОВОЙ БОТ ---

SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b>\n\nКопай руду через /mine', reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: pass
    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Найдено: <b>{reward}</b> монет', parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        h, m = rem // 3600, (rem % 3600) // 60
        await message.answer(f"⏳ Бонус можно взять через <b>{h}ч. {m}м.</b>", parse_mode="HTML")
        return
    gift = random.randint(500, 2000)
    db_query("UPDATE players SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (gift, now, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Вы получили ежедневный бонус: <b>{gift}</b> монет!', parse_mode="HTML")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    kb.append([InlineKeyboardButton(text="🎫 Ввести промокод", callback_data="open_promo")])
    await message.answer(f'🛒 <b>Магазин кирок</b>\nТвоя кирка: {SHOP_PICKS[p["pick_lvl"]]["name"]}', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data == "open_promo")
async def open_promo_cb(callback: types.CallbackQuery):
    await callback.message.answer(f'<tg-emoji emoji-id="{SHOP_ICON_ID}">📝</tg-emoji> <b>Введите промокод в чат:</b>', parse_mode="HTML")
    await callback.answer()

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl, p = int(c.data.split("_")[1]), get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Недостаточно монет!", show_alert=True)

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ майнеров:</b>\n\n"
    for i, pl in enumerate(top, 1):
        text += f"<b>{i}.</b> @{pl[0] if pl[0] else pl[2]} — <b>{pl[1]}</b>\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b>', parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if promo:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]: await message.reply("❌ Уже использовано.")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ +{promo[0]} монет!")
    else: 
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует!', parse_mode="HTML")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/shop", description="🛒 Магазин"),
        BotCommand(command="/top", description="🏆 Топ"),
        BotCommand(command="/bonus", description="🎁 Бонус"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
