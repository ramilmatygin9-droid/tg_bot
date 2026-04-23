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

# --- ИНТЕРФЕЙС ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_back = [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    
    if game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="play_bask_goal")], 
            [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="play_bask_miss")], 
            btn_back
        ]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")], 
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")], 
            btn_back
        ]
    elif game == "dice":
        text = f"Рамиль\n🎲 **Кубик · выбери режим!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
            btn_back
        ]
    # Другие игры можно добавить по аналогии
    else:
        await call.answer("Игра в разработке", show_alert=True)
        return

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ОБРАБОТЧИК ИГРОВОЙ ЛОГИКИ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1] # bask, foot, dice
    choice = data[2] # goal, miss, 1, 2, even...
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    win = False
    result_text = ""
    coef = 1.0

    # ЛОГИКА БАСКЕТБОЛА
    if game_type == "bask":
        res = random.choice(["goal", "miss"])
        win = (res == choice)
        coef = 1.6 if choice == "goal" else 2.4
        result_text = "🏀 Мяч в корзине! Чистый гол!" if res == "goal" else "🗑 Эх, мяч ударился об кольцо и вылетел..."

    # ЛОГИКА ФУТБОЛА
    elif game_type == "foot":
        res = random.choice(["goal", "miss"])
        win = (res == choice)
        coef = 1.6 if choice == "goal" else 2.4
        result_text = "⚽ ГООООЛ!" if res == "goal" else "🥅 Увы, мяч пролетел мимо ворот."

    # ЛОГИКА КУБИКА
    elif game_type == "dice":
        res = random.randint(1, 6)
        if choice.isdigit() and int(choice) == res: 
            win = True
            coef = 5.8
        elif choice == "even" and res % 2 == 0: 
            win = True
            coef = 1.94
        elif choice == "odd" and res % 2 != 0: 
            win = True
            coef = 1.94
        result_text = f"🎲 Выпало число: {res}"

    # Итоги
    if win:
        profit = round(user_data["bet"] * coef, 2)
        user_data["balance"] += (profit - user_data["bet"])
        await call.message.answer(f"🎉 {result_text}\nВы выиграли {profit} mc! 💰")
    else:
        user_data["balance"] -= user_data["bet"]
        await call.message.answer(f"📉 {result_text}\nВы проиграли свою ставку. 😢")
    
    await call.answer()
    # Возвращаемся в главное меню через пару секунд
    await cmd_start(call.message)

# --- НАЗАД ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(
        f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", 
        reply_markup=main_kb()
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
