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

# Premium Emoji IDs из твоих скриншотов
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
SUPPORT_ID = "5924712865763170353"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"  
ERROR_EMOJI_ID = "5240241223632954241"
# Новые медали для Топа
MEDAL_1_ID = "5440539497383087970" # Золото
MEDAL_2_ID = "5447203607294265305" # Серебро
MEDAL_3_ID = "5453902265922376865" # Бронза

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
    if username: # Обновляем username при каждом входе
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
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

# ... (остальные команды админа /add, /del, /list остаются прежними)

# --- ЛОГИКА ИГРОВОГО БОТА ---
@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Добро пожаловать в Майнер бот</b>', parse_mode="HTML")

# --- КОМАНДА ТОП ИГРОКОВ ---
@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    # Получаем топ 10 игроков по балансу
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    
    if not top_players:
        await message.answer("Список игроков пока пуст.")
        return

    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    
    for i, player in enumerate(top_players, 1):
        username, balance, user_id = player
        display_name = f"@{username}" if username else f"ID: {user_id}"
        
        # Назначаем медали для первых трех мест
        if i == 1:
            medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2:
            medal = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3:
            medal = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        else:
            medal = f"<b>{i}.</b>"
            
        text += f"{medal} {display_name} — <b>{balance}</b> монет\n"

    await message.answer(text, parse_mode="HTML")

# --- ОСТАЛЬНЫЕ КОМАНДЫ ---
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id, message.from_user.username)
    # ... логика копания ...
    await message.answer("⛏ Добыча завершена!")

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id, message.from_user.username)
    # ... логика подарка (24 часа) ...
    await message.answer(f"🎁 Подарок забран!")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if not promo:
        # Текст и эмодзи из image.png
        await message.reply(
            f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует или срок действия истек <tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji>',
            parse_mode="HTML"
        )
    else:
        # ... логика успешной активации ...
        await message.reply("✅ Активировано!")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/top", description="🏆 Топ игроков"), # Добавили в меню
        BotCommand(command="/bonus", description="🎁 Подарок"),
        BotCommand(command="/shop", description="🛒 Магазин"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
