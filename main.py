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
        text = f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎳 Бросок", callback_data="play_bowl_anim")], btn_back]
    elif game == "slots":
        text = f"Рамиль\n🎰 **Барабан · испытай удачу!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="play_slots_anim")], btn_back]
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · кидай мяч!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🏀 Бросок", callback_data="play_bask_anim")], btn_back]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · бей по воротам!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="⚽ Удар", callback_data="play_foot_anim")], btn_back]
    elif game == "darts":
        text = f"Рамиль\n🎯 **Дартс · целься в центр!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎯 Бросок", callback_data="play_dart_anim")], btn_back]
    elif game == "dice":
        text = f"Рамиль\n🎲 **Кубик · испытай удачу!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎲 Бросить", callback_data="play_dice_anim")], btn_back]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА С АНИМАЦИЕЙ ЭМОДЗИ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_with_anim(call: types.CallbackQuery):
    game_type = call.data.split("_")[1]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    # Соответствие типов игр эмодзи Telegram
    emojis = {
        "bowl": " bowling",
        "slots": "🎰",
        "bask": "🏀",
        "foot": "⚽",
        "dart": "🎯",
        "dice": "🎲"
    }
    
    # Отправляем анимированный эмодзи
    msg = await call.message.answer_dice(emoji=emojis.get(game_type, "🎲"))
    user_data["balance"] -= user_data["bet"]
    
    # Ждем завершения анимации
    await asyncio.sleep(4)
    
    value = msg.dice.value
    win = False
    coef = 0.0

    # Определение выигрыша по значению анимации
    if game_type == "dice":
        if value >= 4: win, coef = True, 1.94
    elif game_type == "foot" or game_type == "bask":
        if value >= 3: win, coef = True, 1.6
    elif game_type == "bowl":
        if value == 6: win, coef = True, 5.8
    elif game_type == "dart":
        if value == 6: win, coef = True, 5.8
    elif game_type == "slots":
        if value in [1, 22, 43, 64]: win, coef = True, 10.0

    if win:
        reward = round(user_data["bet"] * coef, 2)
        user_data["balance"] += reward
        await call.message.answer(f"🎉 Победил! Выигрыш: {reward} mc\n💰 Баланс: {user_data['balance']} mc")
    else:
        await call.message.answer(f"📉 Проигрыш! Баланс: {user_data['balance']} mc")

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
