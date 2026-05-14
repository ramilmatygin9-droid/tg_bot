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

# Медальки для ТОПа
MEDAL_1_ID = "5440539497383087970"
MEDAL_2_ID = "5447203607294265305"
MEDAL_3_ID = "5453902265922376865"

# Кристаллы и цены скупщика
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "id": "6269242583763913842", "rarity": "Обычный", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "id": "6269061400568532047", "rarity": "Редкий", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "id": "6269383548885535501", "rarity": "Сверхредкий", "price": 5000},
    "Premium1": {"name": "Премиум кристалл 1", "id": "6269338864047578738", "rarity": "Премиум", "price": 10000},
    "Premium2": {"name": "Премиум кристалл 2", "id": "626938864047578738", "rarity": "Премиум", "price": 15000},
    "Premium3": {"name": "Premium Crystal 3", "id": "62693886404578738", "rarity": "Премиум", "price": 20000}
}

# --- НАСТРОЙКИ КЕЙСОВ ---
CASES_DATA = {
    "common_box": {
        "name": "📦 Обычный кейс",
        "price": 3500,
        "items": ["Common", "Rare", "SuperRare"],
        "weights": [70, 25, 5] # Шансы в %
    },
    "rare_box": {
        "name": "💎 Редкий кейс",
        "price": 12000,
        "items": ["Rare", "SuperRare", "Premium1"],
        "weights": [60, 30, 10]
    },
    "legendary_box": {
        "name": "🔥 Легендарный кейс",
        "price": 45000,
        "items": ["SuperRare", "Premium1", "Premium2", "Premium3"],
        "weights": [50, 25, 15, 10]
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

# --- АДМИН-БОТ ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления</b>\n\n/add CODE 5000 24\n/del CODE\n/list", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code, reward, hours = args[1].upper(), int(args[2]), int(args[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод {code} создан!")
    except: await message.answer("Ошибка!")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        code = message.text.split()[1].upper()
        db_query("DELETE FROM promo_codes WHERE code = ?", (code,), commit=True)
        await message.answer(f"🗑 Удален: {code}")
    except: pass

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    text = "🎫 Промокоды:\n" + "\n".join([f"• {p[0]} | {p[1]}💰" for p in promos])
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
    start_text = (
        f"<b>─── 〈 <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Добро пожаловать в захватывающий мир добычи!\n\n"
        f"🔹 <b>Твоя задача:</b> Копать руду и находить редкие камни.\n"
        f"🔹 <b>Команды:</b>\n"
        f"⛏ /mine — работа в шахте\n"
        f"📦 /cases — магазин кейсов\n"
        f"🛒 /shop — магазин кирок\n"
        f"💎 /sell — скупщик\n\n"
        f"<i>Удачи в поисках сокровищ!</i>"
    )
    await message.answer(start_text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>Вы уже в шахте!</b>', parse_mode="HTML")
    
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
    
    if random.random() < 0.4:
        rand_val = random.random()
        if rand_val < 0.1: c_key = "SuperRare"
        elif rand_val < 0.3: c_key = "Rare"
        else: c_key = "Common"
            
        crystal = CRYSTALS_DATA[c_key]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), user_id), commit=True)
        crystal_msg = f'\n✨ Вы нашли кристалл: <tg-emoji emoji-id="{crystal["id"]}">💎</tg-emoji> <b>{crystal["name"]}</b>!'

    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, user_id), commit=True)
    active_miners.remove(user_id)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Результат:</b>\n+ {reward} монет{crystal_msg}', parse_mode="HTML")

# --- МАГАЗИН КЕЙСОВ ---
@dp_main.message(Command("cases"))
async def cases_cmd(message: types.Message):
    kb = []
    for cid, data in CASES_DATA.items():
        kb.append([InlineKeyboardButton(text=f"{data['name']} — {data['price']}💰", callback_data=f"buycase_{cid}")])
    
    await message.answer(
        "📦 <b>Магазин Кейсов</b>\n\nОткрывай кейсы, чтобы получить редкие и премиальные кристаллы!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

@dp_main.callback_query(F.data.startswith("buycase_"))
async def buy_case_callback(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    case = CASES_DATA[cid]
    p = get_player(c.from_user.id)
    
    if p["balance"] < case["price"]:
        return await c.answer("🚫 Недостаточно монет для покупки кейса!", show_alert=True)
    
    # Списание баланса
    db_query("UPDATE players SET balance = balance - ? WHERE user_id = ?", (case["price"], c.from_user.id), commit=True)
    
    # Розыгрыш
    win_key = random.choices(case["items"], weights=case["weights"])[0]
    win_item = CRYSTALS_DATA[win_key]
    
    # Выдача приза
    p["crystals"][win_key] = p["crystals"].get(win_key, 0) + 1
    db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), c.from_user.id), commit=True)
    
    await c.message.edit_text(
        f"📦 <b>Открытие кейса: {case['name']}</b>\n"
        f"──────────────────\n"
        f"🎉 Вам выпал: <tg-emoji emoji-id='{win_item['id']}'>💎</tg-emoji> <b>{win_item['name']}</b>!\n"
        f"Редкость: <b>{win_item['rarity']}</b>\n"
        f"Цена продажи: {win_item['price']}💰",
        parse_mode="HTML"
    )

