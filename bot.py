import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Логирование
logging.basicConfig(level=logging.INFO)

# Конфигурация
TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"

# ID премиум эмодзи из твоих скриншотов
PICKAXE_ID = "5197371802136892976"  # Анимированная кирка
MONEY_BAG_ID = "5206223871467878339" # Мешок с деньгами
CASH_ID = "5206599371868631162"      # Пачка денег

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных игроков
players = {}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Добро пожаловать на прииск!</b>\n\n'
        f'Команды:\n'
        f'⛏ /mine — начать добычу\n'
        f'💰 /balance — проверить счет',
        parse_mode="HTML"
    )

@dp.message(Command("mine"))
async def mine_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = 0

    # Выбираем время работы
    wait_time = random.randint(5, 12)
    
    # Отправляем начальное сообщение
    status_msg = await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Начинаем копать...</b>\n'
        f'⏳ Осталось: <b>{wait_time}</b> сек.', 
        parse_mode="HTML"
    )
    
    # Цикл для живого отсчета секунд
    for seconds_left in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            # Обновляем текст сообщения каждую секунду
            await status_msg.edit_text(
                f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа в процессе...</b>\n'
                f'⏳ Осталось: <b>{seconds_left}</b> сек.',
                parse_mode="HTML"
            )
        except Exception:
            # Игнорируем ошибки, если сообщение удалено или не изменилось
            pass
    
    # Награда
    reward = random.randint(200, 700)
    players[user_id] += reward
    
    # Удаляем таймер перед выводом результата
    await status_msg.delete()
    
    # Итоговое сообщение
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Успешная добыча!</b>\n'
        f'━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji> Найдено: <b>{reward}</b> монет\n'
        f'🏦 Ваш баланс: <b>{players[user_id]}</b>',
        parse_mode="HTML"
    )

@dp.message(Command("balance"))
async def bal_cmd(message: types.Message):
    balance = players.get(message.from_user.id, 0)
    await message.answer(
        f'💰 Ваш баланс: <b>{balance}</b> <tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji>',
        parse_mode="HTML"
    )

async def main():
    print("Шахта с таймером запущена!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
