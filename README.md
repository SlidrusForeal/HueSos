# ZeWorld - Платформа для вирусного маркетинга

Профессиональное решение для создания вирусных кампаний с расширенной аналитикой и интеграцией с мессенджерами.

## Особенности

- 🎣 Генерация кликбейтных превью с Open Graph разметкой
- 📊 Система отслеживания кликов и аналитики в реальном времени
- 🛡 Встроенная защита от ботов и VPN/прокси
- 🤖 Интеграция с Discord для мгновенных уведомлений
- 📈 Автоматическое ведение статистики в PostgreSQL
- 🔐 Админ-панель с RBAC (Role-Based Access Control)
- ⏳ Настраиваемые редиректы с задержкой

## Технологический стек

- **Backend**: Python + Flask
- **Database**: PostgreSQL
- **Аналитика**: ip-api.com + кастомная логика
- **Шаблоны**: HTML5 + CSS3 анимации
- **Безопасность**: Advanced bot detection

## Требования

- Python 3.10+
- PostgreSQL 14+
- Библиотеки: `requirements.txt`

## Быстрый старт

1. Клонировать репозиторий:
```bash
git clone https://github.com/yourrepo/zeworld.git
cd zeworld
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настройка окружения:
```bash
cp .env.example .env
# Заполнить значения в .env файле
```

4. Запустить приложение:
```bash
flask run --host=0.0.0.0 --port=5000
```

## Конфигурация (.env)

```ini
SECRET_KEY=your-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strongpassword!
REAL_URL=https://your-domain.com
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
REDIRECT_DELAY=5
LOGGING_LEVEL=INFO
VPN_CHECK=1 # 0-выкл, 1-опционально, 2-блокировка
ANTI_BOT=3  # Уровень защиты от ботов (1-4)
```

## Администрирование

Доступ к панели: `/admin`

**Функционал:**
- Создание/редактирование ссылок
- Просмотр статистики кликов
- Управление превью-контентом
- Кастомизация редиректов
- Экспорт данных в CSV

## Пример использования

Создание вирусной ссылки:
```python
{
    "path": "shocking-news",
    "title": "🔥 ШОК! Этот секрет скрывали 100 лет!",
    "description": "Узнай правду, пока не поздно...",
    "image_url": "https://example.com/preview.jpg",
    "redirect_url": "https://your-domain.com/content",
    "redirect_delay": 7
}
```

Получите ссылку вида:  
`https://your-domain.com/shocking-news`

## Система защиты

1. **Bot Detection**:
   - Анализ User Agent
   - Проверка ASN/IP диапазонов
   - Хостинг/VPN детекция

2. **Анти-скрейпинг**:
   - Rate Limiting
   - Honeypot-ловушки
   - Защита от headless-браузеров

3. **Мониторинг**:
   - Real-time алерты в Discord
   - Логирование всех запросов
   - Гео-аналитика

## Лицензия

GNU GPLv3. Использование в коммерческих целях требует покупки лицензии.

**Важно!** Запрещено использование для:
- Фишинговых сайтов
- Распространения вредоносного ПО
- Обхода блокировок РКН
