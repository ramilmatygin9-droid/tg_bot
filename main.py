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

# Данные (в реальности тут должна быть БД)
user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}

DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

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
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"💸 Ставка: **{user_data['bet']} руб.**\n\n"
        f"👇 *Выбери игру и начинай!*"
    )
    await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- БЫСТРЫЕ ИГРЫ (МЕНЮ) ---
@dp.callback_query(F.data == "fast")
async def fast_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Краш", callback_data="prep_crash")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await call.message.edit_text("🚀 **Выберите быструю игру:**", reply_markup=kb, parse_mode="Markdown")

# --- ИСПРАВЛЕННАЯ ЛОГИКА ИГРЫ КРАШ ---

# Хранилище активных полетов {user_id: True/False}
active_flights = {}

@dp.callback_query(F.data == "prep_crash")
async def prep_crash(call: types.CallbackQuery):
    text = (
        f"🚀 **Краш (Ракета)**\n\n"
        f"Успей забрать выигрыш, пока ракета не улетела!\n"
        f"{LINE}\n"
        f"💸 Ставка: **{user_data['bet']} руб.**"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛫 Взлёт!", callback_data="start_crash")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="fast")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "start_crash")
async def start_crash(call: types.CallbackQuery):
    uid = call.from_user.id
    
    # Проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    # Списываем ставку
    user_data["balance"] -= user_data["bet"]
    
    # Генерируем точку взрыва (от x1.1 до x4.0)
    crash_point = round(random.uniform(1.1, 4.0), 2)
    current_coef = 1.0
    msg = call.message
    
    # Помечаем, что полет активен
    active_flights[uid] = True
    
    # Цикл полета
    for _ in range(40): # Максимум 40 шагов (до x5.0)
        # Если пользователь нажал "ЗАБРАТЬ", прерываем цикл
        if not active_flights.get(uid):
            return

        # Проверка на взрыв
        if current_coef >= crash_point:
            active_flights[uid] = False # Полет окончен
            await msg.edit_text(
                f"💥 **РАКЕТА ВЗОРВАЛАСЬ!**\nКоэффициент: **x{crash_point}**\n\n❌ Вы проиграли {user_data['bet']} руб.", 
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Еще раз", callback_data="prep_crash")]]),
                parse_mode="Markdown"
            )
            return
        
        current_coef = round(current_coef + 0.1, 1)
        
        # Кнопка ЗАБРАТЬ динамически обновляется
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"💰 ЗАБРАТЬ x{current_coef}", callback_data=f"cashout_{current_coef}")
        ]])
        
        try:
            await msg.edit_text(
                f"🚀 **Ракета летит...**\n\nМножитель: **x{current_coef}**", 
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except: 
            # Если сообщение не изменилось (Telegram error), просто пропускаем шаг
            pass
            
        await asyncio.sleep(0.6) # Скорость полета

@dp.callback_query(F.data.startswith("cashout_"))
async def crash_cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    
    # Если ракета уже взорвалась, забрать нельзя
    if not active_flights.get(uid):
        await call.answer("❌ Слишком поздно! Ракета взорвалась.", show_alert=True)
        return

    # Останавливаем полет
    active_flights[uid] = False
    
    # Считаем выигрыш
    coef_str = call.data.split("_")[1]
    coef = float(coef_str)
    win_amount = int(user_data['bet'] * coef)
    
    # Начисляем баланс
    user_data["balance"] += win_amount
    
    await call.message.edit_text(
        f"🥳 **ВЫ УСПЕЛИ!**\n\n"
        f"💰 Ваш выигрыш: **{win_amount} руб.**\n"
        f"Множитель: **x{coef_str}**\n\n"
        f"💳 Новый баланс: {user_data['balance']} руб.", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")]]),
        parse_mode="Markdown"
    )

# --- МЕНЮ ИГР (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    if game == "crash": return # Обработано выше в разделе Быстрые
    
    header = f"**{call.from_user.first_name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    text = ""

    if game == "dice":
        text = f"🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
            [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="bet_dice_eq3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_dice_big"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_dice_small")]
        ]
    elif game == "bowling":
        text = f"🎳 **Боулинг · выбери исход!**\n{footer}\n\n📈 **Коэффициенты:**\n┕ 1-5 кегли (x5.8)\n┕ 🎳 Страйк (x5.8)\n┕ 😟 Мимо (x5.8)"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_bowling_3")],
              [InlineKeyboardButton(text="4 кегли", callback_data="bet_bowling_4"), InlineKeyboardButton(text="5 кегель", callback_data="bet_bowling_5")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]]
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")], [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
    elif game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_darts_miss")]]
    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ ---
