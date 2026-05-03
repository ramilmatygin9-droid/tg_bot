import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_ID = 0  # Твой ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

users_data = {}

def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {"balance": 1000}
    return users_data[user_id]

# --- КЛАВИАТУРЫ ---

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ИГРЫ", callback_data="all_games")],
        [InlineKeyboardButton(text="💰 БАЛАНС", callback_data="my_balance")]
    ])

def games_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 РАКЕТА X2", callback_data="game_rocket")],
        [InlineKeyboardButton(text="💣 МИНЫ 5x5", callback_data="game_mines")],
        [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="to_main")]
    ])

# --- ИГРА: РАКЕТА С АНИМАЦИЕЙ ---
@dp.callback_query(F.data == "game_rocket")
async def rocket_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Низко (x2)", callback_data="fly_2.0")],
        [InlineKeyboardButton(text="🌌 Высоко (x5)", callback_data="fly_5.0")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")]
    ])
    await callback.message.edit_text("🚀 **ПОДГОТОВКА К ЗАПУСКУ**\n\nВыбери высоту полета:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("fly_"))
async def rocket_animation(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] < 100:
        return await callback.answer("Мало коинов (нужно 100)!", show_alert=True)
    
    user["balance"] -= 100
    mult = float(callback.data.split("_")[1])
    
    # Анимация полета
    stages = ["🚀 Взлёт...", "🔥🚀 Прохождение атмосферы...", "✨🚀 Выход в открытый космос...", "🛰🚀 Почти долетели..."]
    for stage in stages:
        await callback.message.edit_text(f"**{stage}**", parse_mode="Markdown")
        await asyncio.sleep(0.7)

    # Шанс (x2 - 45%, x5 - 15%)
    chance = 45 if mult == 2.0 else 15
    if random.randint(1, 100) <= chance:
        win = int(100 * mult)
        user["balance"] += win
        await callback.message.answer(f"✅ **УСПЕХ!** Ракета долетела на x{mult}!\nВыигрыш: `{win}` 💰", parse_mode="Markdown")
    else:
        await callback.message.answer(f"💥 **КАТАСТРОФА!** Ракета взорвалась...\nПотеряно: `100` 💰", parse_mode="Markdown")
    
    await all_games(callback)

# --- ИГРА: МИНЫ 5x5 ---
@dp.callback_query(F.data == "game_mines")
async def mines_5x5(callback: CallbackQuery):
    # Создаем поле 5x5 (25 ячеек). Сделаем 5 мин на поле.
    field = (["bomb"] * 5) + (["gem"] * 20)
    random.shuffle(field)
    
    kb = []
    for i in range(0, 25, 5): # Создаем 5 рядов по 5 кнопок
        row = []
        for j in range(5):
            item = field[i + j]
            row.append(InlineKeyboardButton(text="❓", callback_data=f"mine_{item}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")])
    
    await callback.message.edit_text(
        "💣 **МИНЫ 5x5**\nНа поле спрятано **5 мин**. Найди кристалл!\n💎 +100 коинов | 💥 -250 коинов", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data.startswith("mine_"))
async def mine_result(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    res = callback.data.split("_")[1]
    
    if res == "bomb":
        user["balance"] -= 250
        await callback.answer("💥 БОМБА! Вы подорвались! -250 коинов.", show_alert=True)
        await all_games(callback)
    else:
        user["balance"] += 100
        await callback.answer("💎 КРИСТАЛЛ! +100 коинов.", show_alert=True)
        # Оставляем игрока на поле, чтобы он мог нажать еще раз
        await mines_5x5(callback)

# --- СИСТЕМНЫЕ ФУНКЦИИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🛠 Добро пожаловать в Phoenix Games!", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "all_games")
async def all_games(callback: CallbackQuery):
    await callback.message.edit_text("🕹 Выбери игру:", reply_markup=games_menu_kb())

@dp.callback_query(F.data == "my_balance")
async def check_balance(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.answer(f"💰 Баланс: {user['balance']} коинов", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text("🛠 Главное меню:", reply_markup=main_menu_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
