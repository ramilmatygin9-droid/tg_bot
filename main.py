
from import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Твой токен, который ты дал
TOKEN = '8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для генерации клавиатуры с «сигналом»
def get_mines_grid(show_signal=False):
    # Генерируем 3 случайных места для «звезд» (сигналов)
    signal_indices = random.sample(range(25), 3) if show_signal else []
    
    buttons = []
    row = []
    
    for i in range(25):
        # Если это сигнал — ставим звезду, если нет — синий квадрат
        char = "⭐" if i in signal_indices else "🟦"
        row.append(InlineKeyboardButton(text=char, callback_data="none"))
        
        if len(row) == 5: # Делаем ряды по 5 кнопок
            buttons.append(row)
            row = []
            
    # Добавляем главную кнопку под сеткой
    buttons.append([InlineKeyboardButton(text="🚀 ПОЛУЧИТЬ СИГНАЛ", callback_data="generate_signal")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f"🤖 **Привет, {message.from_user.first_name}!**\n\n"
        "Я бот-аналитик для игры Mines.\n"
        "Нажми на кнопку ниже, чтобы я рассчитал выигрышную комбинацию.",
        reply_markup=get_mines_grid(),
        parse_mode="Markdown"
    )

# Хэндлер для кнопки генерации
@dp.callback_query(F.data == "generate_signal")
async def handle_signal(call: types.CallbackQuery):
    # Редактируем сообщение, показывая новые «звезды»
    await call.message.edit_text(
        "✅ **Сигнал успешно сгенерирован!**\n"
        "Рекомендуем ставить на эти ячейки:",
        reply_markup=get_mines_grid(show_signal=True),
        parse_mode="Markdown"
    )
    # Обязательно отвечаем на колбэк, чтобы убрать «часики»
    await call.answer()

async def main():
    print("Бот запущен! Напиши /start в Telegram.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