# --- СИСТЕМА СКУПЩИКА ---
@dp_main.message(Command("sell"))
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    for key, data in CRYSTALS_DATA.items():
        count = p["crystals"].get(key, 0)
        if count > 0:
            kb.append([InlineKeyboardButton(text=f"💎 {data['name']} ({count} шт) — {data['price']}💰", callback_data=f"sell_{key}")])
    
    if not kb:
        return await message.answer("У вас нет кристаллов для продажи! ⛏")

    await message.answer("💎 <b>Выберите кристалл для продажи:</b>", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    
    if p["crystals"].get(key, 0) > 0:
        p["crystals"][key] -= 1
        reward = CRYSTALS_DATA[key]["price"]
        db_query("UPDATE players SET balance = balance + ?, crystals = ? WHERE user_id = ?", 
                 (reward, json.dumps(p["crystals"]), c.from_user.id), commit=True)
        
        await c.answer(f"✅ Продано: {CRYSTALS_DATA[key]['name']} (+{reward}💰)")
        # Обновляем сообщение (вызываем sell_cmd логику)
        p_new = get_player(c.from_user.id)
        new_kb = []
        for k, d in CRYSTALS_DATA.items():
            count = p_new["crystals"].get(k, 0)
            if count > 0:
                new_kb.append([InlineKeyboardButton(text=f"💎 {d['name']} ({count} шт) — {d['price']}💰", callback_data=f"sell_{k}")])
        
        if new_kb:
            await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=new_kb))
        else:
            await c.message.edit_text("Вы продали все кристаллы! ⛏")
    else:
        await c.answer("🚫 Кристалл закончился!", show_alert=True)

@dp_main.message(Command("crystals"))
async def crystals_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = "💎 <b>Ваша коллекция:</b>\n\n"
    has_any = False
    for key, count in p["crystals"].items():
        if count > 0:
            has_any = True
            c = CRYSTALS_DATA[key]
            text += f'<tg-emoji emoji-id="{c["id"]}">💎</tg-emoji> {c["name"]}: <b>{count}</b> шт.\n'
    
    if not has_any:
        text = f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>У вас нет кристаллов!</b>'
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = f'<tg-emoji emoji-id="{STAR_TOP_ID}">✨</tg-emoji> <b>Топ богачей:</b>\n\n'
    for i, user in enumerate(top, 1):
        name = f"@{user[0]}" if user[0] else "Игрок"
        icon = {1: MEDAL_1_ID, 2: MEDAL_2_ID, 3: MEDAL_3_ID}.get(i, f"{i}.")
        if i <= 3: icon = f'<tg-emoji emoji-id="{icon}">🏅</tg-emoji>'
        text += f"{icon} <b>{name}</b> — {user[1]}💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    await message.answer(f"🛒 <b>Магазин кирок</b>\nТекущая: {SHOP_PICKS[p['pick_lvl']]['name']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_callback(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        inv = p["inventory"]
        if lvl not in inv: inv.append(lvl)
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ?, inventory = ? WHERE user_id = ?", 
                 (SHOP_PICKS[lvl]["price"], lvl, ",".join(map(str, inv)), c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Недостаточно денег!", show_alert=True)

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b>💰', parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        return await message.answer(f'🚫 Бонус через {rem//3600}ч.')
    db_query("UPDATE players SET balance = balance + 1000, last_bonus = ? WHERE user_id = ?", (now, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> <b>+1000💰 получено!</b>', parse_mode="HTML")

@dp_main.message(Command("promo"))
async def promo_cmd(message: types.Message, command: CommandObject):
    if not command.args: return await message.reply("Введите промокод!")
    code = command.args.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if promo:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]: return await message.reply("Уже использован!")
        p["used_promos"].append(code)
        db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
        await message.reply(f"✅ Активирован! +{promo[0]}💰")
    else: await message.reply("Нет такого кода.")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="Главная"),
        BotCommand(command="/mine", description="Копать"),
        BotCommand(command="/cases", description="Магазин кейсов"),
        BotCommand(command="/sell", description="Скупщик кристаллов"),
        BotCommand(command="/crystals", description="Мои кристаллы"),
        BotCommand(command="/shop", description="Магазин кирок"),
        BotCommand(command="/balance", description="Баланс"),
        BotCommand(command="/top", description="Топ"),
        BotCommand(command="/bonus", description="Бонус"),
        BotCommand(command="/promo", description="Промокод")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())

