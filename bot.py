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

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
INVENTORY_ID = "5431445210141852444"
ERROR_EMOJI_ID = "5240241223632954241" 
NOTEBOOK_ID = "5461019131329402505"    
CHECK_MARK_ID = "5316939641503365999"

# Медальки для ТОПа
MEDAL_1_ID = "5440539497383087970"
MEDAL_2_ID = "5447203607294265305"
MEDAL_3_ID = "5453902265922376865"

# Кристаллы и цены скупщика (включая премиум из скриншотов)
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "id": "6269242583763913842", "rarity": "Обычный", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "id": "6269061400568532047", "rarity": "Редкий", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "id": "6269383548885535501", "rarity": "Сверхредкий", "price": 5000},
    "Premium1": {"name": "Премиум кристалл 1", "id": "6269338864047578738", "rarity": "Премиум", "price": 10000},
    "Premium2": {"name": "Премиум кристалл 2", "id": "626938864047578738", "rarity": "Премиум", "price": 15000},
    "Premium3": {"name": "Премиум кристалл 3", "id": "62693886404578738", "rarity": "Премиум", "price": 20000}
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
                    crystals TEXT DEFAULT '{}')''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    cur.execute("PRAGMA table_info(players)")
    cols = [c[1] for c in cur.fetchall()]
    if 'crystals' not in cols:
        cur.execute("ALTER TABLE players ADD COLUMN crystals TEXT DEFAULT '{}'")
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, inventory, crystals, username FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, inventory, crystals) VALUES (?, 0, 1, '', ?, '1', '{}')", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "inventory": [1], "crystals": {}, "username": username}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {
        "balance": data[0], 
        "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3],
        "inventory": [int(x) for x in data[4].split(",")] if data[4] else [1],
        "crystals": json.loads(data[5] if data[5] else "{}"),
        "username": data[6]
    }

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
    start_text = (
        f"<b>─── 〈 <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Добро пожаловать в захватывающий мир добычи!\n\n"
        f"🔹 <b>Твоя задача:</b> Копать руду и находить редкие камни.\n"
        f"🔹 <b>Команда:</b> /mine — начать работу в шахте.\n"
        f"🔹 <b>Улучшения:</b> /shop — покупай крутые кирки.\n\n"
        f"<i>Удачи в поисках сокровищ!</i>"
    )
    await message.answer(start_text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>Вы уже находитесь в шахте!</b>', parse_mode="HTML")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Начинаем копать...</b>', parse_mode="HTML")
    
    for s in range(wait_time, 0, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работаем в шахте...</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: pass
        
    reward = int(random.randint(200, 600) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    crystal_msg = ""
    
    # Шанс выпадения кристаллов (включая премиум)
    if random.random() < 0.4:
        rand_val = random.random()
        if rand_val < 0.02: c_key = "Premium3"
        elif rand_val < 0.05: c_key = "Premium2"
        elif rand_val < 0.1: c_key = "Premium1"
        elif rand_val < 0.2: c_key = "SuperRare"
        elif rand_val < 0.4: c_key = "Rare"
        else: c_key = "Common"
            
        crystal = CRYSTALS_DATA[c_key]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), user_id), commit=True)
        crystal_msg = f'\n✨ Вы нашли кристалл: <tg-emoji emoji-id="{crystal["id"]}">💎</tg-emoji> <b>{crystal["name"]}</b>!'

    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, user_id), commit=True)
    active_miners.remove(user_id)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Результат:</b>\n+ {reward} монет{crystal_msg}', parse_mode="HTML")

@dp_main.message(Command("sell"))
async def sell_menu(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    for key, c in CRYSTALS_DATA.items():
        count = p["crystals"].get(key, 0)
        kb.append([InlineKeyboardButton(text=f"💎 {c['name']} ({count} шт) — {c['price']}💰", callback_data=f"sell_{key}")])
    
    await message.answer("💎 <b>выбери нужный Кристал для продажи</b> 💎", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    user_id = c.from_user.id
    p = get_player(user_id)
    
    if p["crystals"].get(key, 0) > 0:
        crystal = CRYSTALS_DATA[key]
        p["crystals"][key] -= 1
        reward = crystal["price"]
        
        db_query("UPDATE players SET balance = balance + ?, crystals = ? WHERE user_id = ?", 
                 (reward, json.dumps(p["crystals"]), user_id), commit=True)
        
        kb = []
        for k, info in CRYSTALS_DATA.items():
            count = p["crystals"].get(k, 0)
            kb.append([InlineKeyboardButton(text=f"💎 {info['name']} ({count} шт) — {info['price']}💰", callback_data=f"sell_{k}")])
        
        await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await c.answer(f"✅ Продано за {reward}💰", show_alert=False)
    else:
        await c.answer("🚫 У вас нет этого кристалла!", show_alert=True)

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ богачей:</b>\n\n"
    for i, user in enumerate(top, 1):
        display_name = f"@{user[0]}" if user[0] else "Игрок"
        if i == 1: prefix = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2: prefix = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3: prefix = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        else: prefix = f"{i}."
        text += f"{prefix} <b>{display_name}</b> — {user[1]}💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b>', parse_mode="HTML")

@dp_main.message(Command("crystals"))
async def crystals_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = "💎 <b>Ваша коллекция кристаллов:</b>\n\n"
    has_any = False
    for key, count in p["crystals"].items():
        if count > 0:
            c = CRYSTALS_DATA[key]
            text += f'<tg-emoji emoji-id="{c["id"]}">💎</tg-emoji> {c["name"]}: <b>{count}</b> шт.\n'
            has_any = True
    if not has_any: text = f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>У вас пока нет кристаллов!</b>'
    await message.answer(text, parse_mode="HTML")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="Главная"),
        BotCommand(command="/mine", description="Копать"),
        BotCommand(command="/sell", description="Скупщик кристаллов"),
        BotCommand(command="/balance", description="Баланс"),
        BotCommand(command="/crystals", description="Мои кристаллы"),
        BotCommand(command="/top", description="Топ")
    ], scope=BotCommandScopeDefault())
    await dp_main.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
