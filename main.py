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

# Имитация базы данных
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

# --- ВЫБОР РЕЖИМА ДАРТС ---
@dp.callback_query(F.data == "prep_darts")
async def prepare_darts(call: types.CallbackQuery):
    text = (
        f"Рамиль\n🎯 **Дартс · выбери исход!**\n{DOTS}\n"
        f"💸 Ставка: {user_data['bet']} mс\n\n"
        f"🔰 **Коэффициенты:**\n"
        f"🔴 Красное (x1.94)\n"
        f"⚪ Белое (x2.9)\n"
        f"🎯 Центр (x5.8)\n"
        f"😟 Мимо (x5.8)"
    )
    kb = [
        [InlineKeyboardButton(text="🔴 Красное", callback_data="play_darts_red"), 
         InlineKeyboardButton(text="⚪ Белое", callback_data="play_darts_white")],
        [InlineKeyboardButton(text="🎯 Центр", callback_data="play_darts_center"), 
         InlineKeyboardButton(text="😟 Мимо", callback_data="play_darts_miss")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ИГРЫ ДАРТС ---
@dp.callback_query(F.data.startswith("play_darts_"))
async def play_darts(call: types.CallbackQuery):
    choice = call.data.split("_")[2] # red, white, center, miss
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно mс для броска!", show_alert=True)
        return

    # Имитация броска (шансы распределены согласно коэффициентам)
    # 1-50: Красное, 51-80: Белое, 81-90: Центр, 91-100: Мимо
    res_roll = random.randint(1, 100)
    if res_roll <= 50: res = "red"
    elif res_roll <= 80: res = "white"
    elif res_roll <= 90: res = "center"
    else: res = "miss"

    win = (choice == res)
    
    # Коэффициенты со скриншота
    coefs = {"red": 1.94, "white": 2.9, "center": 5.8, "miss": 5.8}
    current_coef = coefs[choice]

    if win:
        profit = round(user_data["bet"] * current_coef, 2)
        user_data["balance"] += (profit - user_data["bet"])
        msg = f"🎯 **ПОПАДАНИЕ!**\n{DOTS}\nВы выбрали {choice} и выиграли {profit} mc! 🎉"
    else:
        user_data["balance"] -= user_data["bet"]
        # Красивое описание промаха
        names = {"red": "Красное", "white": "Белое", "center": "Центр", "miss": "Мимо ворот"}
        msg = f"😟 **ПРОМАХ!**\n{DOTS}\nВы ставили на {names[choice]}, но дротик попал в {names[res]}. Ставка потеряна."

    await call.message.answer(f"{msg}\n💰 Баланс: {user_data['balance']} mc")
    await call.answer()
    
    # Сразу предлагаем сыграть еще раз, отправляя меню
    await cmd_start(call.message)

# --- ОБЩИЕ ФУНКЦИИ ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: {user_data['balance']} mс\n💸 Ставка: {user_data['bet']} mс", 
        reply_markup=main_kb()
    )

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
