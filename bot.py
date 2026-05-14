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
STAR_TOP_ID = "5472256585323522641"
CASE_EMOJI_ID = "5215535352319602416" # Эмодзи кейса

# Медальки для ТОПа
MEDAL_1_ID = "5440539497383087970"
MEDAL_2_ID = "5447203607294265305"
MEDAL_3_ID = "5453902265922376865"

# Кристаллы
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "id": "6269242583763913842", "rarity": "Обычный", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "id": "6269061400568532047", "rarity": "Редкий", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "id": "6269383548885535501", "rarity": "Сверхредкий", "price": 5000},
    "Premium1": {"name": "Премиум кристалл 1", "id": "6269338864047578738", "rarity": "Премиум", "price": 10000},
    "Premium2": {"name": "Премиум кристалл 2", "id": "626938864047578738", "rarity": "Премиум", "price": 15000},
    "Premium3": {"name": "Premium Crystal 3", "id": "62693886404578738", "rarity": "Премиум", "price": 20000}
}

# --- КЕЙСЫ ---
CASES_DATA = {
    "common_case": {
        "name": "Обычный кейс",
        "price": 5000,
        "items": [
            {"type": "money", "min": 1000, "max": 4000, "chance": 0.6},
            {"type": "crystal", "key": "Common", "chance": 0.3},
            {"type": "crystal", "key": "Rare", "chance": 0.1}
        ]
    },
    "mythic_case": {
        "name": "Мифический кейс",
        "price": 25000,
        "items": [
            {"type": "money", "min": 10000, "max": 50000, "chance": 0.4},
            {"type": "crystal", "key": "SuperRare", "chance": 0.3},
            {"type": "crystal", "key": "Premium1", "chance": 0.2},
            {"type": "crystal", "key": "Premium2", "chance": 0.1}
        ]
    }
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
    if 'crystals' not in cols:
        cur.execute("ALTER TABLE players ADD COLUMN crystals TEXT DEFAULT '{}'")
    if 'cases' not in cols:
        cur.execute("ALTER TABLE players ADD COLUMN cases TEXT DEFAULT '{}'")
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
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {
        "balance": data[0], 
        "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3],
        "inventory": [int(x) for x in data[4].split(",")] if data[4] else [1],
        "crystals": json.loads(data[5] if data[5] else "{}"),
        "username": data[6],
        "cases": json.loads(data[7] if data[7] else "{}")
    }

# --- МАГАЗИН КИРОК ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

# --- КОМАНДЫ ИГРОВОГО БОТА ---

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    start_text = (
        f"<b>─── 〈 <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Добро пожаловать в мир добычи!\n\n"
        f"🔹 <b>Команда:</b> /mine — копать руду.\n"
        f"🔹 <b>Кейсы:</b> /cases — испытать удачу.\n"
        f"🔹 <b>Скупщик:</b> /sell — продать камни.\n"
        f"🔹 <b>Улучшения:</b> /shop — купить кирку.\n"
    )
    await message.answer(start_text, parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>Вы уже в шахте!</b>', parse_mode="HTML")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>', parse_mode="HTML")
    
    await asyncio.sleep(wait_time)
        
    reward = int(random.randint(200, 600) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    crystal_msg = ""
    
    if random.random() < 0.35:
        c_key = random.choices(["Common", "Rare", "SuperRare"], weights=[0.7, 0.25, 0.05])[0]
        crystal = CRYSTALS_DATA[c_key]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), user_id), commit=True)
        crystal_msg = f'\n✨ Найден: <tg-emoji emoji-id="{crystal["id"]}">💎</tg-emoji> <b>{crystal["name"]}</b>!'

    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, user_id), commit=True)
    active_miners.remove(user_id)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>+ {reward} монет</b>{crystal_msg}', parse_mode="HTML")

# --- СИСТЕМА КЕЙСОВ ---
@dp_main.message(Command("cases"))
async def cases_menu(message: types.Message):
    p = get_player(message.from_user.id)
    text = f'<tg-emoji emoji-id="{CASE_EMOJI_ID}">📦</tg-emoji> <b>Магазин Кейсов</b>\n\n'
    kb = []
    
    for c_id, c_info in CASES_DATA.items():
        count = p["cases"].get(c_id, 0)
        text += f"▪️ <b>{c_info['name']}</b>\nЦена: {c_info['price']}💰 | У вас: {count} шт.\n\n"
        kb.append([
            InlineKeyboardButton(text=f"Купить {c_info['name']}", callback_data=f"buycase_{c_id}"),
            InlineKeyboardButton(text=f"Открыть", callback_data=f"opencase_{c_id}")
        ])
    
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buycase_"))
async def buy_case(c: types.CallbackQuery):
    case_id = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    case_info = CASES_DATA[case_id]
    
    if p["balance"] >= case_info["price"]:
        p["cases"][case_id] = p["cases"].get(case_id, 0) + 1
        db_query("UPDATE players SET balance = balance - ?, cases = ? WHERE user_id = ?", 
                 (case_info["price"], json.dumps(p["cases"]), c.from_user.id), commit=True)
        await c.answer(f"✅ Куплен {case_info['name']}!")
        await cases_menu(c.message)
    else:
        await c.answer("❌ Недостаточно средств!", show_alert=True)

