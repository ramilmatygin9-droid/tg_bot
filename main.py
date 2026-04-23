import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 

bot = Bot(token=GAME_TOKEN)
dp = Dispatcher()

user_data = {"balance": 1000, "bet": 10}
DOTS = "· · · · · · · · · · · · · · · · ·"

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

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_back = InlineKeyboardButton(text="◀️ назад", callback_data="to_main")
    
    # --- КУБИК (КАК НА СКРИНШОТЕ) ---
    if game == "dice":
        text = f"Рамиль\n🍀 **Кубик · выбери режим!**\n{DOTS}\n💸 **Ставка: {user_data['bet']} mс**"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
            [InlineKeyboardButton(text="＝ Равно 3 x5.8", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
            [btn_back]
        ]
    
    # --- БОУЛИНГ (КАК НА СКРИНШОТЕ) ---
    elif game == "bowling":
        text = (f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 **Ставка: {user_data['bet']} mс**\n\n"
                f"🔰 **Коэффициенты:**\n"
                f"┕ 1️⃣ - 5️⃣ кегли (x5.8) ❞\n"
                f"┕ 🎳 Страйк (x5.8)\n"
                f"┕ 😟 Мимо (x5.8)")
        kb = [
            [InlineKeyboardButton(text="1 кегля", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_0")],
            [btn_back]
        ]
    
    # --- ОСТАЛЬНЫЕ ИГРЫ ---
    elif game == "mines":
        text = f"Рамиль\n💣 **Мины**\n{DOTS}\n💸 Ставка: {user_data['bet']} mc"
        kb = [[InlineKeyboardButton(text="1", callback_data="play_mines_1"), InlineKeyboardButton(text="3", callback_data="play_mines_3")], [btn_back]]
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол**\n{DOTS}\n💸 Ставка: {user_data['bet']} mc"
        kb = [[InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="play_bask_anim")], [btn_back]]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол**\n{DOTS}\n💸 Ставка: {user_data['bet']} mc"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_anim")], [btn_back]]
    elif game == "darts":
        text = f"Рамиль\n🎯 **Дартс**\n{DOTS}\n💸 Ставка: {user_data['bet']} mc"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_anim")], [btn_back]]
    elif game == "slots":
        text = f"Рамиль\n🎰 **Слоты**\n{DOTS}\n💸 Ставка: {user_data['bet']} mc"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="play_slots_anim")], [btn_back]]
    else: return

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    game_type = call.data.split("_")[1]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно mc!", show_alert=True)
        return

    emoji_map = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲", "slots": "🎰"}
    
    if game_type in emoji_map:
        user_data["balance"] -= user_data["bet"]
        msg = await call.message.answer_dice(emoji=emoji_map[game_type])
        await asyncio.sleep(4)
        
        val = msg.dice.value
        win = False
        # Упрощенная проверка для примера (можно расширить под каждую кнопку)
        if val >= 4: win = True
        
        if win:
            user_data["balance"] += user_data["bet"] * 2
            await call.message.answer(f"🎉 Выигрыш! Баланс: {user_data['balance']} mc")
        else:
            await call.message.answer(f"📉 Проигрыш! Баланс: {user_data['balance']} mc")
    
    await cmd_start(call.message)

@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
