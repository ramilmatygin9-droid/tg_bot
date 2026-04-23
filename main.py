import 
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вставь сюда свой токен от @BotFather
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Имитация базы данных (в реальном проекте используй SQLite или PostgreSQL)
user_data = {
    "balance": 182,
    "bet": 10
}

# --- Клавиатуры ---

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    # Кнопки игр
    builder.row(types.InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
                types.InlineKeyboardButton(text="💎 Алмазы", callback_data="game_diamonds"))
    builder.row(types.InlineKeyboardButton(text="🏰 Башня", callback_data="game_tower"),
                types.InlineKeyboardButton(text="⚜️ Золото", callback_data="game_gold"))
    builder.row(types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast_games"))
    builder.row(types.InlineKeyboardButton(text="📝 Изменить ставку", callback_data="change_bet"))
    return builder.as_markup()

def mines_settings_kb():
    builder = InlineKeyboardBuilder()
    # Выбор количества мин (1-6)
    buttons = [types.InlineKeyboardButton(text=str(i), callback_data=f"mines_count_{i}") for i in range(1, 7)]
    builder.row(*buttons[:3])
    builder.row(*buttons[3:])
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()

# --- Обработчики ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (f"🕹 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💵 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "game_mines")
async def open_mines(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"💣 **Мины · выбери количество мин!**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 **Ставка:** {user_data['bet']} m¢",
        reply_markup=mines_settings_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    text = (f"🕹 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💵 **Ставка:** {user_data['bet']} m¢")
    await callback.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
