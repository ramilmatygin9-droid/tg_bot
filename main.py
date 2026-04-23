<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>T-Interface</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --t-yellow: #ffdd2d;
            --t-black: #000000;
            --t-dark-grey: #1a1a1a;
            --t-light-grey: #262626;
            --text-white: #ffffff;
            --text-muted: #929294;
        }

        body {
            background-color: var(--t-black);
            color: var(--text-white);
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            -webkit-user-select: none;
        }

        /* Сториз */
        .stories-container {
            display: flex;
            gap: 12px;
            padding: 16px;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .stories-container::-webkit-scrollbar { display: none; }

        .story-circle {
            min-width: 64px;
            height: 64px;
            border-radius: 50%;
            border: 2px solid var(--t-yellow);
            padding: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .story-inner {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: var(--t-light-grey);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        /* Контент */
        .main-content {
            padding: 0 16px 100px 16px;
        }

        .section-label {
            font-size: 20px;
            font-weight: 700;
            margin: 20px 0 12px 0;
        }

        /* Плитки */
        .grid-services {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .t-card {
            background-color: var(--t-dark-grey);
            border-radius: 20px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 100px;
        }

        .t-card.full-width {
            grid-column: span 2;
            flex-direction: row;
            align-items: center;
            min-height: 60px;
        }

        .card-icon {
            font-size: 28px;
            margin-bottom: 8px;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
        }

        /* Нижнее меню */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            width: 100%;
            background: rgba(26, 26, 26, 0.95);
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            border-top: 0.5px solid #333;
            backdrop-filter: blur(10px);
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            color: var(--text-muted);
            font-size: 11px;
            flex: 1;
        }

        .nav-item.active {
            color: var(--t-yellow);
        }

        .nav-icon {
            font-size: 20px;
        }
    </style>
</head>
<body>

    <div class="stories-container">
        <div class="story-circle"><div class="story-inner">🌟</div></div>
        <div class="story-circle"><div class="story-inner">🎮</div></div>
        <div class="story-circle"><div class="story-inner">🍔</div></div>
        <div class="story-circle"><div class="story-inner">🍿</div></div>
        <div class="story-circle"><div class="story-inner">✈️</div></div>
    </div>

    <div class="main-content">
        <div class="section-label">Сервисы</div>
        
        <div class="grid-services">
            <div class="t-card" onclick="tg.sendData('qr')">
                <div class="card-icon">🔳</div>
                <div class="card-title">Оплата по QR</div>
            </div>
            <div class="t-card" onclick="tg.sendData('transfer')">
                <div class="card-icon">🔄</div>
                <div class="card-title">Переводы</div>
            </div>

            <div class="t-card full-width" onclick="tg.sendData('market')">
                <div class="card-title">Город • Кэшбэк до 30%</div>
                <div style="font-size: 24px;">🛍️</div>
            </div>

            <div class="t-card" onclick="tg.sendData('cards')">
                <div class="card-icon">💳</div>
                <div class="card-title">Мои карты</div>
            </div>
            <div class="t-card" onclick="tg.sendData('safe')">
                <div class="card-icon">🔒</div>
                <div class="card-title">Безопасность</div>
            </div>
        </div>
    </div>

    <div class="bottom-nav">
        <div class="nav-item active">
            <div class="nav-icon">🏠</div>
            <span>Главная</span>
        </div>
        <div class="nav-item">
            <div class="nav-icon">📊</div>
            <span>Платежи</span>
        </div>
        <div class="nav-item">
            <div class="nav-icon">⚙️</div>
            <span>Настройки</span>
        </div>
        <div class="nav-item">
            <div class="nav-icon">🎧</div>
            <span>Поддержка</span>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        tg.headerColor = '#000000';
        tg.backgroundColor = '#000000';

        // Вибрация при нажатии (как в настоящем приложении)
        document.querySelectorAll('.t-card').forEach(item => {
            item.addEventListener('click', () => {
                tg.HapticFeedback.impactOccurred('light');
            });
        });
    </script>
</body>
</html>
