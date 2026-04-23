import random
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = 'ТВОЙ_ТОКЕН_ТУТ'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Имитация базы данных (в реальности лучше использовать SQLite/PostgreSQL)
user_balances = {}

def get_win_multiplier(mines: int) -> float:
    """Рассчитывает честный коэффициент в зависимости от количества мин."""
    total_cells = 25
    safe_cells = total_cells - mines
    # Вероятность угадать 1 безопасную ячейку: safe_cells / total_cells
    # Множитель = 1 / Вероятность (с небольшой комиссией дома 3%)
    probability = safe_cells / total_cells
    multiplier = (1 / probability) * 0.97 
    return round(multiplier, 2)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000.0  # Начальный баланс

    builder = InlineKeyboardBuilder()
    builder.button(text="Играть 💣", callback_data="lobby")
    
    await message.answer(
        f"🎮 **ИГРА МИНЫ**\n\n"
        f"💰 Ваш баланс: {user_balances[user_id]} 🪙\n"
        "Выберите количество мин. Чем больше риск — тем выше награда!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "lobby")
async def lobby(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    # Варианты количества мин
    mines_options = [1, 3, 5, 10, 15, 20]
    for m in mines_options:
        mult = get_win_multiplier(m)
        builder.button(text=f"💣 {m} (x{mult})", callback_data=f"bet_{m}")
    
    builder.adjust(2)
    await callback.message.edit_text(
        "🕹 **Настройка игры**\nВыберите количество мин на поле 5x5:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("bet_"))
async def play_round(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mines_count = int(callback.data.split("_")[1])
    bet_amount = 100 # Фиксированная ставка для примера
    
    if user_balances.get(user_id, 0) < bet_amount:
        await callback.answer("Недостаточно монет! Баланс пополнен на 1000 для теста.", show_alert=True)
        user_balances[user_id] = 1000
        return

    user_balances[user_id] -= bet_amount
    multiplier = get_win_multiplier(mines_count)
    
    # Логика определения победы
    # Шанс победы = количество безопасных ячеек / общее кол-во ячеек
    win_chance = (25 - mines_count) / 25
    is_win = random.random() < win_chance

    if is_win:
        win_sum = round(bet_amount * multiplier, 2)
        user_balances[user_id] += win_sum
        result_text = (
            f"✅ **ВЫИГРЫШ!**\n\n"
            f"💰 Ставка: {bet_amount}\n"
            f"📈 Множитель: x{multiplier}\n"
            f"💵 Прибыль: +{win_sum} 🪙\n"
            f"💳 Баланс: {user_balances[user_id]} 🪙"
        )
    else:
        result_text = (
            f"💥 **БУМ! ПРОИГРЫШ**\n\n"
            f"💣 Вы выбрали {mines_count} мин и подорвались.\n"
            f"📉 Потеряно: {bet_amount} 🪙\n"
            f"💳 Баланс: {user_balances[user_id]} 🪙"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="Ещё раз 🔄", callback_data="lobby")
    builder.button(text="В меню 🏠", callback_data="main_menu")

    await callback.message.edit_text(result_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery):
    # Возвращаем пользователя в начало
    await cmd_start(callback.message)
    await callback.answer()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
