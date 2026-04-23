# Токен бота, который будет принимать жалобы (админ-панель)
ADMIN_BOT_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

# --- ДОБАВЛЯЕМ В ГЛАВНОЕ МЕНЮ КНОПКУ ПОМОЩЬ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        # ... твои кнопки с играми ...
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# Состояние для ожидания вопроса (упрощенно без FSM для скорости)
users_asking = {}

@dp.callback_query(F.data == "ask_help")
async def help_handler(call: types.CallbackQuery):
    users_asking[call.from_user.id] = True
    await call.message.answer("📝 **Опишите вашу проблему или задайте вопрос:**\n"
                               "Я передам его администрации.")
    await call.answer()

@dp.message(F.text)
async def forward_to_admin(message: types.Message):
    # Если пользователь нажал "Помощь" и пишет текст
    if message.from_user.id in users_asking:
        user_info = f"🆘 **Новый вопрос!**\nОт: {message.from_user.mention_html()} (ID: `{message.from_user.id}`)\n\nТекст: {message.text}"
        
        # Кнопка для админа в другом боте
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{message.from_user.id}")]
        ])
        
        # Отправляем в админ-бот (нужно знать ID админа, либо слать в чат)
        # Для простоты: бот просто пересылает сообщение тебе (замени 12345678 на свой ID)
        YOUR_ID = 12345678 # Впиши сюда свой цифровой ID Telegram
        await admin_bot.send_message(YOUR_ID, user_info, reply_markup=kb, parse_mode="HTML")
        
        await message.answer("✅ **Ваше сообщение отправлено!**\nОжидайте ответа.")
        del users_asking[message.from_user.id]
    else:
        # Тут твоя обычная логика сообщений
        pass
