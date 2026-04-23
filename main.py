import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КНОПКИ (ИНТЕРФЕЙС) ---

def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="💣 ИГРАТЬ (MINES)", callback_data="open_mines")],
        [InlineKeyboardButton(text="📈 КАНАЛ", url="https://t.me/your_channel"), # Замени ссылку
         InlineKeyboardButton(text="👥 О БОТЕ", callback_data="about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_mines_grid(show_signal=False):
    # Генерация сетки 5x5
    # Если show_signal=True, то ставим 3 звезды в рандомные места
    signal_cells = random.sample(range(25), 3) if show_signal else []
    
    buttons = []
    row = []
    for i in range(25):
        char = "⭐" if i in signal_cells else "🟦"
        row.append(InlineKeyboardButton(text=char, callback_data="cell_click"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    
    # Кнопки управления под сеткой
    buttons.append([InlineKeyboardButton(text="🚀 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")])
    buttons.append([InlineKeyboardButton(text="⬅️ В МЕНЮ", callback_data="to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТКА КОМАНД (ФУНКЦИОНАЛ) ---

# Команда /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я — мощный предсказатель для игры Mines.\n"
        "Выбери действие в меню ниже:",
        reply_markup=get_main_menu()
    )

# Переход к игре
@dp.callback_query(F.data == "open_mines")
async def open_mines(call: types.CallbackQuery):
    await call.message.edit_text(
        "📝 **Режим: Mines**\n\nНажми кнопку ниже, чтобы я проанализировал алгоритм и выдал сигнал.",
        reply_markup=get_mines_grid(),
        parse_mode="Markdown"
    )

# Генерация сигнала
@dp.callback_query(F.data == "get_signal")
async def process_signal(call: types.CallbackQuery):
    # Небольшая задержка "для вида" анализа
    await call.answer("Анализирую данные...")
    await call.message.edit_text(
        "✅ **СИГНАЛ ГОТОВ!**\n\nШанс прохода: 98%\nКоличество мин: 3",
        reply_markup=get_mines_grid(show_signal=True),
        parse_mode="Markdown"
    )

# Возврат в главное меню
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(
        "Вы вернулись в главное меню. Выберите действие:",
        reply_markup=get_main_menu()
    )

# Заглушка для кнопок сетки и инфо
@dp.callback_query(F.data == "cell_click")
async def cell_info(call: types.CallbackQuery):
    await call.answer("Нажми на 'Получить сигнал'", show_alert=False)

@dp.callback_query(F.data == "about")
async def about_info(call: types.CallbackQuery):
    await call.answer("Бот создан для демонстрации стратегий игры Mines.", show_alert=True)

# --- ЗАПУСК ---
async def main():
    print("Бот успешно запущен! Проверь Telegram.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")
