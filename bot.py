import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ТОКЕНОВ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk" # Игровой бот
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA" # Админка
OWNER_ID = 8462392581 

# Premium Emoji IDs из ваших файлов
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
SUPPORT_ID = "5924712865763170353"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"  
ERROR_EMOJI_ID = "5240241223632954241" # 🚫
MEDAL_1_ID = "5440539497383087970"    # 🥇
MEDAL_2_ID = "5447203607294265305"    # 🥈
MEDAL_3_ID = "5453902265922376865"    # 🥉
EGGPLANT_ID = "5231264887375633461"   # 🍆

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ (Объединенная) ---
def init_db():
    conn = sqlite3.connect('mega_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, 
                    balance INTEGER DEFAULT 0, 
                    pick_lvl INTEGER DEFAULT 1, 
                    used_promos TEXT DEFAULT "", 
                    last_bonus_time TEXT, 
                    username TEXT,
                    dick_size INTEGER DEFAULT 0,
                    last_dick_grow TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('mega_game.db')
    cur = conn.cursor()
    cur.execute(query, params)
    res = None
    if fetchone: res = cur.fetchone()
    if fetchall: res = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id, username=None):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus_time, dick_size, last_dick_grow FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, username) VALUES (?, ?, ?, ?)", (user_id, 0, 1, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus_time": None, "dick_size": 0, "last_dick_grow": None}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {
        "balance": data[0], "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [],
        "last_bonus_time": data[3], "dick_size": data[4], "last_dick_grow": data[5]
    }

# --- ЛОГИКА АДМИН-БОТА (БЕЗ ИЗМЕНЕНИЙ) ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Админ-панель промокодов</b>\n/add КОД СУММА ЧАСЫ\n/del КОД\n/list", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        _, code, reward, hours = message.text.split()
        expire = "NEVER" if int(hours) == 0 else (datetime.now() + timedelta(hours=int(hours))).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code.upper(), int(reward), expire), commit=True)
        await message.answer(f"✅ Код {code.upper()} создан!")
    except: await message.answer("Ошибка формата!")

# --- ЛОГИКА ИГРОВОГО БОТА (ВСЁ ВМЕСТЕ) ---

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
    await message.answer(f"⛏ <b>Майнер & Дик Бот</b> 🍆\n\nИспользуй меню для игры!", parse_mode="HTML")

# --- СТАРОЕ: МАЙНИНГ ---
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait = random.randint(5, 10)
    status = await message.answer(f"⛏ Копаем... ⏳ {wait} сек.")
    await asyncio.sleep(wait)
    
    mult = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["mult"]
    reward = int(random.randint(200, 700) * mult)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    
    await status.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Добыча: <b>{reward}</b> монет!', parse_mode="HTML")

# --- НОВОЕ: ВЫРАСТИТЬ ---
@dp_main.message(Command("dick"))
async def grow_dick(message: types.Message):
    user_id = message.from_user.id
    p = get_player(user_id, message.from_user.username)
    now = datetime.now()
    
    if p["last_dick_grow"]:
        last = datetime.strptime(p["last_dick_grow"], "%Y-%m-%d %H:%M:%S")
        if now < last + timedelta(hours=24):
            rem = (last + timedelta(hours=24)) - now
            await message.reply(f"❌ Жди еще {rem.seconds // 3600}ч. {(rem.seconds // 60) % 60}мин.")
            return

    growth = random.randint(1, 10)
    new_size = p["dick_size"] + growth
    db_query("UPDATE players SET dick_size = ?, last_dick_grow = ? WHERE user_id = ?", (new_size, now.strftime("%Y-%m-%d %H:%M:%S"), user_id), commit=True)
    
    await message.answer(f"<tg-emoji emoji-id='{EGGPLANT_ID}'>🍆</tg-emoji> Вырос на <b>{growth} см</b>! Итого: <b>{new_size} см</b>", parse_mode="HTML")

# --- СТАРОЕ: ПОДАРОК (24ч) ---
@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = datetime.now()
    if p["last_bonus_time"]:
        last = datetime.strptime(p["last_bonus_time"], "%Y-%m-%d %H:%M:%S")
        if now < last + timedelta(hours=24):
            await message.reply("❌ Подарок можно брать раз в 24 часа!")
            return
    
    gift = random.randint(100, 500)
    db_query("UPDATE players SET balance = balance + ?, last_bonus_time = ? WHERE user_id = ?", (gift, now.strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id), commit=True)
    await message.answer(f"🎁 Вы получили <b>{gift}</b> монет!", parse_mode="HTML")

# --- ОБНОВЛЕННЫЕ ТОПЫ (С МЕДАЛЯМИ) ---
@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    for i, row in enumerate(top_players, 1):
        medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>' if i==1 else f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>' if i==2 else f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>' if i==3 else f"<b>{i}.</b>"
        text += f"{medal} @{row[0] or row[2]} — <b>{row[1]}</b> 💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("top_dick"))
async def top_dick_cmd(message: types.Message):
    top_dicks = db_query("SELECT username, dick_size, user_id FROM players ORDER BY dick_size DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ Гигантов 🍆:</b>\n\n"
    for i, row in enumerate(top_dicks, 1):
        medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>' if i==1 else f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>' if i==2 else f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>' if i==3 else f"<b>{i}.</b>"
        text += f"{medal} @{row[0] or row[2]} — <b>{row[1]} см</b>\n"
    await message.answer(text, parse_mode="HTML")

# --- ОБРАБОТКА ПРОМОКОДОВ ---
@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if not promo:
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует или срок действия истек <tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji>', parse_mode="HTML")
    else:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]:
            await message.reply("❌ Уже использовано!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ Активировано! +{promo[0]} 💰")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/dick", description="🍆 Вырастить (24ч)"),
        BotCommand(command="/bonus", description="🎁 Подарок"),
        BotCommand(command="/top", description="🏆 Топ богатства"),
        BotCommand(command="/top_dick", description="🏆 Топ гигантов"),
        BotCommand(command="/shop", description="🛒 Магазин"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
