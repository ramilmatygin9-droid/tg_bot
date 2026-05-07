import asyncio
import logging
import random
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
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
DIAMOND_RARE = "6269242483763913842"     

# ЦЕНЫ ПРОДАЖИ (для инвентаря)
PRICES = {
    "common": 1000,
    "uncommon": 5000,
    "rare": 15000
}

# Магазин
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
                   balance INTEGER DEFAULT 0, 
                   pick_lvl INTEGER DEFAULT 1, 
                   used_promos TEXT DEFAULT '', 
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
    res = None
    if fetchone: res = cur.fetchone()
    elif fetchall: res = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id, username="Аноним"):
    data = db_query("SELECT balance, pick_lvl, last_bonus, count_common, count_uncommon, count_rare FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, username) VALUES (?, 0, 1, ?)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "last_bonus": 0, "common": 0, "uncommon": 0, "rare": 0}
    return {
        "balance": data[0], "pick_lvl": data[1], "last_bonus": data[2],
        "common": data[3], "uncommon": data[4], "rare": data[5]
    }

# --- ИНВЕНТАРЬ ---

@dp_main.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    p = get_player(message.from_user.id)
    pick_name = SHOP_PICKS.get(p['pick_lvl'], {}).get('name', 'Руки')
    
    text = (
        f"<b><tg-emoji emoji-id='{PICKAXE_ID}'>🎒</tg-emoji> Твой инвентарь:</b>\n\n"
        f"⛏ Кирка: <b>{pick_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b> шт.\n"
        f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>🔷</tg-emoji> Необычные: <b>{p['uncommon']}</b> шт.\n"
        f"<tg-emoji emoji-id='{DIAMOND_RARE}'>🔮</tg-emoji> Редкие: <b>{p['rare']}</b> шт.\n\n"
        f"💰 <i>Нажми кнопку ниже, чтобы продать всё Скупщику!</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all_items")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu_back")]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp_main.callback_query(F.data == "sell_all_items")
async def process_sell(callback: CallbackQuery):
    p = get_player(callback.from_user.id)
    
    total_money = (p['common'] * PRICES['common']) + \
                  (p['uncommon'] * PRICES['uncommon']) + \
                  (p['rare'] * PRICES['rare'])
    
    if total_money == 0:
        await callback.answer("❌ У тебя нет ресурсов для продажи!", show_alert=True)
        return

    db_query(
        "UPDATE players SET balance = balance + ?, count_common = 0, count_uncommon = 0, count_rare = 0 WHERE user_id = ?",
        (total_money, callback.from_user.id),
        commit=True
    )
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='{SKUPSHIK_ID}'>🧔</tg-emoji> Скупщик доволен!</b>\n\n"
        f"Ты продал ресурсы и получил: <b>{total_money:,} 💰</b>",
        parse_mode="HTML"
    )
    await callback.answer("Успешно продано!")

# --- ОСТАЛЬНЫЕ КОМАНДЫ (БЕЗ ИЗМЕНЕНИЙ) ---

@dp_main.message(Command("start"))
async def cmd_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(f"⛏ Привет, {message.from_user.first_name}! Жми /menu чтобы начать игру.")

@dp_main.message(Command("menu"))
async def cmd_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏ Копать", callback_data="mine_action")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv_action"),
         InlineKeyboardButton(text="🛒 Магазин", callback_data="shop_action")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus_action"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top_action")],
        [InlineKeyboardButton(text="💳 Баланс", callback_data="bal_action")]
    ])
    await message.answer(f"<b>ГЛАВНОЕ МЕНЮ</b>", reply_markup=kb, parse_mode="HTML")

@dp_main.message(Command("mine"))
async def cmd_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 10)
    msg = await message.answer(f"⛏ <b>Копаем...</b> (⏳ {wait_time}с)", parse_mode="HTML")
    await asyncio.sleep(wait_time)
    
    luck = random.random()
    res_text = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        res_text = f"\n<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> <b>Редкий алмаз!</b>"
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        res_text = f"\n<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> <b>Полуредкий алмаз!</b>"
    elif luck < 0.40:
        db_query("UPDATE players SET count_common = count_common + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        res_text = f"\n<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> <b>Обычный алмаз!</b>"

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await msg.edit_text(f"💰 Добыто: <b>{reward}</b> монет{res_text}", parse_mode="HTML")

@dp_main.callback_query()
async def callbacks(c: types.CallbackQuery):
    # Добавляем обработку инвентаря через меню
    if c.data == "inv_action": await cmd_inventory(c.message)
    elif c.data == "mine_action": await cmd_mine(c.message)
    elif c.data == "bal_action": 
        p = get_player(c.from_user.id)
        await c.message.answer(f"💳 Баланс: <b>{p['balance']:,}</b>", parse_mode="HTML")
    elif c.data == "menu_back": await cmd_menu(c.message)
    # ... (остальные твои колбэки: shop, bonus, top)
    await c.answer()

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="menu", description="📱 Меню"),
        BotCommand(command="mine", description="⛏ Копать"),
        BotCommand(command="inventory", description="🎒 Инвентарь")
    ])
    await dp_main.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
