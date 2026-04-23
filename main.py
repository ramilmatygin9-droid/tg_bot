import asyncio
import random
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
        [InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")]
    ])

# --- БЫСТРЫЕ ИГРЫ (ДОБАВЛЕН КРАШ) ---
@dp.callback_query(F.data == "fast")
async def fast_games(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Краш", callback_data="prep_crash")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await call.message.edit_text("🚀 **Выберите быструю игру:**", reply_markup=kb, parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ КРАШ (РАКЕТА) ---
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
    # Коэффициент, на котором ракета взорвется
    crash_point = round(random.uniform(1.0, 5.0), 2)
    current_coef = 1.0
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ЗАБРАТЬ", callback_data=f"cashout_crash_{crash_point}")]
    ])
    
    msg = call.message
    # Эмуляция полета
    for _ in range(20):
        if current_coef >= crash_point:
            await msg.edit_text(f"💥 **РАКЕТА ВЗОРВАЛАСЬ!**\nКоэффициент: **x{crash_point}**\n\n❌ Вы проиграли {user_data['bet']} руб.", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Еще раз", callback_data="prep_crash")]]))
            return
        
        current_coef = round(current_coef + 0.1, 1)
        # Обновляем кнопку с текущим кэшаутом
        kb.inline_keyboard[0][0].text = f"💰 ЗАБРАТЬ x{current_coef}"
        try:
            await msg.edit_text(f"🚀 **Ракета летит...**\n\nТекущий множитель: **x{current_coef}**", reply_markup=kb)
        except: pass
        await asyncio.sleep(0.8)

@dp.callback_query(F.data.startswith("cashout_crash_"))
async def cashout_crash(call: types.CallbackQuery):
    # Получаем данные из callback (нужна сложная логика для защиты от читов, тут упрощено)
    win_coef = float(call.message.text.split("x")[1])
    win_amount = int(user_data['bet'] * win_coef)
    
    await call.message.edit_text(
        f"🥳 **ВЫ УСПЕЛИ!**\n\n"
        f"Ракета продолжает полет, но вы забрали:\n"
        f"💰 **{win_amount} руб.** (множитель x{win_coef})",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")]])
    )

# --- ОСТАЛЬНЫЕ ФУНКЦИИ (СТАРЫЕ) ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: **{user_data['balance']} руб.**\n💸 Ставка: **{user_data['bet']} руб.**\n\n👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = (f"👤 **{call.from_user.first_name}** | ID: `{call.from_user.id}`\n"
            f"🎖 Ваш уровень: **{user_data['level']}**\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n{LINE}\nУдачи!")
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]), parse_mode="Markdown")

# ... (Логика кубика, боулинга и других игр из предыдущих сообщений остается здесь) ...

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
