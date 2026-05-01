import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

# ТОКЕН БОТА
GAME_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk"

# СОЗДАЁМ БОТА
bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ХРАНИЛИЩЕ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "bet": 100,
            "games": 0,
            "wins": 0
        }
    return users[user_id]

# КНОПКИ ГЛАВНОГО МЕНЮ
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 СЛОТЫ", callback_data="slots"),
            InlineKeyboardButton(text="🎲 КУБИК", callback_data="dice"),
            InlineKeyboardButton(text="🎡 РУЛЕТКА", callback_data="roulette")
        ],
        [
            InlineKeyboardButton(text="🪨 КАМЕНЬ-НОЖНИЦЫ", callback_data="rps"),
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="mines"),
            InlineKeyboardButton(text="🏀 БАСКЕТБОЛ", callback_data="basketball")
        ],
        [
            InlineKeyboardButton(text="🎮 WEB ИГРЫ", web_app=WebAppInfo(url="https://ramilmatygin9-droid.github.io/GLITCH-WIN/")),
            InlineKeyboardButton(text="💰 БАЛАНС", callback_data="balance")
        ],
        [
            InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="stats"),
            InlineKeyboardButton(text="💸 СТАВКА", callback_data="bet")
        ]
    ])
    return keyboard

# КОМАНДА /START
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user = get_user(message.from_user.id)
    text = f"""🎮 <b>ДОБРО ПОЖАЛОВАТЬ В GLITCH WIN!</b> 🎮

💰 Баланс: <b>{user['balance']}</b> m¢
💸 Ставка: <b>{user['bet']}</b> m¢

👇 <i>Выбери игру и начинай выигрывать!</i>"""
    
    await message.answer(text, reply_markup=main_menu())

