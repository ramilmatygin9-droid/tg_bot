import asyncio
import logging
import random
import sqlite3
import time
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# --- ИНИЦИАЛИЗАЦИЯ ЛОГОВ ---
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ТОКЕНОВ ---
MAIN_TOKEN = "8156857401:AAFkS4GaCYxGEyFyAwgqsqyah-d9PPNHeH0" # Твой новый токен
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# --- ID ПРЕМИУМ ЭМОДЗИ ---
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"        
INVENTORY_ID = "5431445210141852444"
ERROR_EMOJI_ID = "5240241223632954241" 
STAR_TOP_ID = "5472256585323522641"
CASE_EMOJI_ID = "5215535352319602416"

# --- ДАННЫЕ О КРИСТАЛЛАХ ---
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "price": 5000},
    "Premium1": {"name": "Премиум кристалл I", "price": 10000},
    "Premium2": {"name": "Премиум кристалл II", "price": 15000},
    "Premium3": {"name": "Премиум кристалл III", "price": 25000}
}

# --- МАГАЗИН КЕЙСОВ ---
CASES_DATA = {
    "common": {"name": "📦 Обычный кейс", "price": 5000},
    "mythic": {"name": "🎁 Мифический кейс", "price": 25000}
}

# --- ТАБЛИЦА КИРОК (10 УРОВНЕЙ) ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.8},
    3: {"name": "Железная кирка", "price": 15000, "mult": 3.0},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 6.5},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 12.0},
    6: {"name": "Обсидиановая кирка", "price": 450000, "mult": 28.0},
    7: {"name": "Изумрудная кирка", "price": 1200000, "mult": 65.0},
    8: {"name": "Магматическая кирка", "price": 3000000, "mult": 140.0},
    9: {"name": "Незеритовая кирка", "price": 7500000, "mult": 350.0},
    10: {"name": "👑 КИРКА БОГА ШАХТЫ", "price": 20000000, "mult": 1000.0}
}

active_miners = set()
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
                    username TEXT, last_bonus INTEGER DEFAULT 0, inventory TEXT DEFAULT '1', 
                    crystals TEXT DEFAULT '{}', cases TEXT DEFAULT '{}')''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                    (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    
    cur.execute("PRAGMA table_info(players)")
    cols = [c[1] for c in cur.fetchall()]
    if 'crystals' not in cols: cur.execute("ALTER TABLE players ADD COLUMN crystals TEXT DEFAULT '{}'")
    if 'cases' not in cols: cur.execute("ALTER TABLE players ADD COLUMN cases TEXT DEFAULT '{}'")
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, inventory, crystals, username, cases FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, inventory, crystals, cases) VALUES (?, 0, 1, '', ?, '1', '{}', '{}')", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "inventory": [1], "crystals": {}, "username": username, "cases": {}}
    return {
        "balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3], "inventory": [int(x) for x in data[4].split(",")] if data[4] else [1],
        "crystals": json.loads(data[5]), "username": data[6], "cases": json.loads(data[7])
    }

# --- ИГРОВАЯ ЛОГИКА ---
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners: return await message.reply("🚫 Вы уже в шахте!")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    
    msg = await message.answer("⛏ <b>Копаем ресурсы...</b>", parse_mode="HTML")
    await asyncio.sleep(random.randint(4, 6))
    
    reward = int(random.randint(250, 550) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    
    cry_msg = ""
    if random.random() < 0.3:
        c_type = random.choice(["Common", "Rare", "SuperRare"])
        p["crystals"][c_type] = p["crystals"].get(c_type, 0) + 1
        db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), user_id), commit=True)
        cry_msg = f"\n✨ Нашли: <b>{CRYSTALS_DATA[c_type]['name']}</b>"

    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, user_id), commit=True)
    active_miners.remove(user_id)
    await msg.edit_text(f"💰 Добыто: <b>{reward}</b> монет.{cry_msg}", parse_mode="HTML")

@dp_main.message(Command("cases"))
async def cmd_cases(message: types.Message):
    p = get_player(message.from_user.id)
    text = "<b>📦 Магазин кейсов:</b>\n\n"
    kb = []
    for cid, info in CASES_DATA.items():
        count = p["cases"].get(cid, 0)
        text += f"▪️ {info['name']} — {info['price']}💰 (У вас: {count})\n"
        kb.append([
            InlineKeyboardButton(text=f"Купить {info['name']}", callback_data=f"bc_{cid}"),
            InlineKeyboardButton(text="Открыть", callback_data=f"oc_{cid}")
        ])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("bc_"))
async def buy_case(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["balance"] >= CASES_DATA[cid]["price"]:
        p["cases"][cid] = p["cases"].get(cid, 0) + 1
        db_query("UPDATE players SET balance = balance - ?, cases = ? WHERE user_id = ?", (CASES_DATA[cid]["price"], json.dumps(p["cases"]), c.from_user.id), commit=True)
        await c.answer("Куплено!")
        await cmd_cases(c.message)
        await c.message.delete()
    else: await c.answer("Мало монет!", show_alert=True)

@dp_main.callback_query(F.data.startswith("oc_"))
async def open_case(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["cases"].get(cid, 0) <= 0: return await c.answer("Нет кейсов!", show_alert=True)
    
    p["cases"][cid] -= 1
    res = random.choice([("money", 5000), ("crystal", "Premium1")]) if cid == "common" else random.choice([("money", 40000), ("crystal", "Premium3")])
    
    if res[0] == "money":
        db_query("UPDATE players SET balance = balance + ?, cases = ? WHERE user_id = ?", (res[1], json.dumps(p["cases"]), c.from_user.id), commit=True)
        win = f"{res[1]}💰"
    else:
        p["crystals"][res[1]] = p["crystals"].get(res[1], 0) + 1
        db_query("UPDATE players SET crystals = ?, cases = ? WHERE user_id = ?", (json.dumps(p["crystals"]), json.dumps(p["cases"]), c.from_user.id), commit=True)
        win = CRYSTALS_DATA[res[1]]["name"]

    await c.message.answer(f"🎁 Выпало: <b>{win}</b>", parse_mode="HTML")
    await cmd_cases(c.message)
    await c.message.delete()

@dp_main.message(Command("shop"))
async def cmd_shop(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    text = f"🛒 <b>Магазин кирок:</b>\nТекущая: {SHOP_PICKS[p['pick_lvl']]['name']}\n\n"
    for lvl, info in SHOP_PICKS.items():
        if lvl > p["pick_lvl"]:
            text += f"{lvl}. {info['name']} — {info['price']}💰\n"
            kb.append([InlineKeyboardButton(text=f"Купить {info['name']}", callback_data=f"bp_{lvl}")])
            break
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("bp_"))
async def buy_pick(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Улучшено до: {SHOP_PICKS[lvl]['name']}")
    else: await c.answer("Мало денег!", show_alert=True)

# --- АДМИНКА ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("🛠 Админ-панель\n/add [код] [награда] [часы]")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        _, code, reward, hours = message.text.split()
        expire = (datetime.now() + timedelta(hours=int(hours))).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT INTO promo_codes VALUES (?, ?, ?)", (code.upper(), int(reward), expire), commit=True)
        await message.answer(f"✅ Код {code.upper()} создан")
    except: await message.answer("Ошибка!")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/mine", description="Копать"),
        BotCommand(command="/cases", description="Кейсы"),
        BotCommand(command="/shop", description="Магазин"),
        BotCommand(command="/balance", description="Баланс")
    ])
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())

