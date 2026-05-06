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
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA"
OWNER_ID = 8462392581 

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
SUPPORT_ID = "5924712865763170353"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"  
ERROR_EMOJI_ID = "5240241223632954241"

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    # Добавлена колонка last_bonus_time
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, last_bonus_time TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute(query, params)
    res = None
    if fetchone: res = cur.fetchone()
    if fetchall: res = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus_time FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, ?, ?, ?, ?)", (user_id, 0, 1, "", None), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus_time": None}
    return {
        "balance": data[0], 
        "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [],
        "last_bonus_time": data[3]
    }

# --- ЛОГИКА АДМИН-БОТА ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления промокодами</b>", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        parts = message.text.split()
        code, reward, hours = parts[1].upper(), int(parts[2]), int(parts[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Код <b>{code}</b> создан!", parse_mode="HTML")
    except: await message.answer("Ошибка!")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    db_query("DELETE FROM promo_codes WHERE code = ?", (message.text.split()[1].upper(),), commit=True)
    await message.answer("🗑 Удалено.")

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    await message.answer("\n".join([f"{p[0]} - {p[1]}" for p in promos]) if promos else "Пусто.")

# --- ЛОГИКА ИГРОВОГО БОТА ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать!</b>', parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'⛏ Копаем... ⏳ {wait_time} сек.')
    await asyncio.sleep(wait_time)
    
    mult = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["mult"]
    reward = int(random.randint(200, 700) * mult)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    await message.answer(f'💰 Найдено: {reward}')

# --- ОБНОВЛЕННАЯ ЛОГИКА ПОДАРКА (24 ЧАСА) ---
@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = datetime.now()
    
    if p["last_bonus_time"]:
        last_time = datetime.strptime(p["last_bonus_time"], "%Y-%m-%d %H:%M:%S")
        next_time = last_time + timedelta(hours=24)
        
        if now < next_time:
            remaining = next_time - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.reply(
                f'❌ <b>Подарок уже получен!</b>\n'
                f'Следующий можно забрать через: <b>{hours:02d}:{minutes:02d}:{seconds:02d}</b>',
                parse_mode="HTML"
            )
            return

    gift_amount = random.randint(10, 500)
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    db_query("UPDATE players SET balance = balance + ?, last_bonus_time = ? WHERE user_id = ?", 
             (gift_amount, current_time_str, message.from_user.id), commit=True)
    
    text = (f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> <b>Подарок получен!</b>\n\n'
            f'Вы получили: <b>{gift_amount}</b> монет!')
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    current_pick = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["name"]
    text = f'⛏ Магазин. Ваша кирка: {current_pick}'
    keyboard = [[InlineKeyboardButton(text="🎫 Ввести промокод", callback_data="open_promo")]]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp_main.callback_query(F.data == "open_promo")
async def open_promo_cb(callback: types.CallbackQuery):
    await callback.message.answer('📝 Введите промокод:')
    await callback.answer()

@dp_main.message(Command("balance"))
async def balance_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'💰 Баланс: {p["balance"]}')

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if promo:
        reward, expire = promo
        p = get_player(message.from_user.id)
        if expire != "NEVER" and datetime.now() > datetime.strptime(expire, "%Y-%m-%d %H:%M:%S"):
            await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод истек!')
        elif code in p["used_promos"]:
            await message.reply("❌ Уже использовано!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", 
                     (reward, ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ Активировано! +{reward}")
    else:
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует!')

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Главное меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/bonus", description="🎁 Подарок"),
        BotCommand(command="/shop", description="🛒 Магазин"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
