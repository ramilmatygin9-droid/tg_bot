import asyncio
import random
from aiogram import Bot, Dispatcher, types, F

# Твой токен
TOKEN = "8693763218:AAGoc7Y2xTFZeXsaZ_mzksRkFUhOnA3Zj10"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Конструктор унижений: части, из которых бот собирает ответ
PART1 = ["Слышь, ты, ", "Эй, ", "Че ты, ", "Слушай сюда, ", "Ты, ", "Чё, борзый? "]
PART2 = ["чучело огородное, ", "жертва аборта, ", "недоразумение ходячее, ", "клоун дырявый, ", "отброс эволюции, ", "кусок тормоза, "]
PART3 = [
    "рот закрой, пока мухи не нагадили.",
    "в глаза мне смотри, когда я с тобой базарю!",
    "ты вообще понимаешь, что ты никто?",
    "твой лепет только на помойке слушать.",
    "потеряйся в пространстве, пока я тебе не помог.",
    "тебе в детстве вместо соски кирпич давали?",
    "ты зачем вообще интернет себе провел, деградант?",
    "завали свою хлеборезку и не отсвечивай."
]
PART4 = [" Понял меня?!", " Ты свободен.", " Иди плачь мамочке.", " Теряйся!", " Твой уровень — ноль.", " Гуляй, Вася."]

@dp.message(F.text)
async def generate_roast(message: types.Message):
    # Бот собирает случайную фразу из 4-х частей
    p1 = random.choice(PART1)
    p2 = random.choice(PART2)
    p3 = random.choice(PART3)
    p4 = random.choice(PART4)
    
    full_roast = f"{p1}{p2}{p3}{p4}"
    
    # Отвечаем на любое сообщение
    await message.reply(full_roast)

async def main():
    print("Жирапес-Генератор запущен. Берегите нервы!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        print("Жирапес выключен.")
