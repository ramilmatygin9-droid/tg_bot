import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"

# Твои Premium ID
PICKAXE_ID = "5197371802136892976"   
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"
SUPPORT_ID = "5924712865763170353"
SHOP_ICON_ID = "5197269100878907942" # Планшет из image_7

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных: теперь храним баланс и уровень кирки
players = {}

# Настройки магазина: Название, Цена, Множитель добычи
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/start", description="🏠 Главное меню"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/shop", description="🛒 Магазин кирок"),
        BotCommand(command="/balance", description="💰 Баланс"),
        BotCommand(command="/support", description="🎧 Поддержка")
    ]
    await bot.set_my_commands(main_menu_commands, scope=BotCommandScopeDefault())

def get_player(user_id):
    if user_id not in players:
        players[user_id] = {"balance": 0, "pick_lvl": 1}
    return players[user_id]

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b><tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji>\n\n'
        f'Используй /mine или меню чтобы начать копать руду',
        parse_mode="HTML"
    )

# --- МАГАЗИН ---
@dp.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    current_pick = SHOP_PICKS[p["pick_lvl"]]["name"]
    
    text = (
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>покупай кирки и получай больше всех</b>\n\n'
        f'Также у нас есть промокоды <tg-emoji emoji-id="{SHOP_ICON_ID}">📋</tg-emoji>\n'
        f'━━━━━━━━━━━━━━\n'
        f'Твоя кирка: <b>{current_pick}</b>\n'
        f'Выбери новую кирку:'
    )
    
    # Создаем кнопки для каждой кирки (кроме стартовой)
    keyboard = []
    for lvl, info in SHOP_PICKS.items():
        if lvl > 1:
            btn_text = f"{info['name']} — {info['price']} 💵"
            keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_{lvl}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

# Обработка покупки
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    lvl = int(callback.data.split("_")[1])
    p = get_player(callback.from_user.id)
    pick = SHOP_PICKS[lvl]
    
    if p["pick_lvl"] >= lvl:
        await callback.answer("У тебя уже есть эта кирка или лучше!", show_alert=True)
    elif p["balance"] < pick["price"]:
        await callback.answer("Недостаточно монет!", show_alert=True)
    else:
        p["balance"] -= pick["price"]
        p["pick_lvl"] = lvl
        await callback.message.edit_text(
            f'✅ <b>Поздравляем!</b>\nВы купили <b>{pick["name"]}</b>!\n'
            f'Теперь удача на вашей стороне.', parse_mode="HTML"
        )

@dp.message(Command("mine"))
async def mine_cmd(message: types.Message):
    user_id = message.from_user.id
    p = get_player(user_id)
    
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b> ({wait_time}с)', parse_mode="HTML")
    
    for i in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работаем...</b> ({i}с)', parse_mode="HTML")
        except: pass
    
    # Расчет награды с учетом множителя кирки
    multiplier = SHOP_PICKS[p["pick_lvl"]]["mult"]
    base_reward = random.randint(100, 500)
    final_reward = int(base_reward * multiplier)
    
    p["balance"] += final_reward
    await status_msg.delete()
    
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Успех!</b>\n'
        f'Добыто: <b>{final_reward}</b> (Множитель x{multiplier})\n'
        f'<tg-emoji emoji-id="{BALANCE_ID}">💎</tg-emoji> Баланс: <b>{p["balance"]}</b>',
        parse_mode="HTML"
    )

@dp.message(Command("balance"))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Баланс: <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp.message(Command("support"))
async def support_cmd(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{SUPPORT_ID}">🎧</tg-emoji> Поддержка: @твой_ник', parse_mode="HTML")

async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
