import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 
ADMIN_TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"
MY_ID = 846239258 

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

# Имитация базы данных пользователей
user_data = {"balance": 1000, "bet": 10}
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="prep_slots")
        ],
        [
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="prep_mines"),
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")
        ],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet_main")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: {user_data['balance']} mс\n💸 Ставка: {user_data['bet']} mс", 
        reply_markup=main_kb()
    )

# --- ЛОГИКА ИГР (КНОПКИ ТЕПЕРЬ РАБОТАЮТ) ---

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_back = [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    
    if game == "dice":
        text = f"Рамиль\n🎲 **Кубик · выбери режим!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
            [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
            btn_back
        ]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")], 
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")], btn_back]
    elif game == "mines":
        text = f"Рамиль\n💣 **Мины · выбери количество мин!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="1 мина", callback_data="start_mines_1"), InlineKeyboardButton(text="3 мины", callback_data="start_mines_3")],
              [InlineKeyboardButton(text="5 мин", callback_data="start_mines_5"), InlineKeyboardButton(text="10 мин", callback_data="start_mines_10")], btn_back]
    else:
        await call.answer("Данная игра в разработке", show_alert=True)
        return

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ОБЩИЙ ОБРАБОТЧИК ДЛЯ РЕЗУЛЬТАТОВ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    choice = data[2]
    
    # Простая проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    win = False
    result_text = ""
    
    if game_type == "dice":
        res = random.randint(1, 6)
        if choice.isdigit() and int(choice) == res: win = True
        elif choice == "even" and res % 2 == 0: win = True
        elif choice == "odd" and res % 2 != 0: win = True
        elif choice == "high" and res > 3: win = True
        elif choice == "low" and res < 3: win = True
        result_text = f"🎲 Выпало число: {res}"

    elif game_type == "foot":
        res = random.choice(["goal", "miss"])
        win = (res == choice)
        result_text = "⚽ Г-О-О-О-Л!" if res == "goal" else "🥅 Мимо..."

    # Обработка выигрыша/проигрыша
    if win:
        user_data["balance"] += user_data["bet"]
        await call.message.answer(f"🎉 {result_text}\nВы выиграли! Баланс: {user_data['balance']} mc")
    else:
        user_data["balance"] -= user_data["bet"]
        await call.message.answer(f"📉 {result_text}\nПроигрыш. Баланс: {user_data['balance']} mc")
    
    await call.answer()
    await cmd_start(call.message)

# --- ЛОГИКА НАЗАД ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(
        f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", 
        reply_markup=main_kb()
    )

# --- ИСПРАВЛЕННЫЙ ЗАПУСК (ДЛЯ RAILWAY) ---
async def main():
    # Удаляем вебхуки, чтобы избежать ошибки Conflict
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем только одного диспетчера для основного бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