# БАЛАНС
@dp.callback_query(F.data == "balance")
async def show_balance(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    await call.answer(f"💰 Баланс: {user['balance']} m¢", show_alert=True)

# СТАТИСТИКА
@dp.callback_query(F.data == "stats")
async def show_stats(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    winrate = round((user['wins'] / user['games'] * 100), 1) if user['games'] > 0 else 0
    text = f"""📊 <b>ТВОЯ СТАТИСТИКА</b> 📊

🎮 Всего игр: <b>{user['games']}</b>
✅ Побед: <b>{user['wins']}</b>
📈 Винрейт: <b>{winrate}%</b>
💰 Баланс: <b>{user['balance']}</b> m¢
💸 Ставка: <b>{user['bet']}</b> m¢"""
    
    await call.message.edit_text(text, reply_markup=main_menu())

# СМЕНА СТАВКИ
@dp.callback_query(F.data == "bet")
async def change_bet(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bets = [10, 25, 50, 100, 250, 500, 1000]
    current = user['bet']
    next_bet = bets[(bets.index(current) + 1) % len(bets)]
    user['bet'] = next_bet
    await call.answer(f"💸 Ставка изменена на {user['bet']} m¢", show_alert=True)
    
    # Обновляем сообщение
    text = f"""🎮 <b>ДОБРО ПОЖАЛОВАТЬ В GLITCH WIN!</b> 🎮

💰 Баланс: <b>{user['balance']}</b> m¢
💸 Ставка: <b>{user['bet']}</b> m¢

👇 <i>Выбери игру и начинай выигрывать!</i>"""
    await call.message.edit_text(text, reply_markup=main_menu())

# ИГРА СЛОТЫ
@dp.callback_query(F.data == "slots")
async def play_slots(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    
    if user['balance'] < user['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Списываем ставку
    user['balance'] -= user['bet']
    user['games'] += 1
    
    # Символы для слотов
    symbols = ["🍒", "🍊", "🍋", "🍉", "🔔", "💎", "7️⃣", "⭐"]
    
    reel1 = random.choice(symbols)
    reel2 = random.choice(symbols)
    reel3 = random.choice(symbols)
    
    win = False
    multiplier = 0
    
    # Проверка выигрыша
    if reel1 == reel2 == reel3:
        if reel1 == "7️⃣":
            multiplier = 10
        elif reel1 == "⭐":
            multiplier = 8
        elif reel1 == "💎":
            multiplier = 6
        else:
            multiplier = 4
        win = True
    elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
        multiplier = 2
        win = True
    
    if win:
        win_amount = int(user['bet'] * multiplier)
        user['balance'] += win_amount
        user['wins'] += 1
        result_text = f"✅ ПОБЕДА! x{multiplier} = +{win_amount} m¢"
    else:
        result_text = f"❌ ПРОИГРЫШ! -{user['bet']} m¢"
    
    text = f"""🎰 <b>СЛОТЫ</b> 🎰
┌─────────────┐
│  {reel1}   {reel2}   {reel3}  │
└─────────────┘

{result_text}
💰 Баланс: {user['balance']} m¢"""
    
    await call.message.answer(text, reply_markup=main_menu())
    await call.message.delete()

# ИГРА КУБИК
@dp.callback_query(F.data == "dice")
async def play_dice(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    
    if user['balance'] < user['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user['balance'] -= user['bet']
    user['games'] += 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣", callback_data="dice_1"),
            InlineKeyboardButton(text="2️⃣", callback_data="dice_2"),
            InlineKeyboardButton(text="3️⃣", callback_data="dice_3"),
            InlineKeyboardButton(text="4️⃣", callback_data="dice_4"),
            InlineKeyboardButton(text="5️⃣", callback_data="dice_5"),
            InlineKeyboardButton(text="6️⃣", callback_data="dice_6")
        ],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])
    
    text = f"""🎲 <b>КУБИК</b> 🎲

💰 Ставка: {user['bet']} m¢

Выбери число от 1 до 6:"""
    
    await call.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("dice_"))
async def dice_result(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    choice = int(call.data.split("_")[1])
    
    # Кидаем кубик
    msg = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3)
    value = msg.dice.value
    
    if choice == value:
        win_amount = int(user['bet'] * 5.8)
        user['balance'] += win_amount
        user['wins'] += 1
        text = f"""🎲 <b>КУБИК</b> 🎲

Твой выбор: {choice}
Выпало: {value}
✅ ПОБЕДА! x5.8 = +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🎲 <b>КУБИК</b> 🎲

Твой выбор: {choice}
Выпало: {value}
❌ ПРОИГРЫШ! -{user['bet']} m¢
💰 Баланс: {user['balance']} m¢"""
    
    await call.message.answer(text, reply_markup=main_menu())
    await call.message.delete()

# ИГРА КАМЕНЬ-НОЖНИЦЫ-БУМАГА
@dp.callback_query(F.data == "rps")
async def play_rps(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    
    if user['balance'] < user['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user['balance'] -= user['bet']
    user['games'] += 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🪨 КАМЕНЬ", callback_data="rps_rock"),
            InlineKeyboardButton(text="✂️ НОЖНИЦЫ", callback_data="rps_scissors"),
            InlineKeyboardButton(text="📄 БУМАГА", callback_data="rps_paper")
        ],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])
    
    text = f"""🪨✂️📄 <b>КАМЕНЬ-НОЖНИЦЫ-БУМАГА</b> 🪨✂️📄

💰 Ставка: {user['bet']} m¢

Сделай выбор:"""
    
    await call.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("rps_"))
async def rps_result(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    player = call.data.split("_")[1]
    
    bot = random.choice(["rock", "scissors", "paper"])
    
    names = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}
    
    if player == bot:
        user['balance'] += user['bet']
        text = f"""🪨✂️📄 <b>КАМЕНЬ-НОЖНИЦЫ-БУМАГА</b> 🪨✂️📄

Ты: {names[player]}
Бот: {names[bot]}
🤝 НИЧЬЯ! Ставка возвращена
💰 Баланс: {user['balance']} m¢"""
    elif (player == "rock" and bot == "scissors") or \
         (player == "scissors" and bot == "paper") or \
         (player == "paper" and bot == "rock"):
        win_amount = int(user['bet'] * 2)
        user['balance'] += win_amount
        user['wins'] += 1
        text = f"""🪨✂️📄 <b>КАМЕНЬ-НОЖНИЦЫ-БУМАГА</b> 🪨✂️📄

Ты: {names[player]}
Бот: {names[bot]}
✅ ПОБЕДА! +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🪨✂️📄 <b>КАМЕНЬ-НОЖНИЦЫ-БУМАГА</b> 🪨✂️📄

Ты: {names[player]}
Бот: {names[bot]}
❌ ПРОИГРЫШ! -{user['bet']} m¢
💰 Баланс: {user['balance']} m¢"""
    
    await call.message.answer(text, reply_markup=main_menu())
    await call.message.delete()

# ИГРА РУЛЕТКА (простая)
@dp.callback_query(F.data == "roulette")
async def play_roulette(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    
    if user['balance'] < user['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user['balance'] -= user['bet']
    user['games'] += 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔴 КРАСНОЕ (x2)", callback_data="roulette_red"),
            InlineKeyboardButton(text="⚫ ЧЁРНОЕ (x2)", callback_data="roulette_black"),
            InlineKeyboardButton(text="🟢 ЗЕЛЁНОЕ (x14)", callback_data="roulette_green")
        ],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])
    
    text = f"""🎡 <b>РУЛЕТКА</b> 🎡

💰 Ставка: {user['bet']} m¢

Выбери цвет:"""
    
    await call.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("roulette_"))
