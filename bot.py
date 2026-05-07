import asyncio
import logging
import random
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# Эмодзи и Кастомные ID
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
SKUPSHIK_ID = "5452136652111620778"   

# Алмазы
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
dp_main = Dispatcher()

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
    # Достаем данные из БД
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, count_common, count_uncommon, count_rare FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, last_bonus) VALUES (?, 0, 1, '', ?, 0)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "common": 0, "uncommon": 0, "rare": 0}
    
    # ВАЖНО: Ключи должны называться именно так, как ты их вызываешь в cmd_inventory
    return {
        "balance": data[0], 
        "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3], 
        "common": data[4],   # Исправлено
        "uncommon": data[5], # Исправлено
        "rare": data[6]      # Исправлено
    }


# --- ОБРАБОТЧИКИ ---

@dp_main.message(Command("start"))
async def cmd_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> Привет, {message.from_user.first_name}! Ты попал в симулятор майнера.\n'
        f'Используй /mine чтобы начать копать или /menu для навигации!',
        parse_mode="HTML"
    )

@dp_main.message(Command("mine"))
async def cmd_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: pass
    
    luck = random.random()
    diamond_text = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_RARE}">💎</tg-emoji> <b>Редкий алмаз!</b>'
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_UNCOMMON}">💎</tg-emoji> <b>Полуредкий алмаз!</b>'
    elif luck < 0.40:
        db_query("UPDATE players SET count_common = count_common + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_COMMON}">💎</tg-emoji> <b>Обычный алмаз!</b>'

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    
    try: await status_msg.delete()
    except: pass
    
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Добыто: <b>{reward}</b> монет{diamond_text}', parse_mode="HTML")

@dp_main.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    try:
        p = get_player(message.from_user.id)
        text = (f"🎒 <b>Твой инвентарь:</b>\n\n"
                f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b> шт.\n"
                f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Полуредкие: <b>{p['uncommon']}</b> шт.\n"
                f"<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Редкие: <b>{p['rare']}</b> шт.")
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в inventory: {e}")
        await message.answer("Произошла ошибка при открытии инвентаря.")


@dp_main.message(Command("sale"))
async def cmd_sale(message: types.Message):
    p = get_player(message.from_user.id)
    total = (p['common'] * 1000) + (p['uncommon'] * 5000) + (p['rare'] * 15000)
    if total == 0:
        await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя нет алмазов на продажу!", parse_mode="HTML")
        return
    db_query("UPDATE players SET balance = balance + ?, count_common=0, count_uncommon=0, count_rare=0 WHERE user_id = ?", (total, message.from_user.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> Продано за <b>{total:,}</b> монет!", parse_mode="HTML")

@dp_main.message(Command("shop"))
async def cmd_shop(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    for k, v in SHOP_PICKS.items():
        if k > p["pick_lvl"]:
            kb.append([InlineKeyboardButton(text=f"{v['name']} — {v['price']:,} 💵", callback_data=f"buy_{k}")])
    
    if not kb:
        await message.answer("🛒 У тебя уже самая лучшая кирка!")
        return
        
    await message.answer(f'🛒 <b>Магазин кирок</b>\nТвоя кирка: {SHOP_PICKS[p["pick_lvl"]]["name"]}', 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.message(Command("top"))
async def cmd_top(message: types.Message):
    top_players = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "🏆 <b>Топ 10 богатых майнеров:</b>\n\n"
    for i, (name, bal) in enumerate(top_players, 1):
        text += f"{i}. {name or 'Аноним'} — 💰 <b>{bal:,}</b>\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        await message.answer(f"⏳ Бонус будет через <b>{rem//3600}ч. {(rem%3600)//60}м.</b>", parse_mode="HTML")
        return
    gift = random.randint(500, 2500)
    db_query("UPDATE players SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (gift, now, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Бонус: <b>{gift}</b> монет!', parse_mode="HTML")

@dp_main.message(Command("balance"))
async def cmd_balance(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]:,}</b>', parse_mode="HTML")

@dp_main.message(Command("menu"))
async def cmd_menu(message: types.Message):
    kb = [
        [InlineKeyboardButton(text="⛏ Начать копать", callback_data="mine_action")],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv_action"),
            InlineKeyboardButton(text="🤓 Скупщик", callback_data="sale_action")
        ],
        [
            InlineKeyboardButton(text="🛒 Магазин", callback_data="shop_action"),
            InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus_action")
        ],
        [InlineKeyboardButton(text="💳 Баланс", callback_data="bal_action")]
    ]
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Главное меню</b>', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

# --- CALLBACKS ---
@dp_main.callback_query(F.data.endswith("_action"))
async def handle_actions(c: types.CallbackQuery):
    action = c.data.split("_")[0]
    await c.answer()
    if action == "mine": await cmd_mine(c.message)
    elif action == "inv": await cmd_inventory(c.message)
    elif action == "sale": await cmd_sale(c.message)
    elif action == "bonus": await cmd_bonus(c.message)
    elif action == "shop": await cmd_shop(c.message)
    elif action == "bal": await cmd_balance(c.message)

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: 
        await c.answer("Недостаточно монет!", show_alert=True)

# --- ЗАПУСК ---
async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="menu", description="📱 Меню"),
        BotCommand(command="mine", description="⛏ Копать"),
        BotCommand(command="shop", description="🛒 Магазин"),
        BotCommand(command="inventory", description="🎒 Инвентарь"),
        BotCommand(command="sale", description="💎 Продать алмазы"),
        BotCommand(command="balance", description="💰 Баланс"),
        BotCommand(command="top", description="🏆 Топ"),
        BotCommand(command="bonus", description="🎁 Бонус")
    ])
    await dp_main.start_polling(main_bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
