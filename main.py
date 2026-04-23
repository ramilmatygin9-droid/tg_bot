import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "ТВОЙ_ТОКЕН"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_db = {}

def get_user(uid):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'lock': False}
    return user_db[uid]

# Логика определения победы на основе значения Dice
def check_win(emoji, val, choice):
    if emoji == "⚽":
        if choice == "win" and val in [3, 4, 5]: return True, 1.6
        if choice == "lose" and val in [1, 2]: return True, 2.4
    elif emoji == "🏀":
        if choice == "win" and val in [4, 5]: return True, 2.4
        if choice == "lose" and val in [1, 2, 3]: return True, 1.6
    elif emoji == "🎯":
        if choice == "red" and val in [4, 5]: return True, 1.94
        if choice == "white" and val in [2, 3]: return True, 2.9
        if choice == "center" and val == 6: return True, 5.8
        if choice == "miss" and val == 1: return True, 5.8
    elif emoji == "🎳":
        if choice == "strike" and val == 6: return True, 5.8
        if choice == "miss" and val == 1: return True, 5.8
        if choice.isdigit() and val == int(choice): return True, 5.8
    elif emoji == "🎲":
        if choice == "even" and val % 2 == 0: return True, 1.94
        if choice == "odd" and val % 2 != 0: return True, 1.94
        if choice == "high" and val > 3: return True, 1.94
        if choice == "low" and val < 3: return True, 2.9
        if choice == "3" and val == 3: return True, 5.8
        if choice.isdigit() and val == int(choice): return True, 5.8
    return False, 0

@dp.callback_query(F.data.startswith("play_"))
async def play_game(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']: return await callback.answer("⏳ Дождись окончания броска!")
    
    _, emoji, choice = callback.data.split("_")
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно ₽!")

    u['lock'] = True
    u['bal'] -= u['bet']

    # Бросаем кубик
    msg = await callback.message.answer_dice(emoji=emoji if emoji != "🎳" else "🎳")
    val = msg.dice.value

    # Имитируем ожидание анимации (около 4 секунд)
    await asyncio.sleep(4)

    is_win, coef = check_win(emoji, val, choice)

    if is_win:
        prize = int(u['bet'] * coef)
        u['bal'] += prize
        await callback.message.answer(f"✅ Результат: {val}\n💰 Вы выиграли {prize} ₽!")
    else:
        await callback.message.answer(f"❌ Результат: {val}\nВы проиграли {u['bet']} ₽.")

    u['lock'] = False
