import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

# Вставь свой токен
TOKEN = '8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0'
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для создания сетки 5x5
def get_mines_kb(signal=False):
    # Если signal=True, помечаем рандомные 3 клетки звездочкой
    marked_cells = random.sample(range(25), 3) if signal else []
    
    buttons = []
    row = []
    for i in range(25):
        text = "⭐" if i in marked_cells else "🔹"
        row.append(InlineKeyboardButton(text=text, callback_data="empty"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    
    # Кнопка для генерации нового сигнала
    buttons.append([InlineKeyboardButton(text="🚀 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Привет! Нажми на кнопку ниже, чтобы получить сигнал для Mines:", 
                         reply_markup=get_mines_kb())

@dp.callback_query(F.data == "get_signal")
async def send_signal(callback: types.Callback_query):
    await callback.message.edit_text("⚡️ Сигнал сформирован:", 
                                     reply_markup=get_mines_kb(signal=True))

# Запуск бота
if __name__ == '__main__':
    dp.run_polling(bot)
