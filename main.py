import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
ADMIN_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
MY_ID = 846239258  # ИСПРАВЛЕНО: убрана лишняя единица

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

# --- ЛОГИКА СООБЩЕНИЙ ---
@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    
    # Ставка
    if message.bot.id == bot.id and change_bet_state.get(uid):
        if message.text.isdigit():
            user_data["bet"] = int(message.text)
            change_bet_state[uid] = False
            await message.answer(f"✅ Ставка: **{user_data['bet']} руб.**", reply_markup=main_kb())
        return

    # Помощь (отправка админу)
    if message.bot.id == bot.id and user_support_state.get(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{uid}")]])
        sms = f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n🆔 ID: `{uid}`\n👤 Имя: {message.from_user.first_name}\n{LINE}\n✉️ Текст: {message.text}"
        await admin_bot.send_message(MY_ID, sms, reply_markup=kb, parse_mode="Markdown")
        await message.answer("✅ Сообщение отправлено в поддержку!")
        user_support_state[uid] = False

    # Ответ админа (только если ID совпадает)
    elif message.bot.id == admin_bot.id and uid == MY_ID:
        if admin_reply_state.get(MY_ID):
            target = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target, f"✉️ **Ответ техподдержки:**\n\n{message.text}")
                await message.answer(f"✅ Ответ отправлен пользователю `{target}`")
                del admin_reply_state[MY_ID]
            except: await message.answer("❌ Ошибка отправки.")

# --- CALLBACKS ---
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
    await call.message.answer("📝 Напишите ваш вопрос:")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_reply_"))
async def adm_reply(call: types.CallbackQuery):
    admin_reply_state[MY_ID] = call.data.split("_")[2]
    await call.message.answer("⌨️ Пишите текст ответа:")
    await call.answer()

# --- ИГРЫ ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    header = f"👤 **{call.from_user.first_name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    
    if game == "dice":
        text = f"{header}🍀 **Кубик**\n{footer}"
        kb = [[InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
              [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")]]
    elif game == "bowling":
        text = f"{header}🎳 **Боулинг**\n{footer}"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="2 кегли", callback_data="bet_bowling_2")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_6")]]
    elif game == "football":
        text = f"{header}⚽ **Футбол**\n{footer}"
        kb = [[InlineKeyboardButton(text="⚽ Гол", callback_data="bet_football_goal")], [InlineKeyboardButton(text="🥅 Мимо", callback_data="bet_football_miss")]]
    elif game == "basketball":
        text = f"{header}🏀 **Баскет**\n{footer}"
        kb = [[InlineKeyboardButton(text="🏀 Попал", callback_data="bet_basketball_goal")]]
    elif game == "darts":
        text = f"{header}🎯 **Дартс**\n{footer}"
        kb = [[InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center")]]
    elif game == "slots":
        text = f"{header}🎰 **Слоты**\n{footer}"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Нет денег!", show_alert=True); return
    data = call.data.split("_")
    game_type = data[1]
    await call.message.delete()
    emoji = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}[game_type]
    msg = await bot.send_dice(call.message.chat.id, emoji=emoji)
    await asyncio.sleep(4)
    val = msg.dice.value
    
    # Упрощенная проверка победы для теста
    win = (val >= 3)
    if win: user_data["balance"] += user_data["bet"]
    else: user_data["balance"] -= user_data["bet"]

    res = f"**{call.from_user.first_name}**\n{'🥳 Победа!' if win else '❌ Проигрыш'}\n💰 Баланс: {user_data['balance']} руб."
    kb = [[InlineKeyboardButton(text="🔄 Снова", callback_data=f"prep_{game_type}"), InlineKeyboardButton(text="◀️ Меню", callback_data="to_main")]]
    await msg.reply(res, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await bot.send_message(call.from_user.id, f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb())

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
