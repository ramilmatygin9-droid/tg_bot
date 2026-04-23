from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Инициализация бота
bot = Bot(token="ТВОЙ_ТОКЕН")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    # Создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопки, как в твоем примере
    btn_mines = types.InlineKeyboardButton("💣 Мины", callback_data="play_mines")
    btn_slots = types.InlineKeyboardButton("🎰 Слоты", callback_data="play_slots")
    
    keyboard.add(btn_mines, btn_slots)
    
    await message.answer("🎮 ВЫБЕРИ ИГРУ И НАЧИНАЙ!", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