@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type, choice = data[1], data[2]
    await call.message.delete()
    
    emoji = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}[game_type]
    msg = await bot.send_dice(call.message.chat.id, emoji=emoji)
    await asyncio.sleep(4)
    val = msg.dice.value
    win, coef = False, 0.0

    if game_type == "dice":
        if choice == "even": win, coef = (val % 2 == 0), 1.94
        elif choice == "odd": win, coef = (val % 2 != 0), 1.94
        elif choice == "eq3": win, coef = (val == 3), 5.8
        elif choice == "big": win, coef = (val > 3), 1.94
        elif choice == "small": win, coef = (val < 3), 2.9
        elif choice.startswith("v"): win, coef = (val == int(choice[1])), 5.8
    elif game_type == "bowling":
        if choice == "miss": win = (val == 1)
        elif choice == "strike": win = (val == 6)
        elif choice.isdigit(): win = (val == int(choice))
        coef = 5.8
    elif game_type == "football":
        is_goal = (val >= 3)
        win, coef = (choice == "goal" and is_goal) or (choice == "miss" and not is_goal), (1.6 if choice == "goal" else 2.4)
    elif game_type == "basketball":
        is_goal = (val >= 4)
        win, coef = (choice == "goal" and is_goal) or (choice == "miss" and not is_goal), (1.6 if choice == "goal" else 2.4)
    elif game_type == "darts":
        if choice == "center": win, coef = (val == 6), 5.8
        elif choice == "red": win, coef = (val in [4, 5]), 1.94
        elif choice == "white": win, coef = (val in [2, 3]), 2.9
        elif choice == "miss": win, coef = (val == 1), 5.8
    elif game_type == "slots":
        win, coef = (val in [1, 22, 43, 64]), 10.0

    res_text = f"**{call.from_user.first_name}**\n{'🥳 **Победа!**' if win else '❌ **Проигрыш**'}\n{LINE}\n💰 Выигрыш: {int(user_data['bet'] * coef) if win else 0} руб.\n🎲 Результат: {val}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"prep_{game_type}"), InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")]])
    await msg.reply(res_text, reply_markup=kb, parse_mode="Markdown")

# --- СИСТЕМНЫЕ ФУНКЦИИ ---
@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = (f"👤 **{call.from_user.first_name}** | ID: `{call.from_user.id}`\n"
            f"🎖 Ваш уровень: **{user_data['level']}**\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n{LINE}\nУдачи!")
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: **{user_data['balance']} руб.**\n💸 Ставка: **{user_data['bet']} руб.**\n\n👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "withdraw")
async def withdraw(call: types.CallbackQuery):
    await call.answer("💳 Раздел в разработке!", show_alert=True)

@dp.callback_query(F.data == "ask_help")
async def ask_help(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Опишите вашу проблему:")
    await call.answer()

@dp.message()
async def handle_msg(message: types.Message):
    if message.bot.token == GAME_TOKEN:
        if user_support_state.get(message.from_user.id):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{message.from_user.id}")]])
            await admin_bot.send_message(MY_ID, f"🆘 Тикет от {message.from_user.first_name}:\n{message.text}", reply_markup=kb)
            await message.answer("✅ Отправлено админу.")
            del user_support_state[message.from_user.id]
    elif message.bot.token == ADMIN_TOKEN and message.from_user.id == MY_ID:
        if admin_reply_state.get(MY_ID):
            try:
                await bot.send_message(admin_reply_state[MY_ID], f"✉️ **Ответ админа:**\n\n{message.text}")
                await message.answer("✅ Ответ доставлен.")
            except: await message.answer("❌ Ошибка.")
            del admin_reply_state[MY_ID]

@dp.callback_query(F.data.startswith("adm_reply_"))
async def adm_reply(call: types.CallbackQuery):
    admin_reply_state[MY_ID] = call.data.split("_")[2]
    await call.message.answer("Пиши ответ:")
    await call.answer()

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
