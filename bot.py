import asyncio
import random
import sqlite3
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
GAME_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk" # Токен для ИГРЫ
PROMO_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" # Токен для ПРОМО
OWNER_ID = 8462392581 

# Эмодзи ID (Премиум)
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
GIFT_ID = "5792071541084659564"       
SKUPSHIK_ID = "5452136652111620778"   
DIAMOND_COMMON = "6269061400568532047"  
DIAMOND_UNCOMMON = "626938354888535501" 
DIAMOND_RARE = "6269242583763913842"     
CUP_GOLD = "5318821943825154339"
CUP_SILVER = "5318991475512453472"
CUP_BRONZE = "5319114256245863261"

SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 25000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 100000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 500000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 2000000, "mult": 10.0}
}

# --- БАЗА ДАННЫХ (Общая для обоих ботов) ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, 
                   used_promos TEXT, username TEXT, last_bonus INTEGER DEFAULT 0,
                   count_common INTEGER DEFAULT 0, count_uncommon INTEGER DEFAULT 0, count_rare INTEGER DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promocodes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_time INTEGER)''')
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, count_common, count_uncommon, count_rare FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, last_bonus) VALUES (?, 0, 1, '', ?, 0)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "common": 0, "uncommon": 0, "rare": 0}
    if username: db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus": data[3], "common": data[4], "uncommon": data[5], "rare": data[6]}

# --- ДИСПЕТЧЕРЫ ---
dp_game = Dispatcher()
dp_promo = Dispatcher()

# --- ЛОГИКА БОТА ПРОМОКОДОВ (PROMO_TOKEN) ---

@dp_promo.message(Command("start"))
async def promo_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("👑 <b>Панель управления промокодами</b>\n\n• /add КОД СУММА ЧАСЫ\n• /del КОД\n• /list - Список", parse_mode="HTML")

@dp_promo.message(Command("add"))
async def admin_add(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID: return
    args = command.args.split() if command.args else []
    if len(args) < 3: return await message.answer("• /add КОД СУММА ЧАСЫ")
    code, reward, hours = args[0].upper(), int(args[1]), int(args[2])
    expire = 0 if hours == 0 else int(time.time()) + (hours * 3600)
    db_query("INSERT OR REPLACE INTO promocodes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
    await message.answer(f"✅ Код <code>{code}</code> на {reward}💰 создан!", parse_mode="HTML")

@dp_promo.message(Command("del"))
async def admin_del(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID: return
    if not command.args: return
    db_query("DELETE FROM promocodes WHERE code = ?", (command.args.upper(),), commit=True)
    await message.answer(f"❌ Код {command.args.upper()} удален.")

@dp_promo.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    codes = db_query("SELECT code, reward, expire_time FROM promocodes", fetchall=True)
    res = "📜 <b>Активные коды:</b>\n"
    for c, r, e in codes:
        t = "бесконечный" if e == 0 else datetime.fromtimestamp(e).strftime('%d.%m %H:%M')
        res += f"• <code>{c}</code> | {r}💰 | До: {t}\n"
    await message.answer(res or "Кодов нет.", parse_mode="HTML")

# --- ЛОГИКА ИГРОВОГО БОТА (GAME_TOKEN) ---

@dp_game.message(Command("start"))
async def cmd_start(message: types.Message):
    p = get_player(message.from_user.id, message.from_user.username)
    pick = SHOP_PICKS[p["pick_lvl"]]
    welcome = (
        f"<b><tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER SIMULATOR</b>\n\n"
        f"👋 Привет, <b>@{message.from_user.username or 'Игрок'}</b>!\n"
        f"⚙️ Кирка: <code>{pick['name']}</code> (x{pick['mult']})\n"
        f"💰 Баланс: <b>{p['balance']:,}</b>\n\n"
        f"⛏ /mine — копать\n🎒 /inventory — инвентарь\n🛒 /shop — магазин"
    )
    await message.answer(welcome, parse_mode="HTML")

@dp_game.message(Command("mine"))
async def cmd_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait = random.randint(5, 10)
    status = await message.answer(f"⛏ <b>Копаем...</b> (⏳ {wait}с)", parse_mode="HTML")
    await asyncio.sleep(wait)
    
    luck = random.random()
    dia = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        dia = f"\n<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> <b>Редкий алмаз!</b>"
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        dia = f"\n<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> <b>Полуредкий алмаз!</b>"

    rew = int(random.randint(200, 600) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (rew, message.from_user.id), commit=True)
    await status.delete()
    await message.answer(f"💰 +<b>{rew}</b> монет{dia}", parse_mode="HTML")

@dp_game.message(Command("inventory"))
async def cmd_inv(message: types.Message):
    p = get_player(message.from_user.id)
    text = (f"🎒 <b>Инвентарь:</b>\n\n"
            f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Об: <b>{p['common']}</b>\n"
            f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Ред: <b>{p['uncommon']}</b>\n"
            f"<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Эпик: <b>{p['rare']}</b>")
    await message.answer(text, parse_mode="HTML")

@dp_game.message(Command("top"))
async def cmd_top(message: types.Message):
    top = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    res = "🏆 <b>ТОП МАЙНЕРОВ:</b>\n\n"
    for i, (name, bal) in enumerate(top, 1):
        pref = {1: f"<tg-emoji emoji-id='{CUP_GOLD}'>🥇</tg-emoji>", 
                2: f"<tg-emoji emoji-id='{CUP_SILVER}'>🥈</tg-emoji>", 
                3: f"<tg-emoji emoji-id='{CUP_BRONZE}'>🥉</tg-emoji>"}.get(i, f"<b>{i}.</b>")
        res += f"{pref} @{name or 'Anon'} — 💰 <code>{bal:,}</code>\n"
    await message.answer(res, parse_mode="HTML")

@dp_game.message(Command("promo"))
async def cmd_promo(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Введи /promo КОД")
    code = command.args.upper()
    p = get_player(message.from_user.id)
    if code in p["used_promos"]: return await message.answer("❌ Уже использован!")
    
    data = db_query("SELECT reward, expire_time FROM promocodes WHERE code = ?", (code,), fetchone=True)
    if not data or (data[1] != 0 and time.time() > data[1]):
        return await message.answer("❌ Код неверный или истек!")
    
    new_used = ",".join(p["used_promos"] + [code])
    db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (data[0], new_used, message.from_user.id), commit=True)
    await message.answer(f"✅ Начислено {data[0]} монет!")

@dp_game.message(Command("shop"))
async def cmd_shop(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} | {v['price']:,}💰", callback_data=f"buy_{k}")] 
          for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    await message.answer("🛒 <b>Магазин кирок:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb or [[InlineKeyboardButton(text="Макс. уровень!", callback_data="none")]]), parse_mode="HTML")

@dp_game.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Мало монет!", show_alert=True)

# --- ЗАПУСК ---
async def start_all():
    init_db()
    game_bot = Bot(token=GAME_TOKEN)
    promo_bot = Bot(token=PROMO_TOKEN)
    
    # Регистрация команд для подсказок в меню
    await game_bot.set_my_commands([
        BotCommand(command="start", description="Дом"),
        BotCommand(command="mine", description="Копать"),
        BotCommand(command="top", description="Топ"),
        BotCommand(command="inventory", description="Инвентарь"),
        BotCommand(command="shop", description="Магазин"),
        BotCommand(command="promo", description="Промокод")
    ])
    
    print("Бот Игры и Бот Промокодов запущены!")
    await asyncio.gather(
        dp_game.start_polling(game_bot),
        dp_promo.start_polling(promo_bot)
    )

if __name__ == "__main__":
    asyncio.run(start_all())

