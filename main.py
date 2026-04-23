import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных пользователей (в памяти)
users = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_header(user: types.User):
    uid = user.id
    if uid not in users:
        users[uid] = {"balance": 1000, "lvl": 1}
    u = users[uid]
    return (f"👤 {user.first_name} | ID: `{uid}`\n"
            f"🏆 Ваш уровень: {u['lvl']}\n"
            f"💰 Баланс: {u['balance']} m¢\n"
            f"────────────────")

def main_menu_kb():
    kb = [
        [InlineKeyboardButton(text="🏀", callback_data="game_basketball"),
         InlineKeyboardButton(text="⚽", callback_data="game_football"),
         InlineKeyboardButton(text="🎯", callback_data="game_darts"),
         InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
         InlineKeyboardButton(text="🎲", callback_data="game_dice"),
         InlineKeyboardButton(text="🎰", callback_data="game_slots")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="open_fast"),
         InlineKeyboardButton(text="Режимы 💣", callback_data="open_modes")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ГЛАВНЫЕ КОМАНДЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"{get_header(message.from_user)}\nВыбирай игру в меню ниже:", 
                         reply_markup=main_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user)}\nВыбирай игру в меню ниже:", 
                                 reply_markup=main_menu_kb(), parse_mode="Markdown")

# --- РАЗДЕЛ "БЫСТРЫЕ" (КРАШ, МИНЫ) ---

@dp.callback_query(F.data == "open_fast")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🚀 Краш", callback_data="fast_crash"),
         InlineKeyboardButton(text="💣 Мины", callback_data="fast_mines")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="fast_roulette"),
         InlineKeyboardButton(text="💰 Монетка", callback_data="fast_coin")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Быстрые игры**", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- МЕХАНИКА МИНЫ (5x5) ---
active_mines = {}

def get_mines_grid(uid, show_mines=False):
    game = active_mines[uid]
    kb = []
    for y in range(5):
        row = []
        for x in range(5):
            pos = f"{x}_{y}"
            if pos in game['open']:
                text = "💥" if pos in game['mines'] else "💎"
            elif show_mines and pos in game['mines']:
                text = "💣"
            else:
                text = "🔹"
            row.append(InlineKeyboardButton(text=text, callback_data=f"click_m_{pos}"))
        kb.append(row)
    
    if not show_mines:
        kb.append([InlineKeyboardButton(text=f"📥 Забрать {game['cur_win']} m¢", callback_data="mines_cashout")])
    kb.append([InlineKeyboardButton(text="⬅️ Выход", callback_data="open_fast")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data == "fast_mines")
async def start_mines(call: types.CallbackQuery):
    uid = call.from_user.id
    # Генерируем 3 случайные мины
    mines = random.sample([f"{x}_{y}" for x in range(5) for y in range(5)], 3)
    active_mines[uid] = {"mines": mines, "open": [], "cur_win": 10}
    await call.message.edit_text(f"{get_header(call.from_user)}\n💣 **Мины**\nНайди алмазы и не взорвись!", 
                                 reply_markup=get_mines_grid(uid), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("click_m_"))
async def process_mine_click(call: types.CallbackQuery):
    uid = call.from_user.id
    pos = call.data.replace("click_m_", "")
    game = active_mines.get(uid)
    if not game or pos in game['open']: return

    game['open'].append(pos)
    if pos in game['mines']:
        users[uid]['balance'] -= 10
        await call.message.edit_text(f"{get_header(call.from_user)}\n💥 **БУМ! Вы взорвались!**", 
                                     reply_markup=get_mines_grid(uid, True), parse_mode="Markdown")
        del active_mines[uid]
    else:
        game['cur_win'] = int(game['cur_win'] * 1.45)
        await call.message.edit_reply_markup(reply_markup=get_mines_grid(uid))

@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid in active_mines:
        win = active_mines[uid]['cur_win']
        users[uid]['balance'] += win
        await call.answer(f"💰 Забрали {win} m¢!", show_alert=True)
        del active_mines[uid]
        await back_to_main(call)

# --- МЕХАНИКА КРАШ ---

@dp.callback_query(F.data == "fast_crash")
async def crash_start(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="x1.2", callback_data="bet_cr_1.2"),
         InlineKeyboardButton(text="x2.0", callback_data="bet_cr_2.0"),
         InlineKeyboardButton(text="x5.0", callback_data="bet_cr_5.0")],
        [InlineKeyboardButton(text="x10.0", callback_data="bet_cr_10.0"),
         InlineKeyboardButton(text="x50.0", callback_data="bet_cr_50.0"),
         InlineKeyboardButton(text="x100.0", callback_data="bet_cr_100.0")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="open_fast")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Краш**\nВыбери множитель для ставки:", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bet_cr_"))
async def play_crash(call: types.CallbackQuery):
    target = float(call.data.split("_")[2])
    crash_point = round(random.uniform(1.0, 15.0), 2)
    
    msg = await call.message.answer("🚀 Ракета пошла на взлет...")
    await asyncio.sleep(1)
    
    if crash_point >= target:
        users[call.from_user.id]['balance'] += int(10 * target)
        await msg.edit_text(f"🥳 **Победа!**\n🚀 Ракета долетела до x{crash_point}\n💰 Выигрыш: {int(10 * target)} m¢")
    else:
        users[call.from_user.id]['balance'] -= 10
        await msg.edit_text(f"💥 **КРАШ!**\n📉 Взрыв на x{crash_point}\n🎯 Твоя цель была x{target}")

# --- КАЗИНО ИГРЫ (DICE) ---

@dp.callback_query(F.data.startswith("game_"))
async def play_dice_games(call: types.CallbackQuery):
    game_type = call.data.split("_")[1]
    emoji_map = {
        "basketball": "🏀", "football": "⚽", "darts": "🎯", 
        "bowling": "🎳", "dice": "🎲", "slots": "🎰"
    }
    emoji = emoji_map.get(game_type, "🎲")
    
    # Анимация дайса
    dice_msg = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5)
    
    # Простая логика выигрыша (4, 5, 6 для спорта)
    is_win = False
    if emoji == "🎰":
        is_win = dice_msg.dice.value in [1, 22, 43, 64] # Выигрышные в слотах
    else:
        is_win = dice_msg.dice.value >= 4
        
    if is_win:
        users[call.from_user.id]['balance'] += 20
        text = "🥳 **Победа!**"
    else:
        users[call.from_user.id]['balance'] -= 10
        text = "❌ **Проигрыш!**"
        
    await call.message.answer(f"{get_header(call.from_user)}\n{text}\nРезультат: {dice_msg.dice.value}", 
                              reply_markup=main_menu_kb(), parse_mode="Markdown")

# --- ЗАПУСК ---

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
