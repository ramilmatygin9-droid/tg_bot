# --- ИГРА: РАКЕТА (X-МНОЖИТЕЛИ) ---
@dp.callback_query(F.data == "game_rocket")
async def rocket_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Низко (x1.5)", callback_data="fly_1.5")],
        [InlineKeyboardButton(text="🚀 Средне (x2.0)", callback_data="fly_2.0")],
        [InlineKeyboardButton(text="🚀 Высоко (x5.0)", callback_data="fly_5.0")],
        [InlineKeyboardButton(text="🌌 В космос (x10.0)", callback_data="fly_10.0")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="all_games")]
    ])
    await callback.message.edit_text(
        "🚀 **ЗАПУСК РАКЕТЫ**\n\nВыбери высоту полета. Чем выше, тем больше риск взрыва!",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("fly_"))
async def rocket_fly(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    bet = 100  # Ставка за полет
    
    if user["balance"] < bet:
        return await callback.answer("Недостаточно коинов! (Нужно 100)", show_alert=True)
    
    user["balance"] -= bet
    multiplier = float(callback.data.split("_")[1])
    
    # Логика шанса: чем выше множитель, тем ниже шанс успеха
    # x1.5 -> 70% шанс | x2 -> 45% | x5 -> 15% | x10 -> 5%
    chance = 0
    if multiplier == 1.5: chance = 70
    elif multiplier == 2.0: chance = 45
    elif multiplier == 5.0: chance = 15
    elif multiplier == 10.0: chance = 5

    await callback.message.edit_text(f"🚀 Ракета взлетает на множитель **x{multiplier}**... 💨", parse_mode="Markdown")
    await asyncio.sleep(2) # Эффект ожидания

    if random.randint(1, 100) <= chance:
        win_amount = int(bet * multiplier)
        user["balance"] += win_amount
        await callback.message.answer(f"✅ УСПЕХ! Ракета долетела! Твой выигрыш: **{win_amount}** коинов!", parse_mode="Markdown")
    else:
        await callback.message.answer(f"💥 БА-БАХ! Ракета взорвалась на полпути... Ты потерял {bet} коинов.")
    
    await all_games(callback)
