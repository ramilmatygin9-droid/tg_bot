import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 

bot = Bot(token=GAME_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# Имитация БД
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
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="prep_mines")
        ],
        [
            InlineKeyboardButton(text="⬇️ 5 💰", callback_data="bet_down"),
            InlineKeyboardButton(text="10 💰", callback_data="bet_reset"),
            InlineKeyboardButton(text="⬆️ 20 💰", callback_data="bet_up")
        ],
        [InlineKeyboardButton(text="Повторить игру 🔄", callback_data="to_main")]
    ])

# --- ОБРАБОТКА КОМАНД (ПЕРВЫЙ ПРИОРИТЕТ) ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

# --- КНОПКИ МЕНЮ ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_back = InlineKeyboardButton(text="◀️ назад", callback_data="to_main")
    bet = user_data['bet']
    
    if game == "dice":
        text = f"Рамиль\n🍀 *Кубик · выбери режим!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
            [InlineKeyboardButton(text="＝ Равно 3 x5.8", callback_data="play_dice_equal3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
            [btn_back]
        ]
    elif game == "bowling":
        text = (f"Рамиль\n🎳 *Боулинг · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 1️⃣ - 5️⃣ кегли (x5.8)\n"
                f"┕ 🎳 Страйк (x5.8)\n"
                f"┕ 😟 Мимо (x5.8)")
        kb = [
            [InlineKeyboardButton(text="1 кегла", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_0")],
            [btn_back]
        ]
    elif game == "darts":
        text = (f"Рамиль\n🎯 *Дартс · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 🔴 Красное (x1.94)\n"
                f"┕ ⚪️ Белое (x2.9)\n"
                f"┕ 🎯 Центр (x5.8)\n"
                f"┕ 😟 Мимо (x5.8)")
        kb = [
            [InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_dart_white")],
            [InlineKeyboardButton(text="🎯 Центр", callback_data="play_dart_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_dart_miss")],
            [btn_back]
        ]
    elif game == "football":
        text = f"Рамиль\n⚽ *Футбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")],
            [btn_back]
        ]
    elif game == "basketball":
        text = f"Рамиль\n🏀 *Баскетбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [
            [InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_bask_goal")],
            [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_bask_miss")],
            [btn_back]
        ]
    else:
        return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ИГРЫ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_code = data[1]
    selection = data[2]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
        
    user_data["balance"] -= user_data["bet"]
    emoji_map = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲", "slots": "🎰"}
    dice_msg = await call.message.answer_dice(emoji=emoji_map[game_code])
    res = dice_msg.dice.value
    
    win, multiplier, result_text = False, 1.0, ""

    if game_code == "bask":
        is_goal = res >= 4
        result_text = "попадание" if is_goal else "мимо"
        if (selection == "goal" and is_goal): win, multiplier = True, 2.4
        elif (selection == "miss" and not is_goal): win, multiplier = True, 1.6
    elif game_code == "foot":
        is_goal = res >= 3
        result_text = "гол" if is_goal else "мимо"
        if (selection == "goal" and is_goal): win, multiplier = True, 1.6
        elif (selection == "miss" and not is_goal): win, multiplier = True, 2.4
    elif game_code == "dice":
        result_text = f"выпало {res}"
        if selection.isdigit() and int(selection) == res: win, multiplier = True, 5.8
        elif selection == "even" and res % 2 == 0: win, multiplier = True, 1.94
        elif selection == "odd" and res % 2 != 0: win, multiplier = True, 1.94
        elif selection == "high" and res > 3: win, multiplier = True, 1.94
        elif selection == "low" and res < 3: win, multiplier = True, 2.9
        elif selection == "equal3" and res == 3: win, multiplier = True, 5.8
    elif game_code == "bowl":
        result_text = f"{res} кегель" if 1 < res < 6 else ("страйк" if res == 6 else "мимо")
        if selection.isdigit() and (int(selection) == res or (int(selection) == 0 and res == 1)): win, multiplier = True, 5.8

    await asyncio.sleep(3.5)
    
    win_amount = int(user_data["bet"] * multiplier) if win else 0
    if win: user_data["balance"] += win_amount
    
    final_text = (f"🥳 *{emoji_map[game_code]} {'Победа!' if win else 'Проигрыш'} {'✅' if win else '❌'}*\n"
                  f"{DOTS}\n💸 *Ставка:* {user_data['bet']} m¢\n🎲 *Выбрано:* {selection}\n"
                  f"💰 *Выигрыш:* x{multiplier if win else 0} / {win_amount} m¢\n"
                  f"{DOTS}\n⚡️ *Итог:* {result_text}")
    await call.message.answer(final_text, reply_markup=main_kb())

# --- УПРАВЛЕНИЕ СТАВКОЙ ---
@dp.callback_query(F.data.startswith("bet_"))
async def change_bet(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    if action == "up": user_data["bet"] += 10
    elif action == "down" and user_data["bet"] > 5: user_data["bet"] -= 5
    elif action == "reset": user_data["bet"] = 10
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢\n🔥 Текущая ставка: {user_data['bet']}", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
