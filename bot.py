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

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA"
OWNER_ID = 8462392581 

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
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
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, username TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
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
    data = db_query("SELECT balance, pick_lvl, used_promos FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, 0, 1, '', ?)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": []}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else []}

# --- ИГРОВАЯ ЛОГИКА ---

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b><tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji>\n\n'
        f'Используй /mine или меню чтобы начать копать руду',
        reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
    )

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', 
        parse_mode="HTML"
    )
    
    for seconds_left in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(
                f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{seconds_left}</b> сек.',
                parse_mode="HTML"
            )
        except: pass
    
    reward = random.randint(200, 700)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Успешная добыча!</b>\n'
        f'━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji> Найдено: <b>{reward}</b> монет',
        parse_mode="HTML"
    )

@dp_main.message(Command("top"))
async def top_cmd(message: types.Message):
    top_players = db_query("SELECT username, balance, user_id FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "<b>🏆 Топ 10 Майнеров:</b>\n\n"
    for i, player in enumerate(top_players, 1):
        name = f"@{player[0]}" if player[0] else f"ID: {player[2]}"
        medal = {1: f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>', 
                 2: f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>', 
                 3: f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'}.get(i, f"<b>{i}.</b>")
        text += f"{medal} {name} — <b>{player[1]}</b> монет\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    gift = random.randint(10, 500)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (gift, message.from_user.id), commit=True)
    await message.answer(
        f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> <b>вам доступен подарок заберите</b> <tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji>\n\n'
        f'Вы получили: <b>{gift}</b> монет!', parse_mode="HTML"
    )

@dp_main.message(Command("balance"))
async def balance_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> <b>Ваш баланс:</b>\n💰 <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    if promo:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]:
            await message.reply("❌ Вы уже использовали этот промокод!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", 
                     (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ <b>Активировано!</b>\nВы получили <b>{promo[0]}</b> монет!", parse_mode="HTML")

# --- ЗАПУСК ---
async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Главное меню"),
        BotCommand(command="/mine", description="⛏ Копать руду"),
        BotCommand(command="/top", description="🏆 Топ игроков"),
        BotCommand(command="/bonus", description="🎁 Забрать подарок"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
