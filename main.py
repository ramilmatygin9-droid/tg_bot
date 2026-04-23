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

# Данные пользователя
user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}
active_flights = {}
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
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev"),
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
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.bot.id == bot.id:
        text = (
            f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n"
            f"💸 Ставка: **{user_data['bet']} руб.**\n\n"
            f"👇 *Выбери игру и начинай!*"
        )
        await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- СИСТЕМА ПОМОЩИ И СТАВОК ---
@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    
    # Изменение ставки
    if message.bot.id == bot.id and change_bet_state.get(uid):
        if message.text.isdigit() and int(message.text) > 0:
            user_data["bet"] = int(message.text)
            change_bet_state[uid] = False
            await message.answer(f"✅ Ставка изменена на **{user_data['bet']} руб.**", reply_markup=main_kb())
        else:
            await message.answer("❌ Введите корректное число больше 0.")
        return

    # Поддержка
    if message.bot.id == bot.id and user_support_state.get(uid):
        username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
        premium = "💎 Да" if message.from_user.is_premium else "Нет"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{uid}")]])
        report = (f"🆘 **Новый тикет!**\n{LINE}\n👤 Имя: {message.from_user.first_name}\n🔗 Юзер: {username}\n"
                  f"🆔 ID: `{uid}`\n💎 Premium: {premium}\n{LINE}\n📝 Текст: {message.text}")
        await admin_bot.send_message(MY_ID, report, reply_markup=kb, parse_mode="Markdown")
        await message.answer("✅ Сообщение отправлено администрации!")
        user_support_state[uid] = False

    # Ответ админа
    elif message.bot.id == admin_bot.id and uid == MY_ID:
        if admin_reply_state.get(MY_ID):
            target_id = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target_id, f"✉️ **Ответ техподдержки:**\n\n{message.text}")
                await message.answer(f"✅ Ответ отправлен пользователю `{target_id}`")
                del admin_reply_state[MY_ID]
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")

# --- CALLBACKS ---
@dp.callback_query(F.data == "under_dev")
async def dev_alert(call: types.CallbackQuery):
    await call.answer("🛠 Данный раздел находится в разработке!", show_alert=True)

@dp.callback_query(F.data == "change_bet")
async def bet_init(call: types.CallbackQuery):
    change_bet_state[call.from_user.id] = True
    await call.message.answer("✏️ **Введите новую сумму ставки (числом):**")
    await call.answer()

@dp.callback_query(F.data == "ask_help")
async def ask_help(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 **Напишите ваше сообщение в поддержку:**")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_reply_"))
async def adm_reply_callback(call: types.CallbackQuery):
    if call.from_user.id == MY_ID:
        target_id = call.data.split("_")[2]
        admin_reply_state[MY_ID] = target_id
        await call.message.answer(f"⌨️ Введите ответ для пользователя `{target_id}`:")
        await call.answer()

# --- ПОДГОТОВКА ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    header = f"👤 **{call.from_user.first_name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    
    if game == "dice":
        text = f"{header}🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
              [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
              [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="bet_dice_eq3")]]
    elif game == "bowling":
        text = f"{header}🎳 **Боулинг · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_bowling_3")],
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
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_darts_miss")]]
    elif game == "slots":
        text = f"{header}🎰 **Слоты · удачи!**\n{footer}"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ ---
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
        elif choice == "eq3": win, coef = (val == 3), 5.8
        elif choice.startswith("v"): win, coef = (val == int(choice[1])), 5.8
    elif game_type == "bowling":
        win, coef = (choice == "miss" and val == 1) or (choice == "strike" and val == 6) or (choice.isdigit() and val == int(choice)), 5.8
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

    if win: user_data["balance"] += int(user_data["bet"] * coef) - user_data["bet"]
    else: user_data["balance"] -= user_data["bet"]

    res_text = f"**{call.from_user.first_name}**\n{'🥳 **Победа!**' if win else '❌ **Проигрыш**'}\n{LINE}\n💰 Баланс: {user_data['balance']} руб.\n🎲 Результат: {val}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Снова", callback_data=f"prep_{game_type}"), InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")]])
    await msg.reply(res_text, reply_markup=kb, parse_mode="Markdown")

# --- ПРОФИЛЬ И МЕНЮ ---
@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = (f"👤 **{call.from_user.first_name}**\n🆔 ID: `{call.from_user.id}`\n{LINE}\n💰 Баланс: **{user_data['balance']} руб.**\n🎖 Уровень: **{user_data['level']}**\n{LINE}\nУдачи в играх!")
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: **{user_data['balance']} руб.**\n💸 Ставка: **{user_data['bet']} руб.**\n\n👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
