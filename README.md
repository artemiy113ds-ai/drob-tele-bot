# 🛍️ Telegram Mini App E-Commerce Platform

**Повнофункціональний інтернет-магазин електроніки всередині Telegram з адмін-панеллю, інтеграцією Нової Пошти, геймфікацією та аналітикою.**

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688)
![Aiogram](https://img.shields.io/badge/aiogram-3.3.0-2196F3)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Зміст

- [🎯 Особливості](#-особливості)
- [🛠️ Технічний стек](#-технічний-стек)
- [🚀 Встановлення](#-встановлення)
- [📦 Розгортання](#-розгортання)
- [📚 API документація](#-api-документація)
- [🤝 Внесення змін](#-внесення-змін)
- [📄 Ліцензія](#-ліцензія)

---

## 🎯 Особливості

### 👤 Користувацька Частина (Mini App)
- 🏠 **Головна сторінка** з Instagram Stories, банерами та каталогом
- 📱 **3D Sidebar меню** з анімаціями та модульним дизайном
- 🛍️ **Каталог товарів** з розширеним пошуком, фільтрами та сортуванням
- ❤️ **Вибране (Wishlist)** з можливістю додавання сповіщень
- 🛒 **Кошик** з детальним розрахунком, промокодами та доставкою
- 📦 **Інтеграція Нової Пошти** - пошук міст, відділення, створення ТТН
- 📧 **Історія замовлень** з відстеженням статусів та ТТН
- 🎮 **Геймфікація** - рівні, досягнення, щоденні завдання, очки

### ⚙️ Адмін-Панель
- 📊 **Dashboard** зі статистикою та графіками
- 📦 **CRUD товарів** з варіантами, фото, SEO атрибутами
- 🗂️ **Управління категоріями & брендами**
- 📮 **Управління замовленнями** - зміна статусів, розрахунки, ТТН
- 🎟️ **Промокоди** з таргетингом та статистикою
- 📸 **Stories & Banners** - завантаження, редагування
- 📢 **Розсилка** по сегментам користувачів
- 👥 **Користувачі** з RFM аналізом та сегментацією
- 🧩 **Модерація відгуків** - підтвердження, відповіді

### 🤖 Telegram Бот (Aiogram 3.x)
- `/start` - Головне меню з посиланням на магазин
- `/admin PASSWORD` - Отримання прав адміна
- `/orders` - Мої замовлення
- `/favorites` - Вибране
- 📬 **Deep Links** для товарів та замовлень
- 🔔 **Push-сповіщення** про замовлення та статуси
- 📢 **Розсилка** адміном до користувачів

### 🚀 Advanced Features
- **Геймфікація**: Рівні (Bronze→Silver→Gold→Platinum), досягнення, бейджі, щоденні завдання
- **Реферальна програма**: Кожен користувач має унікальне посилання, бонуси за запрошення
- **Wishlist Alerts**: Сповіщення коли товар в наявності, подешевшав
- **RFM сегментація**: Автоматичне розподілення користувачів на сегменти
- **Історія цін**: Графік зміни цін товарів за час
- **Порівняння товарів**: Порівняння характеристик side-by-side
- **Q&A секція**: Користувачі можуть задавати питання до товарів

---

## 🛠️ Технічний Стек

### Backend
- **Python 3.12+** - Мова програмування
- **FastAPI 0.109.0** - Сучасний web-фреймворк з async/await
- **Aiogram 3.3.0** - Telegram Bot API wrapper (нова версія з роутерами)
- **SQLite3** - База даних (готова до міграції на PostgreSQL)
- **Uvicorn** - ASGI сервер для FastAPI
- **Loguru** - Професійне логування

### Frontend
- **Vanilla JavaScript (ES6+)** - Без залежностей для мінімального бандла
- **Telegram Web App SDK** - Інтеграція з Telegram Mini App
- **Swiper.js** - Слайдери та карусель
- **CSS3** з підтримкою Telegram темної теми
- **LocalStorage API** - Синхронізація кошика, вибраного

### DevOps & Deployment
- **Docker** - Контейнеризація додатку
- **Docker Compose** - Оркестрування сервісів
- **Nginx** - Reverse proxy та статичні файли
- **Redis** - Кешування та сесії (опціонально)
- **PostgreSQL** - Альтернатива SQLite для production

---

## 🚀 Встановлення

### 1️⃣ Вимоги
```bash
- Python 3.12+
- Git
- pip та virtualenv
- Docker та Docker Compose (для контейнеризації)
```

### 2️⃣ Клонування репозиторію
```bash
git clone https://github.com/yourusername/telegram-shop.git
cd telegram-shop
```

### 3️⃣ Встановлення залежностей
```bash
# Створити virtual environment
python -m venv venv

# Активувати (Linux/Mac)
source venv/bin/activate

# Активувати (Windows)
venv\Scripts\activate

# Встановити залежності
pip install -r requirements.txt
```

### 4️⃣ Конфігурація
```bash
# Скопіювати .env файл
cp .env.example .env

# Редагувати .env з вашими ключами
nano .env
```

**Важливі змінні в .env:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_PASSWORD=123
NOVA_POSHTA_API_KEY=your_key
```

### 5️⃣ Запуск на локалці
```bash
# Terminal 1: Запустити Telegram Bot
python bot_v3.py

# Terminal 2: Запустити FastAPI сервер
uvicorn main_v3:app --reload --host 0.0.0.0 --port 8000
```

**Додатки будуть доступні:**
- 📱 Mini App: http://127.0.0.1:8000
- ⚙️ Admin Panel: http://127.0.0.1:8000/admin
- 📚 API Docs: http://127.0.0.1:8000/api/docs

---

## 📦 Розгортання

### Використання Docker Compose (Рекомендується)

```bash
# 1. Побудувати образи
docker-compose build

# 2. Запустити всі сервіси
docker-compose up -d

# 3. Перевірити статус
docker-compose ps

# 4. Переглянути логи
docker-compose logs -f api
docker-compose logs -f bot
```

**Доступні сервіси:**
- 🌐 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/api/docs
- 💾 Redis: localhost:6379
- 🔒 HTTPS: https://localhost (після налаштування SSL сертифіката)

### Зупинка сервісів
```bash
docker-compose down

# Видалити томи (осторожно!)
docker-compose down -v
```

### Production Deployment

#### Варіант 1: DigitalOcean / Linode / Heroku
```bash
# 1. Push на Git
git push origin main

# 2. На сервері:
git clone <your-repo>
cd telegram-shop
docker-compose -f docker-compose.prod.yml up -d
```

#### Варіант 2: AWS / Google Cloud
Див. `docs/deployment-cloud.md`

#### Варіант 3: VPS (Ubuntu 22.04)
```bash
# 1. Встановити Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Встановити Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Клонувати проект
git clone <your-repo>
cd telegram-shop

# 4. Налаштувати .env
nano .env

# 5. Запустити
docker-compose up -d
```

---

## 📚 API Документація

FastAPI автоматично генерує інтерактивну документацію Swagger:

📖 **OpenAPI (Swagger)**: http://localhost:8000/api/docs
📖 **ReDoc**: http://localhost:8000/api/redoc

### Основні Endpoints

#### 🔐 Auth
```
POST /api/auth/login              - Вхід користувача
GET  /api/user/balance            - Баланс користувача
```

#### 📦 Products
```
GET  /api/products                - Список товарів (фільтри, пошук)
GET  /api/product/{id}            - Деталі товара
POST /api/product                 - Створити товар (адмін)
POST /api/product/delete          - Видалити товар (адмін)
```

#### 🛒 Orders
```
POST /api/order/create            - Створити замовлення
POST /api/order/status            - Змінити статус (адмін)
POST /api/orders                  - Список замовлень користувача
```

#### 📮 Nova Poshta
```
GET  /api/np/cities               - Пошук міст
GET  /api/np/warehouses           - Відділення міста
POST /api/create_ttn              - Створити ТТН (адмін)
```

#### ❤️ Favorites
```
POST /api/favorite/toggle         - Додати/видалити з вибраного
POST /api/favorites/list          - Список вибраного
```

#### 🎟️ Promocodes
```
POST /api/promocode/validate      - Перевіра промокоду
POST /api/promocode               - Створити промокід (адмін)
```

Повна документація див. **[API.md](docs/API.md)**

---

## 🧪 Тестування

### Юніт-тести
```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

### Інтеграційні тести
```bash
pytest tests/integration/ -v
```

### Тестування бота
```bash
python tests/test_bot.py
```

---

## 📁 Структура Проекту

```
telegram-shop/
├── .env                    # Конфігурація (НІКОЛИ не комітьте!)
├── requirements.txt        # Python залежності
├── Dockerfile             # Docker образ
├── docker-compose.yml     # Сервіси (API, Bot, Redis, Nginx)
├── nginx.conf             # Nginx конфіг для reverse proxy
│
├── bot_v3.py              # 🤖 Telegram Bot (Aiogram 3.x)
├── main_v3.py             # 🚀 FastAPI веб-сервер
├── database.py            # 💾 База даних (20+ таблиці)
├── gamification.py        # 🎮 Геймфікація, рефереали
├── nova_poshta.py         # 📮 Інтеграція Нової Пошти
│
├── index.html             # 📱 Mini App (Telegram WebApp)
├── admin.html             # ⚙️ Адмін-панель
├── style.css              # 🎨 Стилі
├── script.js              # ⚡ JavaScript логіка
│
├── static/
│   ├── uploads/           # Завантажені фото товарів
│   ├── banners/           # Зображення банерів
│   └── images/            # Статичні зображення
│
├── logs/
│   ├── api.log            # Логи FastAPI
│   └── bot.log            # Логи Telegram Bot
│
├── docs/
│   ├── API.md             # API документація
│   ├── DEPLOYMENT.md      # Інструкції по развертыванню
│   └── ARCHITECTURE.md    # Архітектура системи
│
└── tests/
    ├── test_api.py        # Тести API endpoints
    ├── test_bot.py        # Тести бота
    └── test_gamification.py # Тести геймфікації
```

---

## 🔧 Управління БД

### Ініціалізація БД
```python
from database import init_db
from gamification import create_gamification_tables

init_db()                           # Основна схема
create_gamification_tables()        # Геймфікація
```

### Резервне копіювання
```bash
# SQLite
cp shop.db shop.db.backup

# Або скрипт
python scripts/backup_db.py
```

### Міграція на PostgreSQL
Див. `docs/POSTGRESQL_MIGRATION.md`

---

## 🚀 Швидкий Старт (TL;DR)

```bash
# Clone & Setup
git clone <repo>
cd telegram-shop
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Set TELEGRAM_BOT_TOKEN & ADMIN_PASSWORD

# Run with Docker
docker-compose up -d

# Or run locally
python bot_v3.py &
uvicorn main_v3:app --reload

# Open browser
open http://localhost:8000
```

---

## 🤝 Внесення Змін

### Contributing Guidelines
1. Fork проект
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style
- Python: PEP 8, use `black` для форматування
- JavaScript: ESLint конфіг `.eslintrc.json`
- Усі функції мають мати docstrings & type hints

---

## 📄 Ліцензія

Проект розповсюджується під MIT License. Див. [LICENSE](LICENSE)

---

## 📞 Контакти & Підтримка

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/telegram-shop/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/telegram-shop/discussions)
- 📧 **Email**: support@yourshop.com
- 💬 **Telegram**: [@YourShopSupport](https://t.me/yourshopsupport)

---

## 📊 Статистика Проекту

- 📦 **20+ таблиці БД**
- 📚 **40+ API endpoints**
- 🎮 **10+ досягнень**
- 🤖 **Повна інтеграція Telegram**
- 🚀 **Production-ready**

---

## 🎓 Навчальні Ресурси

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Aiogram 3.x Docs](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [WebApp Documentation](https://core.telegram.org/bots/webapps)

---

**Зроблено з ❤️ для українських бізнесменів**

⭐ Якщо проект вам допоміг, дайте зірку!
