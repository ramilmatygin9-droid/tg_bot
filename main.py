import asyncio
import random
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

user_data = {"balance": 1000, "bet": 10}
change_bet_state = {}
user_support_state = {} 

DOTS = "· · · · · · · · · · · · · · · · ·"
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
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="prep_mines"),
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")
        ],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet_main")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: {user_data['balance']} mс\n💸 Ставка: {user_data['bet']} mс", reply_markup=main_kb())

# --- ПОМОЩЬ (ПИШЕТ В БОТА АДМИНУ) ---
@dp.callback_query(F.data == "ask_help")
async def help_handler(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("🆘 **ПОДДЕРЖКА**\n\nНапишите ваше сообщение прямо сюда, и я передам его администратору.")
    await call.answer()

# --- ОБРАБОТКА ВСЕХ СООБЩЕНИЙ (ПОДДЕРЖКА И СТАВКА) ---
@dp.message()
async def handle_all_messages(message: types.Message):
    uid = message.from_user.id
    
    # Отправка сообщения админу в бота
    if user_support_state.get(uid):
        sms = (f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n{LINE}\n👤 Имя: {message.from_user.first_name}\n🆔 ID: `{uid}`\n✉️ Текст: {message.text}")
        try:
            # Отправляем через admin_bot тебе в ЛС
            await admin_bot.send_message(MY_ID, sms)
            await message.answer("✅ Сообщение успешно доставлено администратору!")
        except:
            await message.answer("❌ Ошибка: бот не может написать админу. Проверьте MY_ID.")
        user_support_state[uid] = False
        return

    # Изменение ставки
    if uid in change_bet_state:
        if message.text.isdigit():
            user_data["bet"] = int(message.text)
            game_back = change_bet_state.pop(uid)
            await message.answer(f"✅ Ставка: {user_data['bet']} mс")
            # Возврат в меню (имитация нажатия кнопки)
            mock_call = types.CallbackQuery(id="0", from_user=message.from_user, chat_instance="0", message=message, data=f"prep_{game_back}")
            await prepare_game(mock_call)

# --- ИНТЕРФЕЙС ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    btn_edit = InlineKeyboardButton(text="✏️", callback_data=f"change_bet_{game}")
    btn_back = [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]

    if game == "dice":
        text = f"Рамиль\n🍀 **Кубик · выбери режим!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit],
              [InlineKeyboardButton(text="1", callback_data="b_d_1"), InlineKeyboardButton(text="2", callback_data="b_d_2"), InlineKeyboardButton(text="3", callback_data="b_d_3")],
              [InlineKeyboardButton(text="4", callback_data="b_d_4"), InlineKeyboardButton(text="5", callback_data="b_d_5"), InlineKeyboardButton(text="6", callback_data="b_d_6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="b_d_e"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="b_d_o")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="b_d_m"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="b_d_l")],
              btn_back]
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit], [InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="b_b_g")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="b_b_m")], btn_back]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit], [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="b_f_g")], [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="b_f_m")], btn_back]
    elif game == "darts":
        text = f"Рамиль\n🎯 **Дартс · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit], [InlineKeyboardButton(text="🔴 Красное", callback_data="b_dt_r"), InlineKeyboardButton(text="⚪ Белое", callback_data="b_dt_w")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="b_dt_c"), InlineKeyboardButton(text="😟 Мимо", callback_data="b_dt_m")], btn_back]
    elif game == "bowling":
        text = f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit], [InlineKeyboardButton(text="1 кегля", callback_data="b_bw_1"), InlineKeyboardButton(text="3 кегли", callback_data="b_bw_3")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="b_bw_s"), InlineKeyboardButton(text="😟 Мимо", callback_data="b_bw_m")], btn_back]
    elif game == "mines":
        text = f"Рамиль\n💣 **Мины · выбери мины!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [[btn_edit], [InlineKeyboardButton(text="1", callback_data="sm_1"), InlineKeyboardButton(text="3", callback_data="sm_3"), InlineKeyboardButton(text="5", callback_data="sm_5")],
              [InlineKeyboardButton(text="10", callback_data="sm_10"), InlineKeyboardButton(text="24", callback_data="sm_24")], btn_back]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ИЗМЕНЕНИЕ СТАВКИ ---
@dp.callback_query(F.data.startswith("change_bet_"))
async def change_bet_handler(call: types.CallbackQuery):
    game = call.data.split("_")[2]
    change_bet_state[call.from_user.id] = game
    await call.message.answer("✏️ Введите новую сумму ставки:")
    await call.answer()

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await admin_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
