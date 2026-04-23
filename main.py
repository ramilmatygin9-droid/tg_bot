import asyncio
import random
import hashlib
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Имитация БД
users = {}

def get_header(user: types.User):
    uid = user.id
    if uid not in users: users[uid] = {"balance": 1000, "lvl": 1}
    u = users[uid]
    return (f"👤 {user.first_name} | ID: `{uid}`\n"
            f"🏆 Ваш уровень: {u['lvl']}\n"
            f"💰 Баланс: {u['balance']} m¢\n"
            f"────────────────")

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="g_b"), InlineKeyboardButton(text="⚽", callback_data="g_f"),
         InlineKeyboardButton(text="🎯", callback_data="g_d"), InlineKeyboardButton(text="🎳", callback_data="g_bw"),
         InlineKeyboardButton(text="🎲", callback_data="g_dice"), InlineKeyboardButton(text="🎰", callback_data="g_s")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="m_fast"), InlineKeyboardButton(text="Режимы 💣", callback_data="m_modes")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- МЕНЮ БЫСТРЫХ ИГР (ИЗ ВИДЕО) ---
@dp.callback_query(F.data == "m_fast")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🎡 Рул. рулетка", callback_data="g_roul"), InlineKeyboardButton(text="🎰 Монета", callback_data="g_coin")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="g_d"), InlineKeyboardButton(text="🎲 Кубик", callback_data="g_dice")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="prep_mines"), InlineKeyboardButton(text="🚀 Краш", callback_data="g_crash")],
        [InlineKeyboardButton(text="🎣 Рыбалка", callback_data="g_fish"), InlineKeyboardButton(text="🎰 Слоты", callback_data="g_s")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Быстрые игры**", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- МИНЫ: ПОДГОТОВКА (ВЫБОР КОЛИЧЕСТВА) ---
@dp.callback_query(F.data == "prep_mines")
async def setup_mines(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💣 3", callback_data="st_m_3"), InlineKeyboardButton(text="💣 4", callback_data="st_m_4"), InlineKeyboardButton(text="💣 5", callback_data="st_m_5")],
        [InlineKeyboardButton(text="💣 10", callback_data="st_m_10"), InlineKeyboardButton(text="💣 11", callback_data="st_m_11"), InlineKeyboardButton(text="💣 12", callback_data="st_m_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n💣 **Мины**\nВыбери количество бомб на поле:", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- МИНЫ: ЛОГИКА И КОЭФФИЦИЕНТЫ ---
@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines(call: types.CallbackQuery):
    count = int(call.data.split("_")[2])
    # Генерируем хэш для "Честности"
    game_id = random.randint(1000, 9999)
    game_hash = hashlib.sha256(str(game_id).encode()).hexdigest()[:15]
    
    # Таблица коэффициентов (динамическая)
    c1 = round(25/(25-count), 2)
    c2 = round(c1 * (24/(24-count)), 2)
    c3 = round(c2 * (23/(23-count)), 2)

    text = (f"{get_header(call.from_user)}\n"
            f"💣 **Мины — Игра началась!**\n"
            f"Количество мин: `{count}`\n"
            f"🛡 Hash: `{game_hash}...`\n\n"
            f"📈 **Коэффициенты:**\n"
            f"1️⃣ — x{c1} | 2️⃣ — x{c2} | 3️⃣ — x{c3}\n"
            f"────────────────\n"
            f"Нажимай на ячейки ниже 👇")
    
    # Здесь должна быть генерация кнопок 5x5 (для краткости - пример одной кнопки)
    kb = [[InlineKeyboardButton(text="🔹 Начать открывать", callback_data="click_0")]]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ОБРАБОТЧИК КРАША (ИЗ ВИДЕО) ---
@dp.callback_query(F.data == "g_crash")
async def crash_info(call: types.CallbackQuery):
    kb = [[InlineKeyboardButton(text="🚀 Взлететь!", callback_data="crash_go")],
          [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Краш**\nСделайте ставку и заберите выигрыш до взрыва!", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- СТАРТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(get_header(message.from_user), reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(get_header(call.from_user), reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