async def roulette_result(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    choice = call.data.split("_")[1]
    
    # Результат рулетки
    rand = random.randint(0, 13)
    if rand == 0:
        result = "green"
    elif rand <= 6:
        result = "red"
    else:
        result = "black"
    
    if choice == result:
        multiplier = 14 if result == "green" else 2
        win_amount = int(user['bet'] * multiplier)
        user['balance'] += win_amount
        user['wins'] += 1
        text = f"""🎡 <b>РУЛЕТКА</b> 🎡

Выпало: {result.upper()}
✅ ПОБЕДА! x{multiplier} = +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🎡 <b>РУЛЕТКА</b> 🎡

Выпало: {result.upper()}
❌ ПРОИГРЫШ! -{user['bet']} m¢
💰 Баланс: {user['balance']} m¢"""
    
    await call.message.answer(text, reply_markup=main_menu())
    await call.message.delete()

# ИГРА БАСКЕТБОЛ
@dp.callback_query(F.data == "basketball")
async def play_basketball(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    
    if user['balance'] < user['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user['balance'] -= user['bet']
    
    msg = await call.message.answer_dice(emoji="🏀")
    await asyncio.sleep(3)
    value = msg.dice.value
    
    if value >= 5:
        win_amount = int(user['bet'] * 2.4)
        user['balance'] += win_amount
        user['games'] += 1
        user['wins'] += 1
        text = f"""🏀 <b>БАСКЕТБОЛ</b> 🏀

🎯 ПОПАДАНИЕ! x2.4
✅ Выигрыш: +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        user['games'] += 1
        text = f"""🏀 <b>БАСКЕТБОЛ</b> 🏀

🙈 МИМО!
❌ Проигрыш: -{user['bet']} m¢
💰 Баланс: {user['balance']} m¢"""
    
    await call.message.answer(text, reply_markup=main_menu())
    await call.message.delete()

# ИГРА МИНЫ
@dp.callback_query(F.data == "mines")
async def play_mines(call: types.CallbackQuery):
    await call.answer("🚧 Мины в разработке!", show_alert=True)

# КНОПКА НАЗАД
@dp.callback_query(F.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"""🎮 <b>ДОБРО ПОЖАЛОВАТЬ В GLITCH WIN!</b> 🎮

💰 Баланс: <b>{user['balance']}</b> m¢
💸 Ставка: <b>{user['bet']}</b> m¢

👇 <i>Выбери игру и начинай выигрывать!</i>"""
    await call.message.edit_text(text, reply_markup=main_menu())

# ЗАПУСК БОТА
async def main():
    print("🤖 БОТ ЗАПУЩЕН!")
    print("🎮 Доступны игры: Слоты, Кубик, Рулетка, Камень-ножницы, Баскетбол")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
