import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

# !!! ЗАМЕНИ ЭТОТ ТЕКСТ НА СВОЙ РЕАЛЬНЫЙ ТОКЕН !!!
API_TOKEN = 'ВАШ_ТОКЕН_БОТА_ОТ_BOTFATHER'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Имитация данных пользователя (в реальном проекте используй базу данных)
user_balance = 182
current_bet = 10

# --- Функция для создания клавиатуры ГЛАВНОГО МЕНЮ ---
def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()

    # Ряд 1: Игры
    builder.row(types.InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
                types.InlineKeyboardButton(text="💎 Алмазы", callback_data="game_diamonds"))
    
    # Ряд 2: Игры
    builder.row(types.InlineKeyboardButton(text="🏰 Башня", callback_data="game_tower"),
                types.InlineKeyboardButton(text="⚜️ Золото", callback_data="game_gold"))
    
    # Ряд 3: Игры
    builder.row(types.InlineKeyboardButton(text="🐸 Квак", callback_data="game_kvak"),
                types.InlineKeyboardButton(text="HiLo ⬆️⬇️", callback_data="game_hilo"))
    
    # Ряд 4: Игры
    builder.row(types.InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="game_21"),
                types.InlineKeyboardButton(text="Пирамида ⛺️", callback_data="game_pyramid"))
    
    # Ряд 5: Арена
    builder.row(types.InlineKeyboardButton(text="🥊 Арена", callback_data="game_arena"))
    
    # Ряд 6: Быстрые игры
    builder.row(types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast_games"))

    # Ряд 7: Кнопки управления ставкой (из image_11.png)
    builder.row(types.InlineKeyboardButton(text="📝 Изменить ставку", callback_data="edit_bet"))

    # Ряд 8: Играть в WEB (из image_11.png)
    builder.row(types.InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_web_app_bot")) # Замените ссылку

    return builder.as_markup()

# --- Обработчик команды /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Приветственный текст, как на скриншотах
    welcome_text = (
        f"🕹 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {user_balance} m¢\n"
        f"💵 **Ставка:** {current_bet} m¢\n\n"
        f"👇 **Выбери игру и начинай!**"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

# --- Обработчики нажатий на кнопки (принципы работы) ---

@dp.callback_query(F.data == "game_mines")
async def process_mines(callback: types.CallbackQuery):
    # Пример перехода в меню выбора количества мин (как в image_12.png)
    builder = InlineKeyboardBuilder()
    buttons = [types.InlineKeyboardButton(text=str(i), callback_data=f"set_mines_{i}") for i in range(1, 7)]
    builder.row(*buttons[:3])
    builder.row(*buttons[3:])
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))

    text = (
        f"💣 **Мины · выбери количество мин!**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 **Ставка:** {current_bet} m¢"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    # Возврат в главное меню
    await cmd_start(callback.message)

@dp.callback_query(F.data == "edit_bet")
async def edit_bet_handler(callback: types.CallbackQuery):
    # Простое уведомление для примера
    await callback.answer("Здесь будет меню изменения ставки.", show_alert=True)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
