import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Имитация БД
user_db = {
    "balance": 5000.0,
    "bet": 100.0,
    "mines_count": 3
}

# --- КЛАВИАТУРЫ ---

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    # Как в gminesbot: Игры в два столбца + кнопки профиля
    builder.row(types.InlineKeyboardButton(text="💣 Mines", callback_data="game_mines"),
                types.InlineKeyboardButton(text="🎰 Slots", callback_data="game_slots"))
    builder.row(types.InlineKeyboardButton(text="💎 Crystals", callback_data="game_crystals"),
                types.InlineKeyboardButton(text="🎲 Dice", callback_data="game_dice"))
    builder.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                types.InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit"))
    builder.row(types.InlineKeyboardButton(text="📊 Топ игроков", callback_data="top"))
    return builder.as_markup()

def mines_settings_kb():
    builder = InlineKeyboardBuilder()
    # Выбор кол-ва мин
    builder.row(
        types.InlineKeyboardButton(text="3💣", callback_data="set_m_3"),
        types.InlineKeyboardButton(text="5💣", callback_data="set_m_5"),
        types.InlineKeyboardButton(text="10💣", callback_data="set_m_10")
    )
    builder.row(types.InlineKeyboardButton(text="⚙️ Своё число", callback_data="custom_mines"))
    builder.row(types.InlineKeyboardButton(text="💰 Изменить ставку", callback_data="edit_bet"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def game_field_kb():
    builder = InlineKeyboardBuilder()
    # Сетка 5x5 (25 кнопок)
    for i in range(25):
        builder.add(types.InlineKeyboardButton(text="🔹", callback_data=f"step_{i}"))
    builder.adjust(5)
    builder.row(types.InlineKeyboardButton(text="💰 Забрать", callback_data="cashout"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        f"👋 **Привет, {message.from_user.first_name}!**\n\n"
        f"💳 **Ваш баланс:** `{user_db['balance']} ₽`\n"
        f"🎮 **Выбирай игру из списка ниже:**"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"💳 **Баланс:** `{user_db['balance']} ₽`\n🎮 **Выбирай игру:**",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "game_mines")
async def mines_main(callback: types.CallbackQuery):
    text = (
        f"💣 **Mines**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 **Ставка:** `{user_db['bet']} ₽`\n"
        f"💣 **Кол-во мин:** `{user_db['mines_count']}`\n\n"
        f"Нажмите кнопку ниже, чтобы начать игру."
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="▶️ ИГРАТЬ", callback_data="start_mines_game"))
    builder.row(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="mines_settings"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "mines_settings")
async def m_settings(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ **Настройка игры Mines:**", reply_markup=mines_settings_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "start_mines_game")
async def play_mines(callback: types.CallbackQuery):
    # Логика начала игры
    await callback.message.edit_text(
        f"🕹 **Игра началась!**\n"
        f"💰 **Множитель:** `x0.00`\n"
        f"💵 **Выигрыш:** `0 ₽`",
        reply_markup=game_field_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    text = (
        f"👤 **Профиль пользователя**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{callback.from_user.id}`\n"
        f"💰 Баланс: `{user_db['balance']} ₽`\n"
        f"📈 Всего игр: `124`"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
