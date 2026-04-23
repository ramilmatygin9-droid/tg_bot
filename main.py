import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
ADMIN_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
MY_ID = 8462392581  # Твой ID

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

user_support_state = {}
admin_reply_state = {}

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
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")
        ]
    ])

# --- МЕНЮ ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    name = call.from_user.first_name
    header = f"**{name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: 10 руб.**"
    
    kb = []
    text = ""

    if game == "dice":
        text = f"{header}🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [
            [InlineKeyboardButton(text="1️⃣", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2️⃣", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3️⃣", callback_data="bet_dice_v3")],
            [InlineKeyboardButton(text="4️⃣", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5️⃣", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6️⃣", callback_data="bet_dice_v6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="➖ Равно 3 x5.8", callback_data="bet_dice_eq3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_dice_big"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_dice_small")]
        ]
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
        text = f"{header}⚽ **Футбол · выбери исход!**\n{footer}"
    elif game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")],
              [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
        text = f"{header}🏀 **Баскет · выбери исход!**\n{footer}"
    elif game == "bowling":
        kb = [
            [InlineKeyboardButton(text="1️⃣ кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="3️⃣ кегли", callback_data="bet_bowling_3")],
            [InlineKeyboardButton(text="4️⃣ кегли", callback_data="bet_bowling_4"), InlineKeyboardButton(text="5️⃣ кегель", callback_data="bet_bowling_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]
        ]
        text = f"{header}🎳 **Боулинг · выбери исход!**\n{footer}\n\n🔰 **Коэффициенты:**\n┕ 1️⃣ - 5️⃣ кегли (x5.8)\n┕ 🎳 Страйк (x5.8)\n┕ 😟 Мимо (x5.8)"
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_darts_miss")]]
        text = f"{header}🎯 **Дартс · выбери исход!**\n{footer}\n\n🔰 **Коэффициенты:**\n┕ 🔴 Красное (x1.94)\n┕ ⚪ Белое (x2.9)\n┕ 🎯 Центр (x5.8)\n┕ 😟 Мимо (x5.8)"
    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]
        text = f"{header}🎰 **Слоты · удачи!**\n{footer}"

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
    elif game_type == "basketball":
        win, coef = ((choice == "goal" and val >= 4) or (choice == "miss" and val < 4)), (1.6 if choice == "goal" else 2.4)
    elif game_type == "football":
        win, coef = ((choice == "goal" and val >= 3) or (choice == "miss" and val < 3)), (1.6 if choice == "goal" else 2.4)
    elif game_type == "bowling":
        if choice == "strike": win = (val == 6)
        elif choice == "miss": win = (val == 1)
        else: win = (val == int(choice))
        coef = 5.8
    elif game_type == "darts":
        if choice == "center": win, coef = (val == 6), 5.8
        elif choice == "red": win, coef = (val in [4, 5]), 1.94
        elif choice == "white": win, coef = (val in [2, 3]), 2.9
        elif choice == "miss": win, coef = (val == 1), 5.8
    elif game_type == "slots":
        win, coef = (val in [1, 22, 43, 64]), 10.0

    res_text = f"**{call.from_user.first_name}**\n{'🥳 **Победа!**' if win else '❌ **Проигрыш**'}\n{LINE}\n💰 Выигрыш: {int(10 * coef) if win else 0} руб. {'✅' if win else '❌'}\n🎲 Результат: {val}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 играть снова", callback_data=f"prep_{game_type}"),
        InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")
    ]])
    await msg.reply(res_text, reply_markup=kb, parse_mode="Markdown")

# --- ВЫВОД (В РАЗРАБОТКЕ) ---
@dp.callback_query(F.data == "withdraw")
async def withdraw_handler(call: types.CallbackQuery):
    await call.answer("💳 Данный раздел находится в разработке!", show_alert=True)

# --- ПОДДЕРЖКА ---
@dp.callback_query(F.data == "ask_help")
async def ask_help(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 **Опишите вашу проблему или вопрос:**")
    await call.answer()

@dp.message()
async def handle_messages(message: types.Message):
    if message.bot.token == GAME_TOKEN:
        if message.text == "/start":
            await message.answer(f"**{message.from_user.first_name}**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")
        elif user_support_state.get(message.from_user.id):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{message.from_user.id}")]])
            await admin_bot.send_message(MY_ID, f"🆘 **Тикет от {message.from_user.first_name}** (`{message.from_user.id}`):\n\n{message.text}", reply_markup=kb)
            await message.answer("✅ **Отправлено!** Ожидайте ответа.")
            del user_support_state[message.from_user.id]
    elif message.bot.token == ADMIN_TOKEN and message.from_user.id == MY_ID:
        if admin_reply_state.get(MY_ID):
            target_id = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target_id, f"✉️ **Ответ администрации:**\n\n{message.text}")
                await message.answer(f"✅ Отправлено пользователю `{target_id}`")
            except:
                await message.answer("❌ Ошибка отправки")
            del admin_reply_state[MY_ID]

@dp.callback_query(F.data.startswith("adm_reply_"))
async def admin_reply_handler(call: types.CallbackQuery):
    if call.message.bot.token == ADMIN_TOKEN:
        user_id = call.data.split("_")[2]
        admin_reply_state[MY_ID] = user_id
        await call.message.answer(f"✍️ Пиши ответ для `{user_id}`:")
        await call.answer()

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"**{call.from_user.first_name}**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
