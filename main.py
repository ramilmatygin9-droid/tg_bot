import asyncio
import random
import hashlib
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Замени на свой токен
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных
user_db = {}

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---

def get_header(user: types.User):
    uid = user.id
    if uid not in user_db:
        user_db[uid] = {"balance": 1000, "lvl": 1}
    u = user_db[uid]
    return (f"👤 {user.first_name} | ID: `{uid}`\n"
            f"🏆 Ваш уровень: {u['lvl']}\n"
            f"💰 Баланс: {u['balance']} m¢\n"
            f"────────────────")

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="g_basket"), InlineKeyboardButton(text="⚽", callback_data="g_foot"),
         InlineKeyboardButton(text="🎯", callback_data="g_darts"), InlineKeyboardButton(text="🎳", callback_data="g_bowl"),
         InlineKeyboardButton(text="🎲", callback_data="g_dice"), InlineKeyboardButton(text="🎰", callback_data="g_slots")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="m_fast"), InlineKeyboardButton(text="Режимы 💣", callback_data="m_modes")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- ОБРАБОТЧИКИ МЕНЮ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"{get_header(message.from_user)}\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user)}\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "m_fast")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="g_roul"), InlineKeyboardButton(text="💰 Монетка", callback_data="g_coin")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="prep_mines"), InlineKeyboardButton(text="🚀 Краш", callback_data="g_crash")],
        [InlineKeyboardButton(text="🎣 Рыбалка", callback_data="g_fish"), InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Быстрые игры**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ИГРА МИНЫ (КАК НА ВИДЕО) ---

@dp.callback_query(F.data == "prep_mines")
async def setup_mines(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💣 3", callback_data="st_m_3"), InlineKeyboardButton(text="💣 4", callback_data="st_m_4"), InlineKeyboardButton(text="💣 5", callback_data="st_m_5")],
        [InlineKeyboardButton(text="💣 10", callback_data="st_m_10"), InlineKeyboardButton(text="💣 11", callback_data="st_m_11"), InlineKeyboardButton(text="💣 12", callback_data="st_m_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n💣 **Мины**\nВыбери количество бомб:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines(call: types.CallbackQuery):
    count = int(call.data.split("_")[2])
    h = hashlib.sha256(str(random.random()).encode()).hexdigest()[:10]
    # Коэффициенты
    c1 = round(25/(25-count), 2)
    c2 = round(c1 * (24/(24-count)), 2)
    
    text = (f"{get_header(call.from_user)}\n💣 **Игра началась!**\nМин: {count}\n"
            f"🛡 Hash: `{h}`\n📈 x{c1} | x{c2} | ...\n────────────────")
    
    # Сетка 5х5 (упрощенная для примера)
    buttons = []
    for _ in range(5):
        buttons.append([InlineKeyboardButton(text="🔹", callback_data="m_click") for _ in range(5)])
    buttons.append([InlineKeyboardButton(text="📥 Забрать", callback_data="to_main")])
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ИГРА КРАШ ---

@dp.callback_query(F.data == "g_crash")
async def crash_start(call: types.CallbackQuery):
    kb = [[InlineKeyboardButton(text="x1.5", callback_data="c_1.5"), InlineKeyboardButton(text="x2.0", callback_data="c_2.0")],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Краш**\nВыбери множитель:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ДАРТС (ВЫБОР СЕКТОРОВ) ---

@dp.callback_query(F.data == "g_darts")
async def darts_bet(call: types.CallbackQuery):
    kb = [[InlineKeyboardButton(text="🎯 Центр (x5)", callback_data="d_6")],
          [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="d_red"), InlineKeyboardButton(text="⚪ Белое (x2)", callback_data="d_white")]]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🎯 Выбери куда целишься:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА DICE ИГР (ФУТБОЛ, БАСКЕТ, СЛОТЫ) ---

@dp.callback_query(F.data.in_(["g_basket", "g_foot", "g_bowl", "g_dice", "g_slots"]))
async def play_dice(call: types.CallbackQuery):
    emoji_map = {"g_basket": "🏀", "g_foot": "⚽", "g_bowl": "🎳", "g_dice": "🎲", "g_slots": "🎰"}
    emoji = emoji_map[call.data]
    
    msg = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5) # Ждем анимацию
    
    val = msg.dice.value
    win = False
    
    if emoji == "🎰" and val in [1, 22, 43, 64]: win = True
    elif emoji in ["🏀", "⚽"] and val >= 4: win = True
    elif emoji == "🎳" and val == 6: win = True
    elif emoji == "🎲" and val >= 4: win = True

    if win:
        user_db[call.from_user.id]["balance"] += 50
        res = "🥳 **Победа!**"
    else:
        user_db[call.from_user.id]["balance"] -= 10
        res = "❌ **Проигрыш**"
        
    await call.message.answer(f"{get_header(call.from_user)}\n{res}\nРезультат: {val}", reply_markup=main_kb(), parse_mode="Markdown")

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