@dp_main.callback_query(F.data.startswith("opencase_"))
async def open_case(c: types.CallbackQuery):
    case_id = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    
    if p["cases"].get(case_id, 0) <= 0:
        return await c.answer("❌ У вас нет таких кейсов!", show_alert=True)
    
    p["cases"][case_id] -= 1
    case_info = CASES_DATA[case_id]
    
    # Розыгрыш
    item = random.choices(case_info["items"], weights=[i["chance"] for i in case_info["items"]])[0]
    
    result_text = ""
    if item["type"] == "money":
        win = random.randint(item["min"], item["max"])
        db_query("UPDATE players SET balance = balance + ?, cases = ? WHERE user_id = ?", 
                 (win, json.dumps(p["cases"]), c.from_user.id), commit=True)
        result_text = f"💰 Вы выиграли {win} монет!"
    else:
        c_key = item["key"]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        db_query("UPDATE players SET crystals = ?, cases = ? WHERE user_id = ?", 
                 (json.dumps(p["crystals"]), json.dumps(p["cases"]), c.from_user.id), commit=True)
        result_text = f"💎 Выпал кристалл: {CRYSTALS_DATA[c_key]['name']}!"
    
    await c.message.answer(f"🎰 <b>Открытие {case_info['name']}...</b>\n\n{result_text}", parse_mode="HTML")
    await c.answer()
    await cases_menu(c.message)

# --- ОСТАЛЬНЫЕ КОМАНДЫ (БЕЗ ИЗМЕНЕНИЙ) ---

@dp_main.message(Command("sell"))
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    for key, data in CRYSTALS_DATA.items():
        count = p["crystals"].get(key, 0)
        if count > 0:
            kb.append([InlineKeyboardButton(text=f"💎 {data['name']} ({count} шт) — {data['price']}💰", callback_data=f"sell_{key}")])
    
    if not kb:
        return await message.answer("У вас нет камней на продажу.")
    await message.answer("💎 <b>Выберите кристалл для продажи:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["crystals"].get(key, 0) > 0:
        p["crystals"][key] -= 1
        reward = CRYSTALS_DATA[key]["price"]
        db_query("UPDATE players SET balance = balance + ?, crystals = ? WHERE user_id = ?", (reward, json.dumps(p["crystals"]), c.from_user.id), commit=True)
        await c.answer(f"✅ Продано за {reward}💰")
        await sell_cmd(c.message) # Обновить список
    else:
        await c.answer("Нет в наличии!")

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b>', parse_mode="HTML")

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = f'<tg-emoji emoji-id="{STAR_TOP_ID}">✨</tg-emoji> <b>Топ богачей:</b>\n\n'
    for i, user in enumerate(top, 1):
        prefix = f"{i}."
        if i == 1: prefix = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        text += f"{prefix} <b>{user[0] or 'Игрок'}</b> — {user[1]}💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    await message.answer(f"🛒 <b>Магазин</b>\nТекущая кирка: {SHOP_PICKS[p['pick_lvl']]['name']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_callback(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        inv = p["inventory"]
        if lvl not in inv: inv.append(lvl)
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ?, inventory = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, ",".join(map(str, inv)), c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Вы купили: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Недостаточно денег!", show_alert=True)

# --- АДМИН ПАНЕЛЬ ---
@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code, reward, hours = args[1].upper(), int(args[2]), int(args[3])
        expire = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод {code} создан!")
    except: await message.answer("Ошибка! /add CODE REWARD HOURS")

@dp_main.message(Command("promo"))
async def promo_cmd(message: types.Message, command: CommandObject):
    if not command.args: return await message.reply("Введите код!")
    code = command.args.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if promo:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]: return await message.reply("Уже использован!")
        p["used_promos"].append(code)
        db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
        await message.reply(f"✅ Активировано! +{promo[0]}💰")
    else: await message.reply("Код не найден!")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="Главная"),
        BotCommand(command="/mine", description="Копать"),
        BotCommand(command="/cases", description="Кейсы"),
        BotCommand(command="/sell", description="Скупщик"),
        BotCommand(command="/shop", description="Магазин"),
        BotCommand(command="/balance", description="Баланс"),
        BotCommand(command="/top", description="Топ"),
        BotCommand(command="/promo", description="Промокод")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())

