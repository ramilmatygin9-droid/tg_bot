import telebot
import random
import os
from telebot.types import Message

TOKEN = os.getenv("8156857401:AAHiNO7znRig1ttMSiJ3joAPHhUr--Z213g")  # Токен в переменных Railway
bot = telebot.TeleBot(TOKEN)

# База игроков в памяти (для простоты). При перезапуске данные обнуляются.
# Для постоянного хранения используй SQLite или PostgreSQL.
players = {}

def init_player(user_id, name):
    if user_id not in players:
        players[user_id] = {
            "name": name,
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "wins": 0,
            "losses": 0
        }

def save_exp(user_id, gained):
    players[user_id]["exp"] += gained
    # Повышение уровня: нужно exp = level * 100
    needed = players[user_id]["level"] * 100
    if players[user_id]["exp"] >= needed:
        players[user_id]["level"] += 1
        players[user_id]["exp"] -= needed
        players[user_id]["max_hp"] += 20
        players[user_id]["hp"] = players[user_id]["max_hp"]
        return True
    return False

@bot.message_handler(commands=["start"])
def cmd_start(message: Message):
    user = message.from_user
    init_player(user.id, user.first_name)
    bot.reply_to(message,
                 f"👋 {user.first_name}, добро пожаловать в игру!\n"
                 "Твой профиль: /profile\n"
                 "Идём на охоту: /hunt\n"
                 "Вызов на дуэль: /duel @username\n"
                 "Топ игроков: /top")

@bot.message_handler(commands=["profile"])
def cmd_profile(message: Message):
    user = message.from_user
    init_player(user.id, user.first_name)
    p = players[user.id]
    text = (f"📜 Профиль {p['name']}\n"
            f"⭐ Уровень: {p['level']}\n"
            f"📊 Опыт: {p['exp']}/{p['level']*100}\n"
            f"❤️ Здоровье: {p['hp']}/{p['max_hp']}\n"
            f"🏆 Побед: {p['wins']} / Поражений: {p['losses']}")
    bot.reply_to(message, text)

@bot.message_handler(commands=["hunt"])
def cmd_hunt(message: Message):
    user = message.from_user
    init_player(user.id, user.first_name)
    p = players[user.id]
    if p["hp"] <= 0:
        bot.reply_to(message, "💀 Ты мёртв! Воскресись через /revive")
        return

    monsters = [("Гоблин", 20, 15, 10), ("Волк", 30, 20, 15), ("Орк", 40, 30, 25), ("Тролль", 60, 40, 35)]
    name, hp, power, exp_reward = random.choice(monsters)
    # Симуляция боя
    player_damage = random.randint(10, 20) + p["level"] * 2
    monster_damage = random.randint(power-5, power+5)
    p["hp"] -= monster_damage
    if p["hp"] < 0:
        p["hp"] = 0
    monster_hp = hp - player_damage
    if monster_hp <= 0:
        # Победа
        gained_exp = exp_reward + p["level"] * 5
        save_exp(user.id, gained_exp)
        p["wins"] += 1
        result = (f"⚔️ Ты победил {name}!\n"
                  f"💥 Нанесён урон: {player_damage}\n"
                  f"❤️ Твоё HP: {p['hp']}/{p['max_hp']}\n"
                  f"✨ +{gained_exp} опыта")
    else:
        # Поражение
        p["losses"] += 1
        result = (f"😵 Ты проиграл {name}.\n"
                  f"💔 Твоё HP: {p['hp']}/{p['max_hp']}\n"
                  f"👹 У монстра осталось {monster_hp} HP")
    bot.reply_to(message, result)
    if p["hp"] <= 0:
        bot.reply_to(message, "Ты умер. Используй /revive")

@bot.message_handler(commands=["revive"])
def cmd_revive(message: Message):
    user = message.from_user
    init_player(user.id, user.first_name)
    if players[user.id]["hp"] <= 0:
        players[user.id]["hp"] = players[user.id]["max_hp"]
        bot.reply_to(message, "✨ Ты воскрес с полным здоровьем!")
    else:
        bot.reply_to(message, "Ты ещё жив!")

@bot.message_handler(commands=["duel"])
def cmd_duel(message: Message):
    user = message.from_user
    init_player(user.id, user.first_name)
    if not message.reply_to_message:
        bot.reply_to(message, "Ответь на сообщение игрока команде /duel")
        return
    target = message.reply_to_message.from_user
    init_player(target.id, target.first_name)
    p1 = players[user.id]
    p2 = players[target.id]
    if p1["hp"] <= 0 or p2["hp"] <= 0:
        bot.reply_to(message, "Один из участников мёртв!")
        return
    # Простой расчёт урона
    dmg1 = random.randint(15, 25) + p1["level"] * 2
    dmg2 = random.randint(15, 25) + p2["level"] * 2
    p1["hp"] -= dmg2
    p2["hp"] -= dmg1
    if p1["hp"] < 0: p1["hp"] = 0
    if p2["hp"] < 0: p2["hp"] = 0
    result = (f"🥊 Дуэль: {p1['name']} vs {p2['name']}\n"
              f"{p1['name']} нанёс {dmg1}, у него осталось {p1['hp']} HP\n"
              f"{p2['name']} нанёс {dmg2}, у него осталось {p2['hp']} HP\n")
    if p1["hp"] <= 0 and p2["hp"] <= 0:
        result += "Ничья! Оба мертвы."
    elif p1["hp"] <= 0:
        result += f"{p2['name']} победил!"
        p2["wins"] += 1
        p1["losses"] += 1
        gained = 30 + p2["level"] * 5
        save_exp(target.id, gained)
        result += f" {p2['name']} получает +{gained} опыта"
    elif p2["hp"] <= 0:
        result += f"{p1['name']} победил!"
        p1["wins"] += 1
        p2["losses"] += 1
        gained = 30 + p1["level"] * 5
        save_exp(user.id, gained)
        result += f" {p1['name']} получает +{gained} опыта"
    bot.reply_to(message, result)
    if p1["hp"] <= 0:
        bot.reply_to(message, f"{p1['name']}, ты мёртв. Используй /revive")
    if p2["hp"] <= 0:
        bot.reply_to(message, f"{p2['name']}, ты мёртв. Используй /revive")

@bot.message_handler(commands=["top"])
def cmd_top(message: Message):
    sorted_players = sorted(players.values(), key=lambda x: x["exp"] + x["level"] * 100, reverse=True)[:5]
    if not sorted_players:
        bot.reply_to(message, "Нет зарегистрированных игроков.")
        return
    text = "🏆 Топ игроков:\n"
    for i, p in enumerate(sorted_players, 1):
        text += f"{i}. {p['name']} — уровень {p['level']}, опыта {p['exp']}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=["help"])
def cmd_help(message: Message):
    bot.reply_to(message, "/start - регистрация\n/profile - статистика\n/hunt - охота\n/duel (ответ на сообщение) - дуэль\n/top - рейтинг\n/revive - воскрешение")

if __name__ == "__main__":
    bot.infinity_polling()
