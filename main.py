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
        [InlineKeyboardButton(text="🎮 ИГРАТЬ", callback_data="all_games")],
        [InlineKeyboardButton(text="💰 БАЛАНС", callback_data="my_balance")]
    ])

def games_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 РАКЕТА (БАРАБАН)", callback_data="game_rocket")],
        [InlineKeyboardButton(text="💣 МИНЫ 5x5", callback_data="game_mines")],
        [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="to_main")]
    ])

# --- ИГРА: РАКЕТА (ЭФФЕКТ БАРАБАНА) ---
@dp.callback_query(F.data == "game_rocket")
async def rocket_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 ЗАПУСК (100 💰)", callback_data="spin_rocket")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")]
    ])
    await callback.message.edit_text("🚀 **РАКЕТНЫЙ БАРАБАН**\n\nНажми кнопку, чтобы запустить ракету и узнать множитель!", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "spin_rocket")
async def rocket_spin(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] < 100:
        return await callback.answer("Мало коинов!", show_alert=True)
    
    user["balance"] -= 100
    
    # Список для эффекта барабана
    slots = ["🛸 x0.0", "🚀 x1.5", "✨ x2.0", "🔥 x0.0", "🌌 x5.0", "🚀 x1.1", "🛸 x0.0", "💎 x10.0"]
    
    # Имитация кручения (барабан)
    for _ in range(6): # 6 раз меняем картинку
        random_slot = random.choice(slots)
        await callback.message.edit_text(f"🎰 **КРУТИМ БАРАБАН:**\n\n> {random_slot} <", parse_mode="Markdown")
        await asyncio.sleep(0.3)

    # Финальный расчет
    # Шансы: 50% - проигрыш (x0), 30% - x1.5, 15% - x3, 5% - x10
    res_val = random.choices([0.0, 1.5, 3.0, 10.0], weights=[50, 30, 15, 5])[0]
    
    if res_val > 0:
        win = int(100 * res_val)
        user["balance"] += win
        result_text = f"✅ **ПОБЕДА!**\n\nРезультат: ✨ `{res_val}x`\nВыигрыш: +{win} 💰"
    else:
        result_text = f"💥 **ВЗРЫВ!**\n\nРезультат: 💀 `0.0x`\nРакета не взлетела."

    await callback.message.edit_text(result_text, reply_markup=games_menu_kb(), parse_mode="Markdown")

# --- ИГРА: МИНЫ 5x5 ---
@dp.callback_query(F.data == "game_mines")
async def mines_5x5(callback: CallbackQuery):
    field = (["bomb"] * 5) + (["gem"] * 20)
    random.shuffle(field)
    
    kb = []
    for i in range(0, 25, 5):
        row = []
        for j in range(5):
            item = field[i + j]
            row.append(InlineKeyboardButton(text="❓", callback_data=f"mine_{item}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")])
    
    await callback.message.edit_text(
        "💣 **МИНЫ 5x5**\nНа поле **5 мин**. Найди кристалл!\n💎 +100 | 💥 -250", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data.startswith("mine_"))
async def mine_result(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    res = callback.data.split("_")[1]
    
    if res == "bomb":
        user["balance"] -= 250
        await callback.answer("💥 БОМБА! -250 💰", show_alert=True)
        await all_games(callback)
    else:
        user["balance"] += 100
        await callback.answer("💎 КРИСТАЛЛ! +100 💰", show_alert=True)
        await mines_5x5(callback)

# --- СИСТЕМА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🚀 Добро пожаловать!", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "all_games")
async def all_games(callback: CallbackQuery):
    await callback.message.edit_text("🕹 Выбери игру:", reply_markup=games_menu_kb())

@dp.callback_query(F.data == "my_balance")
async def check_balance(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.answer(f"💰 Баланс: {user['balance']}", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=main_menu_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
