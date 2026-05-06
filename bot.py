import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardRemove

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
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, last_bonus_time TEXT, username TEXT)''')
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

def get_player(user_id, username=None):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus_time FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?)", (user_id, 0, 1, "", None, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus_time": None}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus_time": data[3]}

# --- ЛОГИКА ИГРОВОГО БОТА ---
@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Добро пожаловать в Майнер бот</b>\nВсе функции доступны в меню команд.', 
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>', parse_mode="HTML")
    await asyncio.sleep(wait_time)
    
    reward = random.randint(100, 500)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.edit_text(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Накопал: <b>{reward}</b> монет!', parse_mode="HTML")

@dp_main.message(Command("balance"))
async def balance_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    for i, player in enumerate(top_players, 1):
        username, balance, user_id = player
        name = f"@{username}" if username else f"ID: {user_id}"
        if i == 1: medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2: medal = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3: medal = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        else: medal = f"<b>{i}.</b>"
        text += f"{medal} {name} — <b>{balance}</b> монет\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    reward = 500
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Бонус получен!', parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if not promo:
        await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует!', parse_mode="HTML")
    else:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]:
            await message.reply("❌ Уже использован!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", 
                     (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f'<tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji> Промокод активирован!', parse_mode="HTML")

async def main():
    init_db()
    # Настройка меню (синяя кнопка "Меню")
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/top", description="🏆 Топ"),
        BotCommand(command="/balance", description="💰 Баланс"),
        BotCommand(command="/bonus", description="🎁 Бонус")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
