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
active_mines_games = {}

DOTS = "· · · · · · · · · · · · · · · · ·"

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
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    ])

# --- ИНТЕРФЕЙС ИГР ПО СКРИНШОТАМ ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    uid = call.from_user.id
    
    # Кнопка изменения ставки (карандаш)
    btn_edit = InlineKeyboardButton(text="✏️", callback_data=f"change_bet_{game}")
    btn_back = [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]

    if game == "dice":
        text = f"Рамиль\n🍀 **Кубик · выбери режим!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="1", callback_data="bet_dice_1"), InlineKeyboardButton(text="2", callback_data="bet_dice_2"), InlineKeyboardButton(text="3", callback_data="bet_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="bet_dice_4"), InlineKeyboardButton(text="5", callback_data="bet_dice_5"), InlineKeyboardButton(text="6", callback_data="bet_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="bet_dice_3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_dice_more"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_dice_less")],
            btn_back
        ]
    elif game == "bowling":
        text = f"Рамиль\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс\n\n🔰 **Коэффициенты:**\n" \
               f"1️⃣ - 5️⃣ кегли (x5.8)\n🎳 Страйк (x5.8)\n😟 Мимо (x5.8)"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="1 кегля", callback_data="bet_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_bowl_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="bet_bowl_4"), InlineKeyboardButton(text="5 кеглей", callback_data="bet_bowl_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowl_s"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowl_m")],
            btn_back
        ]
    elif game == "football":
        text = f"Рамиль\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_foot_g")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_foot_m")],
            btn_back
        ]
    elif game == "basketball":
        text = f"Рамиль\n🏀 **Баскетбол · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="🏀 Гол - x1.6", callback_data="bet_basket_g")],
            [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basket_m")],
            btn_back
        ]
    elif game == "darts":
        text = f"Рамиль\n🎯 **Дартс · выбери исход!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс\n\n🔰 **Коэффициенты:**\n" \
               f"🔴 Красное (x1.94)\n⚪ Белое (x2.9)\n🎯 Центр (x5.8)\n😟 Мимо (x5.8)"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="🔴 Красное", callback_data="bet_dart_r"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_dart_w")],
            [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_dart_c"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_dart_m")],
            btn_back
        ]
    elif game == "mines":
        text = f"Рамиль\n💣 **Мины · выбери мины!**\n{DOTS}\n💸 Ставка: {user_data['bet']} mс"
        kb = [
            [btn_edit],
            [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
            [InlineKeyboardButton(text="1", callback_data="st_m_1"), InlineKeyboardButton(text="2", callback_data="st_m_2"), InlineKeyboardButton(text="3", callback_data="st_m_3")],
            [InlineKeyboardButton(text="4", callback_data="st_m_4"), InlineKeyboardButton(text="5", callback_data="st_m_5"), InlineKeyboardButton(text="6", callback_data="st_m_6")],
            btn_back
        ]
    else: return

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА ИЗМЕНЕНИЯ СТАВКИ ---
@dp.callback_query(F.data.startswith("change_bet"))
async def start_change_bet(call: types.CallbackQuery):
    uid = call.from_user.id
    parts = call.data.split("_")
    change_bet_state[uid] = parts[2] if len(parts) > 2 else "main"
    await call.message.answer("✏️ Введите новую сумму ставки:")

@dp.message()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    if uid in change_bet_state:
        if message.text.isdigit():
            user_data["bet"] = int(message.text)
            back_to = change_bet_state.pop(uid)
            if back_to == "main":
                await message.answer(f"✅ Ставка: {user_data['bet']} mс", reply_markup=main_kb())
            else:
                # Возвращаем в меню той же игры
                await message.answer(f"✅ Ставка изменена!", reply_markup=main_kb())
        else:
            await message.answer("⚠️ Введите число.")

# --- ЗАПУСК ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: {user_data['balance']} mс\n💸 Ставка: {user_data['bet']} mс", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} mс", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
