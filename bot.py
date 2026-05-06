import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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
MEDAL_1_ID = "5440539497383087970" # Золото
MEDAL_2_ID = "5447203607294265305" # Серебро
MEDAL_3_ID = "5453902265922376865" # Бронза

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- ЦЕНЫ И КИРКИ ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, 
                    used_promos TEXT, last_bonus_time TEXT, username TEXT)''')
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
    elif fetchall: res = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id, username=None):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus_time FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?)", (user_id, 0, 1, "", None, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus_time": None}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus_time": data[3]}

# --- КЛАВИАТУРА ---
def main_kb():
    kb = [
        [KeyboardButton(text="⛏ Копать"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="🎁 Бонус")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🎧 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- АДМИН-БОТ ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления промокодами</b>", parse_mode="HTML")

# --- ИГРОВОЙ БОТ ---
@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Добро пожаловать в Майнер бот</b>', 
        reply_markup=main_kb(),
        parse_mode="HTML"
    )

@dp_main.message(F.text == "⛏ Копать")
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id, message.from_user.username)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'⛏ <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    
    for i in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'⛏ <b>Копаем...</b>\n⏳ Осталось: <b>{i}</b> сек.', parse_mode="HTML")
        except: pass
    
    mult = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["mult"]
    reward = int(random.randint(200, 700) * mult)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Ты накопал: <b>{reward}</b> монет!', parse_mode="HTML")

@dp_main.message(F.text == "💰 Баланс")
@dp_main.message(Command("balance"))
async def balance_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Твой баланс: <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp_main.message(F.text == "🏆 Топ")
@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    if not top_players:
        await message.answer("Список игроков пока пуст.")
        return

    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    for i, player in enumerate(top_players, 1):
        username, balance, user_id = player
        display_name = f"@{username}" if username else f"ID: {user_id}"
        
        if i == 1: medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2: medal = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3: medal = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        else: medal = f"<b>{i}.</b>"
            
        text += f"{medal} {display_name} — <b>{balance}</b> монет\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(F.text == "🛒 Магазин")
@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = f'<tg-emoji emoji-id="{SHOP_ICON_ID}">🛒</tg-emoji> <b>Магазин кирок</b>\n\n'
    keyboard = []
    for lvl, info in SHOP_PICKS.items():
        if lvl > p["pick_lvl"]:
            keyboard.append([InlineKeyboardButton(text=f"{info['name']} — {info['price']} 💵", callback_data=f"buy_{lvl}")])
    
    if not keyboard:
        text += "У тебя максимальный уровень!"
    else:
        text += "Выбери улучшение:"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_pick(call: types.CallbackQuery):
    lvl = int(call.data.split("_")[1])
    p = get_player(call.from_user.id)
    pick = SHOP_PICKS[lvl]
    if p["balance"] >= pick["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (pick["price"], lvl, call.from_user.id), commit=True)
        await call.message.edit_text(f"✅ Куплена <b>{pick['name']}</b>!", parse_mode="HTML")
    else:
        await call.answer("❌ Недостаточно монет!", show_alert=True)

@dp_main.message(F.text == "🎁 Бонус")
@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = datetime.now()
    if p["last_bonus_time"]:
        last = datetime.strptime(p["last_bonus_time"], "%Y-%m-%d %H:%M:%S")
        if now < last + timedelta(hours=24):
            rem = (last + timedelta(hours=24)) - now
            await message.reply(f"❌ Бонус через {rem.seconds // 3600}ч.", parse_mode="HTML")
            return
    gift = random.randint(300, 800)
    db_query("UPDATE players SET balance = balance + ?, last_bonus_time = ? WHERE user_id = ?", 
             (gift, now.strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Бонус: <b>{gift}</b> монет!', parse_mode="HTML")

@dp_main.message(F.text == "🎧 Поддержка")
async def support_cmd(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{SUPPORT_ID}">🎧</tg-emoji> Админ: @Ramilpopa_4', parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if not promo:
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует <tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji>', parse_mode="HTML")
    else:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]:
            await message.reply("❌ Уже использован!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply("✅ Активировано!", parse_mode="HTML")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/top", description="🏆 Топ"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
