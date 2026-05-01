import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Имитация БД
user_data = {"balance": 1000, "bet": 10, "mines_count": 3, "cases": 0}
game_sessions = {} 
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---

# Главное меню
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="Bowling 🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="prep_slots")
        ],
        [
            InlineKeyboardButton(text="📦 Кейсы", callback_data="menu_cases"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")
        ],
        [
            # ТВОЯ ОБНОВЛЕННАЯ ССЫЛКА ЗДЕСЬ
            InlineKeyboardButton(
                text="🕹 ИГРАТЬ В WEB (GLITCH-WIN)", 
                web_app=WebAppInfo(url="https://ramilmatygin9-droid.github.io/GLITCH-WIN/")
            )
        ],
        [
            InlineKeyboardButton(text="📝 Изменить ставку", callback_data="change_bet"),
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance")
        ]
    ])

# Меню режимов
def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="🎡 Рулетка", callback_data="menu_wheel")],
        [InlineKeyboardButton(text="🧱 Башня", callback_data="under_dev"), InlineKeyboardButton(text="Золото ⚜️", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="HiLo ⬇️", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="under_dev"), InlineKeyboardButton(text="Пирамида 🏜", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# Меню рулетки (барабанной)
def wheel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="play_wheel_red")],
        [InlineKeyboardButton(text="⚫ Черное (x2)", callback_data="play_wheel_black")],
        [InlineKeyboardButton(text="🟢 Зеленое (x14)", callback_data="play_wheel_green")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

# Меню кейсов
def cases_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Купить кейс (100 m¢)", callback_data="buy_case")],
        [InlineKeyboardButton(text="🔥 Открыть кейс", callback_data="open_case")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- ЛОГИКА ИГР ---

# Рулетка
@dp.callback_query(F.data == "menu_wheel")
async def wheel_menu(call: types.CallbackQuery):
    text = (f"🎡 **БАРАБАННАЯ РУЛЕТКА**\n{DOTS}\n"
            f"💰 Баланс: {user_data['balance']} m¢\n"
            f"💸 Ставка: {user_data['bet']} m¢\n\n"
            f"Выбери цвет на барабане:")
    await call.message.edit_text(text, reply_markup=wheel_kb())

@dp.callback_query(F.data.startswith("play_wheel_"))
async def wheel_play(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    
    choice = call.data.split("_")[2]
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    msg = await call.message.edit_text("🎡 *Крутим барабан...* 🌀")
    await asyncio.sleep(2)
    
    res_val = random.randint(0, 14)
    if res_val == 0: res_color = "green"
    elif res_val % 2 == 0: res_color = "red"
    else: res_color = "black"
    
    colors_icons = {"red": "🔴", "black": "⚫", "green": "🟢"}
    win = choice == res_color
    mult = 14 if res_color == "green" else 2
    
    if win:
        win_amt = bet * mult
        user_data["balance"] += win_amt
        res_text = f"✅ ПОБЕДА! Выпало {colors_icons[res_color]}\n💰 +{win_amt} m¢"
    else:
        res_text = f"❌ ПРОИГРЫШ! Выпало {colors_icons[res_color]}\n💸 -{bet} m¢"
        
    await msg.edit_text(f"🎡 **РЕЗУЛЬТАТ РУЛЕТКИ**\n{DOTS}\n{res_text}\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

# Кейсы
@dp.callback_query(F.data == "menu_cases")
async def cases_menu(call: types.CallbackQuery):
    text = (f"📦 **МАГАЗИН КЕЙСОВ**\n{DOTS}\n"
            f"💰 Баланс: {user_data['balance']} m¢\n"
            f"📦 В наличии: {user_data['cases']} шт.\n\n"
            f"Из кейса может выпасть от 10 до 500 m¢!")
    await call.message.edit_text(text, reply_markup=cases_kb())

@dp.callback_query(F.data == "buy_case")
async def buy_case(call: types.CallbackQuery):
    if user_data["balance"] < 100:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    user_data["balance"] -= 100
    user_data["cases"] += 1
    await call.answer("📦 Кейс куплен!")
    await cases_menu(call)

@dp.callback_query(F.data == "open_case")
async def open_case(call: types.CallbackQuery):
    if user_data["cases"] <= 0:
        await call.answer("❌ У тебя нет кейсов!", show_alert=True)
        return
    
    user_data["cases"] -= 1
    msg = await call.message.edit_text("📦 *Трясем кейс...*")
    await asyncio.sleep(1)
    await msg.edit_text("📦 *Открываем замок...*")
    await asyncio.sleep(1)
    
    win = random.choices([20, 50, 100, 250, 500], weights=[50, 30, 15, 4, 1])[0]
    user_data["balance"] += win
    
    await msg.edit_text(f"🎁 **КЕЙС ОТКРЫТ!**\n{DOTS}\n✨ Твой выигрыш: {win} m¢\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

# Баланс и режимы
@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    await call.answer(f"💰 Баланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=modes_kb())

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    bet = user_data['bet']
    btn_back = InlineKeyboardButton(text="◀️ назад", callback_data="to_main")
    
    if game == "basketball":
        text = f"Рамиль\n🏀 *Баскетбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_bask_goal")],
              [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_bask_miss")], [btn_back]]
    elif game == "football":
        text = f"Рамиль\n⚽ *Футбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")], [btn_back]]
    elif game == "darts":
        text = (f"Рамиль\n🎯 *Дартс · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 🔴 Красное (x1.94) ❞\n┕ ⚪️ Белое (x2.9)\n┕ 🎯 Центр (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_dart_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_dart_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_dart_miss")], [btn_back]]
    elif game == "bowling":
        text = (f"Рамиль\n🎳 *Боулинг · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 1️⃣ - 5️⃣ кегли (x5.8) ❞\n┕ 🎳 Страйк (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="1 кегла", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
              [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_0")], [btn_back]]
    elif game == "dice":
        text = f"Рамиль\n🍀 *Кубик · выбери режим!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
              [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
              [InlineKeyboardButton(text="＝ Равно 3 x5.8", callback_data="play_dice_equal3")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
              [btn_back]]
    elif game == "slots":
        text = f"Рамиль\n🎰 *Слоты · крути барабаны!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="🎰 КРУТИТЬ", callback_data="play_slots_spin")], [btn_back]]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    data = call.data.split("_")
    game_code = data[1]
    if game_code == "wheel": return
    selection = data[2] if len(data) > 2 else "spin"
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    if game_code == "slots":
        symbols = ["🍒", "🍊", "🍋", "🍉", "🔔", "💎", "7️⃣"]
        reel1, reel2, reel3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        multiplier = 0
        if reel1 == reel2 == reel3:
            multiplier = 10 if reel1 == "7️⃣" else 5
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 2
        
        if multiplier > 0:
            win_amount = int(bet * multiplier)
            user_data["balance"] += win_amount
            result_text = f"✅ ПОБЕДА! x{multiplier} = {win_amount} m¢"
        else:
            result_text = f"❌ ПРОИГРЫШ! -{bet} m¢"
        
        await call.message.answer(f"🎰 **СЛОТЫ**\n{DOTS}\n[ {reel1} ] [ {reel2} ] [ {reel3} ]\n{DOTS}\n{result_text}\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())
        await call.message.delete()
        return

    emojis = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲"}
    dice_msg = await call.message.answer_dice(emoji=emojis.get(game_code, "🎲"))
    await asyncio.sleep(3)
    val = dice_msg.dice.value
    win = False
    multiplier = 0
    
    if game_code == "bask":
        win = (selection == "goal" and val >= 4) or (selection == "miss" and val <= 3)
        multiplier = 2.4 if selection == "goal" else 1.6
    elif game_code == "foot":
        win = (selection == "goal" and val >= 3) or (selection == "miss" and val <= 2)
        multiplier = 1.6 if selection == "goal" else 2.4
    elif game_code == "dart":
        if selection == "red": win = val in [2, 3]; multiplier = 1.94
        elif selection == "white": win = val in [4, 5]; multiplier = 2.9
        elif selection == "center": win = val == 6; multiplier = 5.8
        elif selection == "miss": win = val == 1; multiplier = 5.8
    elif game_code == "bowl":
        win = (selection == "6" and val == 6) or (selection == "0" and val == 1) or (selection.isdigit() and val == int(selection))
        multiplier = 5.8
    elif game_code == "dice":
        if selection.isdigit(): win = val == int(selection); multiplier = 5.8
        elif selection == "even": win = val % 2 == 0; multiplier = 1.94
        elif selection == "odd": win = val % 2 != 0; multiplier = 1.94
        elif selection == "high": win = val > 3; multiplier = 1.94
        elif selection == "low": win = val < 3; multiplier = 2.9

    if win:
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        res_text = f"🥳 ПОБЕДА! ✅\n💰 Выигрыш: {win_amount} m¢"
    else:
        res_text = f"😭 ПРОИГРЫШ ❌\n💸 Потеряно: {bet} m¢"
    
    await call.message.answer(f"{res_text}\n🎯 Выпало: {val}\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())
    await call.message.delete()

# --- МИНЫ ---
def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    text = f"Рамиль\n💣 *Мины · выбери мины!*\n{DOTS}\n💸 *Ставка: {user_data['bet']} m¢*"
    await call.message.edit_text(text, reply_markup=mines_start_kb())

@dp.callback_query(F.data == "mines_double")
async def mines_double(call: types.CallbackQuery):
    user_data['bet'] *= 2
    await call.answer(f"💸 Ставка удвоена! Теперь: {user_data['bet']} m¢")
    await mines_menu(call)

@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    user_data["balance"] -= user_data["bet"]
    board = [0]*25
    for idx in random.sample(range(25), m_count): board[idx] = 1
    game_sessions[user_id] = {'board': board, 'bet': user_data['bet'], 'mines': m_count, 'opened': [], 'game_over': False}
    await call.message.edit_text(f"💣 *Мины запущены!*\nМин: {m_count}", reply_markup=get_mines_board_kb(user_id))

def get_mines_board_kb(user_id):
    s = game_sessions.get(user_id)
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            char = "❓"
            if idx in s['opened']: char = "💥" if s['board'][idx] == 1 else "💎"
            row.append(InlineKeyboardButton(text=char, callback_data=f"mopen_{idx}"))
        kb.append(row)
    if not s['game_over']:
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        mult = 1 + (opened_safe * 0.2)
        kb.append([InlineKeyboardButton(text=f"💰 Забрать x{mult:.2f}", callback_data="m_cashout")])
    else:
        kb.append([InlineKeyboardButton(text="🔄 Заново", callback_data=f"setmines_{s['mines']}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data.startswith("mopen_"))
async def mines_step(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(call.from_user.id)
    if not s or s['game_over'] or idx in s['opened']: return
    s['opened'].append(idx)
    if s['board'][idx] == 1: s['game_over'] = True
    await call.message.edit_reply_markup(reply_markup=get_mines_board_kb(call.from_user.id))

@dp.callback_query(F.data == "m_cashout")
async def mines_cashout(call: types.CallbackQuery):
    s = game_sessions.get(call.from_user.id)
    if not s: return
    opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
    win = int(s['bet'] * (1 + opened_safe * 0.2))
    user_data["balance"] += win
    await call.message.edit_text(f"✅ Забрал {win} m¢!", reply_markup=main_kb())

# --- ОБЩЕЕ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    bets = [10, 25, 50, 100, 250, 500, 1000]
    user_data['bet'] = bets[(bets.index(user_data['bet']) + 1) % len(bets)]
    await call.answer(f"💸 Ставка: {user_data['bet']} m¢")
    await back_to_main(call)

@dp.callback_query(F.data == "under_dev")
async def dev(call: types.CallbackQuery):
    await call.answer("🚧 В разработке", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
