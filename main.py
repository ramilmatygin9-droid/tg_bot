import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦИЯ ИНТЕРФЕЙСА (КАК НА СКРИНШОТЕ) ---
def get_game_menu(balance=44, bet=10):
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {balance} m¢\n"
        f"💸 **Ставка:** {bet} m¢\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    
    kb = [
        # Первый ряд - эмодзи игры
        [
            InlineKeyboardButton(text="🏀", callback_data="game_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="game_football"),
            InlineKeyboardButton(text="🎯", callback_data="game_darts"),
            InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="game_dice"),
            InlineKeyboardButton(text="🎰", callback_data="game_slots"),
        ],
        # Второй ряд - кнопки режимов
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast_games"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes_mines"),
        ],
        # Третий ряд - WEB версия
        [
            InlineKeyboardButton(text="🕹 Играть в WEB", web_app=types.WebAppInfo(url="https://google.com")) # Тут нужна твоя ссылка
        ],
        # Четвертый ряд - Изменение ставки
        [
            InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")
        ]
    ]
    
    return text, InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Очищаем вебхуки и запускаем меню
    text, markup = get_game_menu()
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "modes_mines")
async def mines_mode(call: types.CallbackQuery):
    # Тут можно вызвать ту самую сетку 5х5, которую мы делали раньше
    await call.answer("Переходим в Mines...")
    await call.message.edit_text("💣 **Режим MINES**\nВыбери количество мин:", reply_markup=None) # Добавь сюда свою клавиатуру

@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    await call.answer("Функция изменения ставки в разработке", show_alert=True)

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Интерфейс запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
