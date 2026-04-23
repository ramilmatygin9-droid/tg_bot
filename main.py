import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
ADMIN_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
MY_ID = 8462392581 

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}
active_flights = {}

DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

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
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")]
    ])

# --- РАЗДЕЛ РЕЖИМЫ (ТУТ КРАШ) ---
@dp.callback_query(F.data == "modes")
async def modes_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Краш (Бомбы)", callback_data="prep_crash")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await call.message.edit_text("💣 **Выбери режим:**", reply_markup=kb, parse_mode="Markdown")

# --- ЛОГИКА КРАША ---
@dp.callback_query(F.data == "prep_crash")
async def prep_crash(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛫 Взлёт!", callback_data="start_crash")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="modes")]
    ])
    await call.message.edit_text(f"🚀 **Краш (Угадай где нет бомбы)**\n{LINE}\n💸 Ставка: {user_data['bet']} руб.", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "start_crash")
async def start_crash(call: types.CallbackQuery):
    uid = call.from_user.id
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user_data["balance"] -= user_data["bet"]
    crash_point = round(random.uniform(1.2, 4.5), 2)
    current_coef, active_flights[uid] = 1.0, True
    msg = call.message

    for _ in range(50):
        if not active_flights.get(uid): return
        if current_coef >= crash_point:
            active_flights[uid] = False
            await msg.edit_text(f"💥 **БОМБА ВЗОРВАЛАСЬ! x{crash_point}**\n❌ Вы проиграли {user_data['bet']} руб.", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Снова", callback_data="prep_crash")]]))
            return
        
        current_coef = round(current_coef + 0.1, 1)
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"💰 ЗАБРАТЬ x{current_coef}", callback_data=f"cashout_{current_coef}")]])
        try: await msg.edit_text(f"🚀 Ракета летит: **x{current_coef}**", reply_markup=kb)
        except: pass
        await asyncio.sleep(0.6)

@dp.callback_query(F.data.startswith("cashout_"))
async def crash_cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    if not active_flights.get(uid): return
    active_flights[uid] = False
    coef = float(call.data.split("_")[1])
    win = int(user_data['bet'] * coef)
    user_data["balance"] += win
    await call.message.edit_text(f"🥳 **УСПЕХ!**\n💰 Вы забрали: **{win} руб.**\nМножитель: **x{coef}**", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Меню", callback_data="to_main")]]))

# --- ЛОГИКА МЯЧЕЙ, ДАРТСА И Т.Д. (ТВОЕ СТАРОЕ) ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    if game == "crash": return
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    text = f"Игра: {game}\n{footer}"

    if game == "dice":
        kb = [[InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
              [InlineKeyboardButton(text="⚖️ Чёт", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечёт", callback_data="bet_dice_odd")]]
    elif game == "bowling":
        kb = [[InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]]
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол", callback_data="bet_football_goal")], [InlineKeyboardButton(text="🥅 Мимо", callback_data="bet_football_miss")]]
    elif game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попадание", callback_data="bet_basketball_goal")], [InlineKeyboardButton(text="🗑 Мимо", callback_data="bet_basketball_miss")]]
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_darts_miss")]]
    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]: return
    data = call.data.split("_")
    game_type, choice = data[1], data[2]
    await call.message.delete()
    
    emoji_map = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}
    msg = await bot.send_dice(call.message.chat.id, emoji=emoji_map[game_type])
    await asyncio.sleep(4)
    val, win, coef = msg.dice.value, False, 1.94

    if game_type == "dice": win = (choice == "even" and val % 2 == 0) or (choice == "odd" and val % 2 != 0)
    elif game_type == "football": win = (choice == "goal" and val >= 3) or (choice == "miss" and val < 3)
    elif game_type == "bowling": win = (choice == "strike" and val == 6) or (choice == "miss" and val == 1)
    elif game_type == "slots": win, coef = (val in [1, 22, 43, 64]), 10.0
    # Остальная логика дартс/баскет аналогично твоим коэф.

    if win: user_data["balance"] += int(user_data["bet"] * coef) - user_data["bet"]
    else: user_data["balance"] -= user_data["bet"]

    await msg.reply(f"💰 Баланс: {user_data['balance']} руб.\nРезультат: {val}", 
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Еще раз", callback_data=f"prep_{game_type}"), InlineKeyboardButton(text="◀️ Меню", callback_data="to_main")]]))

# --- ПОДДЕРЖКА (ТВОЕ) ---
@dp.callback_query(F.data == "ask_help")
async def ask_help(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Напиши проблему:")

@dp.message()
async def handle_msg(message: types.Message):
    if message.bot.token == GAME_TOKEN and user_support_state.get(message.from_user.id):
        await admin_bot.send_message(MY_ID, f"🆘 От {message.from_user.id}:\n{message.text}")
        await message.answer("✅ Отправлено."); del user_support_state[message.from_user.id]

# --- ОБЩЕЕ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.bot.token == GAME_TOKEN:
        await message.answer(f"🎮 **ИГРАЕМ!**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **МЕНЮ**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb(), parse_mode="Markdown")

async def main(): await dp.start_polling(bot, admin_bot)
if __name__ == "__main__": asyncio.run(main())
