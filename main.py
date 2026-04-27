<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #ffffff; color: #333; margin: 0; padding: 0; }
        
        /* Профиль и Опыт */
        .header { padding: 20px; background: #fafafa; border-bottom: 1px solid #eee; }
        .lvl-container { width: 100%; height: 8px; background: #eee; border-radius: 4px; margin-top: 10px; overflow: hidden; }
        .lvl-bar { height: 100%; background: #0088cc; width: 0%; transition: width 0.5s; }
        .balance { font-size: 26px; font-weight: bold; color: #27ae60; margin: 5px 0; }

        /* Кейсы и Карточки */
        .section-title { padding: 20px 20px 5px; font-size: 14px; color: #888; text-transform: uppercase; }
        .case-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; }
        .case-item { background: #fff; border: 1px solid #eee; border-radius: 20px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center; transition: 0.2s; }
        .case-item:active { transform: scale(0.95); }
        .case-icon { font-size: 40px; margin-bottom: 10px; }

        /* Всплывающее окно приза */
        #win-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.95); z-index: 100; flex-direction: column; align-items: center; justify-content: center; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .win-amount { font-size: 48px; font-weight: bold; color: #f1c40f; margin: 20px; }

        /* Навигация */
        .nav { position: fixed; bottom: 0; width: 100%; display: flex; background: white; border-top: 1px solid #eee; padding-bottom: env(safe-area-inset-bottom); }
        .nav-btn { flex: 1; padding: 15px; border: none; background: none; font-weight: bold; color: #888; }
        .nav-btn.active { color: #0088cc; }
    </style>
</head>
<body>

<div class="header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span id="rank-text">🍀 Новичок</span>
        <span style="font-weight: bold;">Lvl <span id="lvl-num">1</span></span>
    </div>
    <div class="lvl-container"><div id="lvl-bar" class="lvl-bar"></div></div>
    <div class="balance" id="balance">1000 💰</div>
</div>

<div id="page-cases">
    <div class="section-title">Доступные кейсы</div>
    <div class="case-grid">
        <div class="case-item" onclick="openCase(100, '🎁')">
            <div class="case-icon">🎁</div>
            <b>Бомж-кейс</b><br>
            <small>100 💰</small>
        </div>
        <div class="case-item" onclick="openCase(1000, '💎')">
            <div class="case-icon">💎</div>
            <b>VIP кейс</b><br>
            <small>1000 💰</small>
        </div>
        <div class="case-item" onclick="openCase(5000, '👑')">
            <div class="case-icon">👑</div>
            <b>Royal кейс</b><br>
            <small>5000 💰</small>
        </div>
        <div class="case-item" onclick="openCase(0, '🕒')" style="border-style: dashed; opacity: 0.6;">
            <div class="case-icon">🕒</div>
            <b>Скоро...</b>
        </div>
    </div>
</div>

<div id="win-modal">
    <div style="font-size: 20px;">ТЕБЕ ВЫПАЛО:</div>
    <div class="win-amount" id="win-display">0</div>
    <button onclick="closeModal()" style="padding: 12px 40px; border-radius: 25px; border: none; background: #333; color: white; font-weight: bold;">ЗАБРАТЬ</button>
</div>

<div class="nav">
    <button class="nav-btn active">КЕЙСЫ</button>
    <button class="nav-btn" onclick="alert('Инвентарь в разработке!')">ИНВЕНТАРЬ</button>
</div>

<script>
    let tg = window.Telegram.WebApp;
    let balance = 1000;
    let xp = 0;
    let lvl = 1;
    tg.expand();

    function openCase(price, icon) {
        if (balance < price) {
            tg.showAlert("Недостаточно средств! Кликай больше.");
            return;
        }

        balance -= price;
        xp += Math.floor(price / 10) + 5; // Даем опыт за открытие
        
        // Логика выигрыша (шансы)
        let win = 0;
        let rand = Math.random();
        if (price === 100) win = rand < 0.1 ? 500 : Math.floor(rand * 150);
        if (price === 1000) win = rand < 0.05 ? 10000 : Math.floor(rand * 2500);
        if (price === 5000) win = rand < 0.02 ? 50000 : Math.floor(rand * 12000);

        balance += win;
        checkLvl();
        updateUI();

        // Показываем анимацию выигрыша
        document.getElementById('win-display').innerText = win + " 💰";
        document.getElementById('win-modal').style.display = 'flex';
        tg.HapticFeedback.notificationOccurred('success');
    }

    function checkLvl() {
        let nextLvlXp = lvl * 100;
        if (xp >= nextLvlXp) {
            xp -= nextLvlXp;
            lvl++;
            tg.showPopup({title: "УРОВЕНЬ UP!", message: `Поздравляем! Теперь у тебя ${lvl} уровень!`});
        }
        
        // Ранги
        let ranks = ["Новичок", "Игрок", "Опытный", "Мастер", "Миллионер", "Шейх"];
        let rankIdx = Math.min(Math.floor(lvl / 3), ranks.length - 1);
        document.getElementById('rank-text').innerText = "🍀 " + ranks[rankIdx];
    }

    function updateUI() {
        document.getElementById('balance').innerText = balance + " 💰";
        document.getElementById('lvl-num').innerText = lvl;
        let progress = (xp / (lvl * 100)) * 100;
        document.getElementById('lvl-bar').style.width = progress + "%";
    }

    function closeModal() {
        document.getElementById('win-modal').style.display = 'none';
    }

    updateUI();
</script>
</body>
</html>
