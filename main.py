import asyncio
import random
import logging
from datetime import datetime
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

# Данные пользователя
user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}
change_bet_state = {}

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
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="prep_mines"), # Новая кнопка
            InlineKeyboardButton(text="Режимы 💣", callback_data="under_dev")
        ],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="under_dev")]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    now = datetime.now().strftime("%H:%M:%S | %d.%m.%Y")
    if message.bot.token == GAME_TOKEN:
        text = (
            f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n"
            f"💸 Ставка: **{user_data['bet']} руб.**\n"
            f"🕒 Время: `{now}`\n\n"
            f"👇 *Выбери игру и начинай!*"
        )
        await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- ЛОГИКА СООБЩЕНИЙ (Поддержка и Ставка) ---
@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    if message.bot.token == GAME_TOKEN:
        if change_bet_state.get(uid):
            if message.text.isdigit():
                user_data["bet"] = int(message.text)
                change_bet_state[uid] = False
                await message.answer(f"✅ Ставка изменена на **{user_data['bet']} руб.**", reply_markup=main_kb())
            return
        if user_support_state.get(uid):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f_adm_reply_{uid})]])
            sms = (f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n{LINE}\n👤 Имя: {message.from_user.first_name}\n"
                   f"🆔 ID: `{uid}`\n{LINE}\n✉️ Текст: {message.text}")
            try:
                await admin_bot.send_message(MY_ID, sms, reply_markup=kb, parse_mode="Markdown")
                await message.answer("✅ Сообщение отправлено!") 
            except:
                await message.answer("❌ Ошибка при отправке. Попробуйте позже.")
            user_support_state[uid] = False
    elif message.bot.token == ADMIN_TOKEN and uid == MY_ID:
        if admin_reply_state.get(MY_ID):
            target = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target, f"✉️ **Ответ техподдержки:**\n\n{message.text}")
                await message.answer(f"✅ Ответ отправлен пользователю `{target}`")
                del admin_reply_state[MY_ID]
            except:
                await message.answer("❌ Ошибка отправки пользователю.")

# --- CALLBACKS (Базовые) ---
@dp.callback_query(F.data == "profile")
async def view_profile(call: types.CallbackQuery):
    text = (
        f"👤 **ВАШ ПРОФИЛЬ**\n{LINE}\n"
        f"🆔 ID: `{call.from_user.id}`\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"💸 Текущая ставка: **{user_data['bet']} руб.**\n"
        f"📈 Уровень: **{user_data['level']}**\n{LINE}"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "under_dev")
async def dev_alert(call: types.CallbackQuery):
    await call.answer("🛠 В разработке...", show_alert=True)

@dp.callback_query(F.data == "change_bet")
async def bet_init(call: types.CallbackQuery):
    change_bet_state[call.from_user.id] = True
    await call.message.answer("✏️ Введите сумму ставки:")
    await call.answer()

@dp.callback_query(F.data == "ask_help")
async def help_init(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Напишите ваш вопрос для поддержки:")
    await call.answer()

# --- РЕЖИМ МИНЫ ---
@dp.callback_query(F.data == "prep_mines")
async def mines_choice(call: types.CallbackQuery):
    header = f"👤 **{call.from_user.first_name}**\n"
    text = f"{header}💣 **МИНЫ**\n{LINE}\nВыбери количество мин на поле (1-24):"
    
    # Кнопки выбора количества мин
    btns = [3, 5, 10, 15, 20, 24]
    kb = []
    row = []
    for b in btns:
        row.append(InlineKeyboardButton(text=str(b), callback_data=f"start_mines_{b}"))
        if len(row) == 3:
            kb.append(row)
            row = []
    kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("start_mines_"))
async def start_mines(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True); return
    
    count = int(call.data.split("_")[2])
    # Генерируем поле 5x5 (всего 25 ячеек)
    text = f"💣 **ИГРА НАЧАТА**\nМин: {count}\nСтавка: {user_data['bet']} руб.\n\nНажимай на ячейки! 👇"
    
    kb = []
    for i in range(5):
        row = []
        for j in range(5):
            row.append(InlineKeyboardButton(text="❓", callback_data=f"mine_click_{count}_{i*5+j}"))
        kb.append(row)
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# (Логика нажатия на мину упрощена для примера, чтобы не забивать код)
@dp.callback_query(F.data.startswith("mine_click_"))
async def mine_click(call: types.CallbackQuery):
    data = call.data.split("_")
    count = int(data[2])
    # Шанс проигрыша зависит от кол-ва мин
    if random.randint(1, 25) <= count:
        user_data["balance"] -= user_data["bet"]
        await call.message.edit_text(f"💥 **БУМ! Вы попали на мину.**\n💰 Баланс: {user_data['balance']} руб.", 
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Снова", callback_data="prep_mines")]]))
    else:
        win = int(user_data["bet"] * (1 + (count/10)))
        user_data["balance"] += win - user_data["bet"]
        await call.message.edit_text(f"💎 **ЧИСТО! Вы выиграли {win} руб.**\n💰 Баланс: {user_data['balance']} руб.", 
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Еще ячейку", callback_data=f"start_mines_{count}"), 
                                                                                         InlineKeyboardButton(text="◀️ Забрать", callback_data="to_main")]]))

# --- ПОДГОТОВКА ОСТАЛЬНЫХ ИГР (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    if game == "mines": return # Пропускаем, так как обработано выше
    header = f"👤 **{call.from_user.first_name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    if game == "dice":
        text = f"{header}🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
              [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")]]
    elif game == "bowling":
        text = f"{header}🎳 **Боулинг · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="2 кегли", callback_data="bet_bowling_2")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]]
    elif game == "football":
        text = f"{header}⚽ **Футбол · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")], [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
    elif game == "basketball":
        text = f"{header}🏀 **Баскет · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
    elif game == "darts":
        text = f"{header}🎯 **Дартс · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center")]]
    elif game == "slots":
        text = f"{header}🎰 **Слоты**\n{footer}"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True); return
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
        elif choice.startswith("v"): win, coef = (val == int(choice[1])), 5.8
    elif game_type == "bowling":
        win, coef = (choice == "strike" and val == 6) or (choice == "miss" and val == 1) or (choice.isdigit() and val == int(choice)), 5.8
    elif game_type == "football":
        win, coef = (choice == "goal" and val >= 3) or (choice == "miss" and val < 3), 1.6
    elif game_type == "basketball":
        win, coef = (choice == "goal" and val >= 4) or (choice == "miss" and val < 4), 1.6
    elif game_type == "darts":
        if choice == "center": win, coef = (val == 6), 5.8
        elif choice == "red": win, coef = (val in [4, 5]), 1.94
        elif choice == "white": win, coef = (val in [2, 3]), 2.9
    elif game_type == "slots":
        win, coef = (val in [1, 22, 43, 64]), 10.0
    if win: user_data["balance"] += int(user_data["bet"] * coef) - user_data["bet"]
    else: user_data["balance"] -= user_data["bet"]
    res_text = f"**{call.from_user.first_name}**\n{'🥳 **Победа!**' if win else '❌ **Проигрыш**'}\n{LINE}\n💰 Баланс: {user_data['balance']} руб.\n🎲 Результат: {val}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Снова", callback_data=f"prep_{game_type}"), InlineKeyboardButton(text="◀️ Меню", callback_data="to_main")]])
    await msg.reply(res_text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await bot.send_message(call.from_user.id, f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await admin_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
