import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 
ADMIN_TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"

bot = Bot(token=GAME_TOKEN)
dp = Dispatcher()

# Данные пользователя
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
    
    if game == "mines":
        text = f"Рамиль\n💣 **Мины · выбери количество мин!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
              [InlineKeyboardButton(text="1", callback_data="play_mines_1"), InlineKeyboardButton(text="2", callback_data="play_mines_2"), InlineKeyboardButton(text="3", callback_data="play_mines_3")],
              [InlineKeyboardButton(text="4", callback_data="play_mines_4"), InlineKeyboardButton(text="5", callback_data="play_mines_5"), InlineKeyboardButton(text="6", callback_data="play_mines_6")],
              btn_back]
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="play_bask_anim")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="play_bask_anim")], btn_back]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_anim")], [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_anim")], btn_back]
    elif game == "darts":
        text = f"Рамиль\n🎯 **Дартс · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_anim"), InlineKeyboardButton(text="⚪ Белое", callback_data="play_dart_anim")], 
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_dart_anim"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_dart_anim")], btn_back]
    elif game == "bowling":
        text = f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="play_bowl_anim"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_anim")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_anim"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_anim")], btn_back]
    elif game == "dice":
        text = f"Рамиль\n🎲 **Кубик · выбери режим!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="1", callback_data="play_dice_anim"), InlineKeyboardButton(text="2", callback_data="play_dice_anim"), InlineKeyboardButton(text="3", callback_data="play_dice_anim")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_anim"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_anim")], btn_back]
    elif game == "slots":
        text = f"Рамиль\n🎰 **Барабан · испытай удачу!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="play_slots_anim")], btn_back]
    else: return

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ИГР ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    game_type = call.data.split("_")[1]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно mc!", show_alert=True)
        return

    if game_type == "mines":
        # Логика Мины
        if random.random() > 0.4:
            profit = round(user_data["bet"] * 1.5, 2)
            user_data["balance"] += profit
            await call.message.answer(f"💎 Вы нашли алмаз! +{profit} mc")
        else:
            user_data["balance"] -= user_data["bet"]
            await call.message.answer(f"💣 БАБАХ! Вы подорвались на мине.")
    else:
        # Логика Анимаций
        emoji_map = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲", "slots": "🎰"}
        user_data["balance"] -= user_data["bet"]
        msg = await call.message.answer_dice(emoji=emoji_map.get(game_type, "🎲"))
        await asyncio.sleep(4)
        
        val = msg.dice.value
        win = False
        if (game_type == "dice" and val >= 4) or (game_type in ["foot", "bask"] and val >= 3) or (val == 6) or (game_type == "slots" and val in [1, 22, 43, 64]):
            win = True
        
        if win:
            user_data["balance"] += user_data["bet"] * 2
            await call.message.answer(f"🎉 Победил! Баланс: {user_data['balance']} mc")
        else:
            await call.message.answer(f"📉 Проиграл! Баланс: {user_data['balance']} mc")

    await cmd_start(call.message)

@dp.message(Command("start"))
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
