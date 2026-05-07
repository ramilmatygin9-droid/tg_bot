import asyncio
import logging
import random
import sqlite3
import time
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# Эмодзи и Кастомные ID (из твоих скриншотов)
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
SKUPSHIK_ID = "5452136652111620778"   # 🤓

# Алмазы (ID из JSON дампов)
DIAMOND_COMMON = "6269061400568532047"  
DIAMOND_UNCOMMON = "626938354888535501" 
DIAMOND_RARE = "6269242583763913842"     

# ЦЕНЫ НА КИРКИ
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 25000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 100000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 500000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 2000000, "mult": 10.0}
}

main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, 
                   balance INTEGER, 
                   pick_lvl INTEGER, 
                   used_promos TEXT, 
                   username TEXT, 
                   last_bonus INTEGER DEFAULT 0,
                   count_common INTEGER DEFAULT 0,
                   count_uncommon INTEGER DEFAULT 0,
                   count_rare INTEGER DEFAULT 0)''')
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, count_common, count_uncommon, count_rare FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, last_bonus) VALUES (?, 0, 1, '', ?, 0)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "common": 0, "uncommon": 0, "rare": 0}
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {
        "balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3], "common": data[4], "uncommon": data[5], "rare": data[6]
    }

# --- МЕНЮ ---
@dp_main.message(Command("start"), Command("menu"))
async def main_menu(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    kb = [
        [InlineKeyboardButton(text="⛏ Начать копать", callback_data="mine_action")],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv_action"),
            InlineKeyboardButton(text="🤓 Скупщик", callback_data="sell_action")
        ],
        [
            InlineKeyboardButton(text="🛒 Магазин", callback_data="shop_action"),
            InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus_action")
        ],
        [InlineKeyboardButton(text="💳 Баланс", callback_data="bal_action")]
    ]
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Главное меню Майнера</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# --- ЛОГИКА КОПАНИЯ (СТАРЫЙ ТЕКСТ) ---
@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.chat.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    
    # Старая анимация
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except:
            pass
    
    luck = random.random()
    diamond_text = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.chat.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_RARE}">💎</tg-emoji> <b>В инвентарь добавлен: Редкий алмаз!</b>'
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.chat.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_UNCOMMON}">💎</tg-emoji> <b>В инвентарь добавлен: Полуредкий алмаз!</b>'
    elif luck < 0.40:
        db_query("UPDATE players SET count_common = count_common + 1 WHERE user_id = ?", (message.chat.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_COMMON}">💎</tg-emoji> <b>В инвентарь добавлен: Обычный алмаз!</b>'

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.chat.id), commit=True)
    
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Добыто: <b>{reward}</b> монет{diamond_text}', parse_mode="HTML")

# --- ИНВЕНТАРЬ И ПРОДАЖА ---
@dp_main.message(Command("inv"))
async def inventory_cmd(message: types.Message):
    p = get_player(message.chat.id)
    text = (f"🎒 <b>Твой инвентарь:</b>\n\n"
            f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b> шт.\n"
            f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Полуредкие: <b>{p['uncommon']}</b> шт.\n"
            f"<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Редкие: <b>{p['rare']}</b> шт.\n\n"
            f"Чтобы продать всё, нажми /sell")
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("sell"))
async def sell_diamonds(message: types.Message):
    p = get_player(message.chat.id)
    total = (p['common'] * 1000) + (p['uncommon'] * 5000) + (p['rare'] * 15000)
    if total == 0:
        await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя нет камней на продажу!")
        return
    db_query("UPDATE players SET balance = balance + ?, count_common=0, count_uncommon=0, count_rare=0 WHERE user_id = ?", (total, message.chat.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> Скупщик купил всё за <b>{total:,}</b> монет!", parse_mode="HTML")

# --- БОНУС, БАЛАНС, МАГАЗИН ---
@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    p = get_player(message.chat.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        await message.answer(f"⏳ Бонус будет через <b>{rem//3600}ч. {(rem%3600)//60}м.</b>", parse_mode="HTML")
        return
    gift = random.randint(500, 2500)
    db_query("UPDATE players SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (gift, now, message.chat.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Бонус: <b>{gift}</b> монет!', parse_mode="HTML")

@dp_main.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.chat.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]:,}</b>', parse_mode="HTML")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.chat.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']:,} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    await message.answer(f'🛒 <b>Магазин кирок</b>', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

# --- ОБРАБОТКА CALLBACK ---
@dp_main.callback_query(F.data.endswith("_action"))
async def handle_actions(c: types.CallbackQuery):
    action = c.data.split("_")[0]
    await c.answer()
    if action == "mine": await main_mine(c.message)
    elif action == "inv": await inventory_cmd(c.message)
    elif action == "sell": await sell_diamonds(c.message)
    elif action == "bonus": await bonus_cmd(c.message)
    elif action == "shop": await shop_cmd(c.message)
    elif action == "bal": await bal_cmd(c.message)

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Недостаточно монет!", show_alert=True)

# --- ЗАПУСК ---
async def main():
    init_db()
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())

