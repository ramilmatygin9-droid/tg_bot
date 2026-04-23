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

user_data = {"balance": 1000, "bet": 10}
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- ГЛАВНОЕ МЕНЮ ---
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

# --- ПОДГОТОВКА ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_back = [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    
    if game == "bowling":
        text = f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс\n\n🔰 **Коэффициенты:**\n1 - 5 кегли (x5.8)\n🎳 Страйк (x5.8)\n😟 Мимо (x5.8)"
        kb = [
            [InlineKeyboardButton(text="1 кегля", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_miss")],
            btn_back
        ]
    elif game == "slots":
        text = f"Рамиль\n🎰 **Барабан · испытай удачу!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="play_slots_spin")], btn_back]
    # Логика для остальных (футбол, дартс и т.д. остается как была)
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="play_bask_goal")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="play_bask_miss")], btn_back]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ИГР (БОУЛИНГ И БАРАБАН) ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    choice = data[2]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    win = False
    coef = 5.8
    result_text = ""

    if game_type == "bowl":
        # Генерация результата: 1, 3, 4, 5 кеглей, strike (6) или miss (0)
        res_val = random.choice(["1", "3", "4", "5", "strike", "miss"])
        win = (choice == res_val)
        names = {"1": "1 кеглю", "3": "3 кегли", "4": "4 кегли", "5": "5 кеглей", "strike": "СТРАЙК 🎳", "miss": "МИМО 😟"}
        result_text = f"Результат броска: {names[res_val]}"

    elif game_type == "slots":
        # Используем встроенный кубик Телеграма для слотов
        msg = await call.message.answer_dice(emoji="🎰")
        # Значения 1, 22, 43, 64 - это джекпоты в слотах tg
        if msg.dice.value in [1, 22, 43, 64]:
            win = True
            coef = 10.0
            result_text = "🎰 ДЖЕКПОТ!"
        else:
            win = False
            result_text = "🎰 Ничего не выпало..."

    if win:
        profit = round(user_data["bet"] * coef, 2)
        user_data["balance"] += (profit - user_data["bet"])
        await call.message.answer(f"🎉 {result_text}\nВы выиграли {profit} mc!")
    else:
        user_data["balance"] -= user_data["bet"]
        await call.message.answer(f"📉 {result_text}\nПроигрыш. Баланс: {user_data['balance']} mc")
    
    await call.answer()
    await cmd_start(call.message)

@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ИГРОВОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
