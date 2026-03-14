"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 TELEGRAM BOT - AIOGRAM 3.3.0 (НОВАЯ ВЕРСИЯ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Telegram бот для інтернет-магазину з роутерами та FSM
Features: Mini App, Адмін команди, Сповіщення, Deep Links
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
import sqlite3
from typing import Optional, Dict
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, User as TelegramUser,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

# ═══════════════════════════════════════════════════════════════════
# 📋 КОНФІГУРАЦІЯ
# ═══════════════════════════════════════════════════════════════════

# Bot Token
API_TOKEN = '8140568883:AAFAu9spWaeCuuC52Hb3uYmnwUNtn-VoUgY'

# Admin Configuration
ADMIN_PASSWORD = '123'
ADMIN_IDS = [548995648]  # Список ID адмінів

# Web App URL (ВАЖЛИВО: замените на ваш реальный URL!)
# Используем тестовую страницу для отладки
WEB_APP_URL = 'http://127.0.0.1:8000/test.html'
WEB_APP_DEV = 'http://127.0.0.1:5000'  # Для розробки

# Database
DB_NAME = 'shop.db'

# ═══════════════════════════════════════════════════════════════════
# 🔧 LOGGING
# ═══════════════════════════════════════════════════════════════════

logger.remove()  # Remove default handler
logger.add(
    "logs/bot.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
    level="INFO"
)
logger.add(lambda msg: print(msg, end=""), level="DEBUG")

# ═══════════════════════════════════════════════════════════════════
# 🤖 BOT INITIALIZATION (AiOGRAM 3.x)
# ═══════════════════════════════════════════════════════════════════

# Create bot and dispatcher with memory storage
bot = Bot(token=API_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Create main router
main_router = Router()

# ═══════════════════════════════════════════════════════════════════
# 💾 DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════

def get_db_connection():
    """Отримати з'єднання з БД"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_role(user_id: int) -> str:
    """Отримує роль користувача з БД"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 'user'
    except Exception as e:
        logger.error(f"Database error: {e}")
        return 'user'

def is_admin(user_id: int) -> bool:
    """Перевіряє чи користувач є адміном"""
    if user_id in ADMIN_IDS:
        return True
    role = get_user_role(user_id)
    return role in ['admin', 'manager']

def register_user(user: TelegramUser, role: str = 'user') -> None:
    """Реєструє нового користувача в БД"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, last_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user.id,
            user.username or '',
            user.first_name or '',
            user.last_name or '',
            role,
            datetime.now()
        ))
        conn.commit()
        conn.close()
        logger.info(f"✅ User registered: {user.id} (@{user.username})")
    except Exception as e:
        logger.error(f"Registration error: {e}")

def update_user_role(user_id: int, new_role: str) -> bool:
    """Оновлює роль користувача"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (new_role, user_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Role update error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════
# 🎛️ KEYBOARD BUILDERS
# ═══════════════════════════════════════════════════════════════════

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Головне меню для користувача"""
    buttons = []
    
    # Головна кнопка - магазин
    buttons.append([
        InlineKeyboardButton(
            text="🛍️ Відкрити Магазин",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ])
    
    # Інші кнопки
    buttons.append([
        InlineKeyboardButton(text="📦 Мої замовлення", callback_data="my_orders"),
        InlineKeyboardButton(text="❤️ Вибране", callback_data="favorites")
    ])
    
    # Адмін панель (для адмінів)
    if is_admin(user_id):
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Адмін Панель",
                url=f"{WEB_APP_URL}/admin"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Меню для адміна"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Розсилка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="📦 Замовлення", callback_data="admin_orders"),
            InlineKeyboardButton(text="👥 Користувачі", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(
                text="🌐 Адмін Панель",
                url=f"{WEB_APP_URL}/admin"
            )
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ═══════════════════════════════════════════════════════════════════
# 📊 FSM STATES (Для складних діалогів)
# ═══════════════════════════════════════════════════════════════════

class AdminBroadcastStates(StatesGroup):
    """Стани для відправки розсилки"""
    waiting_for_message = State()
    waiting_for_confirmation = State()

class AdminAuthStates(StatesGroup):
    """Стани для авторизації адміна"""
    waiting_for_password = State()

# ═══════════════════════════════════════════════════════════════════
# 🎬 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════

@main_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обробка команди /start"""
    # Реєстрація користувача
    register_user(message.from_user)
    
    # Парсинг deep link (опціонально)
    # args = message.text.split()
    # if len(args) > 1:
    #     handle_deep_link(args[1])
    
    text = f"""
👋 Привіт, <b>{message.from_user.first_name}</b>!

Ласкаво просимо до нашого магазину електроніки! 🎉

Тут ви можете:
🛍️ Переглядати та купувати товари
📦 Відстежувати ваші замовлення
❤️ Зберігати улюблені товари
💳 Оплачувати онлайн

Натисніть кнопку нижче для початку:
    """
    
    await message.answer(text, reply_markup=get_main_keyboard(message.from_user.id))
    logger.info(f"🚀 User started: {message.from_user.id}")

@main_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Обробка команди /admin з паролем"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(
            "❌ Використання: /admin PASSWORD\n"
            "Введіть пароль адміна."
        )
        return
    
    password = args[1]
    
    if password == ADMIN_PASSWORD:
        update_user_role(message.from_user.id, 'admin')
        await message.answer(
            "✅ Вам надано права адміна!\n\n"
            "Користуйтеся меню нижче:",
            reply_markup=get_admin_keyboard()
        )
        logger.warning(f"⚠️ Admin rights granted to user {message.from_user.id}")
    else:
        await message.answer("❌ Неправильний пароль!")
        logger.warning(f"❌ Wrong admin password attempt from {message.from_user.id}")

@main_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка"""
    text = """
<b>📖 ДОВІДКА</b>

<b>Основні команди:</b>
/start - Головне меню
/orders - Мої замовлення
/favorites - Вибране
/help - Ця довідка

<b>Для адмінів:</b>
/admin PASSWORD - Отримати права адміна

<b>Как використовувати магазин:</b>
1️⃣ Натисніть на кнопку "Відкрити Магазин"
2️⃣ Переглядайте товари, фільтруйте по категоріям
3️⃣ Додавайте в кошик або в вибране
4️⃣ При оформленні замовлення заповніть адресу та телефон
5️⃣ Виберіть спосіб доставки та оплатіть

<b>Потрібна допомога?</b>
Напишіть нам у чат підтримки: @shop_support
    """
    await message.answer(text)

@main_router.message(Command("orders"))
async def cmd_orders(message: Message) -> None:
    """Мої замовлення"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, order_number, status, total, created_at 
            FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (message.from_user.id,))
        
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            await message.answer("📦 У вас поки немає замовлень.")
            return
        
        text = "<b>📦 Ваші останні замовлення:</b>\n\n"
        for order in orders:
            text += (
                f"<b>Замовлення #{order['order_number']}</b>\n"
                f"Статус: {order['status']}\n"
                f"Сума: {order['total']} грн\n"
                f"Дата: {order['created_at']}\n\n"
            )
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Orders error: {e}")
        await message.answer("❌ Помилка при отриманні замовлень.")

@main_router.message(Command("favorites"))
async def cmd_favorites(message: Message) -> None:
    """Вибране"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.price
            FROM favorites f
            JOIN products p ON f.product_id = p.id
            WHERE f.user_id = ?
        ''', (message.from_user.id,))
        
        favorites = cursor.fetchall()
        conn.close()
        
        if not favorites:
            await message.answer("❤️ Ваше вибране пусто.")
            return
        
        text = "<b>❤️ Ваше вибране:</b>\n\n"
        for fav in favorites:
            text += f"• {fav['name']} - {fav['price']} грн\n"
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Favorites error: {e}")
        await message.answer("❌ Помилка при отриманні вибраного.")

# ═══════════════════════════════════════════════════════════════════
# 🔘 CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════════════

@main_router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery) -> None:
    """Повернення на головне меню"""
    await callback.message.edit_text(
        f"👋 Привіт, <b>{callback.from_user.first_name}</b>!\n\n"
        "Що вас цікавить?",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )
    await callback.answer()

@main_router.callback_query(F.data == "my_orders")
async def callback_my_orders(callback: CallbackQuery) -> None:
    """Мої замовлення (callback)"""
    await callback.message.answer(
        "📦 Перейдіть до магазину, щоб переглядати замовлення\n"
        "Або використайте команду /orders"
    )
    await callback.answer()

@main_router.callback_query(F.data == "favorites")
async def callback_favorites(callback: CallbackQuery) -> None:
    """Вибране (callback)"""
    await callback.message.answer(
        "❤️ Перейдіть до магазину для управління виbraным\n"
        "Або використайте команду /favorites"
    )
    await callback.answer()

@main_router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    """Довідка (callback)"""
    await callback.message.edit_text(
        """
<b>📖 ДОВІДКА</b>

📱 <b>Web App Магазин</b>
Натисніть "🛍️ Відкрити Магазин" для повного функціоналу

📦 <b>Замовлення</b>
Вся інформація про замовлення доступна в магазині

❤️ <b>Вибране</b>
Збережіте улюблені товари в додатку

💬 <b>Підтримка</b>
Пишіть нам з питаннями
        """,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

# ═══════════════════════════════════════════════════════════════════
# 👑 ADMIN CALLBACKS
# ═══════════════════════════════════════════════════════════════════

@main_router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery) -> None:
    """Статистика для адміна"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM products")
        products_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        orders_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
        pending_count = cursor.fetchone()['count']
        
        conn.close()
        
        text = f"""
<b>📊 СТАТИСТИКА</b>

👥 Користувачів: {users_count}
🛍️ Товарів: {products_count}
📦 Замовлень: {orders_count}
⏳ Чекають обробки: {pending_count}
        """
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await callback.answer("❌ Помилка при отриманні статистики", show_alert=True)
    
    await callback.answer()

@main_router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Розсилка"""
    await callback.message.answer(
        "📢 Введіть повідомлення для розсилки:"
    )
    await state.set_state(AdminBroadcastStates.waiting_for_message)
    await callback.answer()

@main_router.message(AdminBroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    """Обробка тексту розсилки"""
    await state.update_data(broadcast_message=message.text)
    
    buttons = [
        [
            InlineKeyboardButton(text="✅ Відправити", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Скасувати", callback_data="broadcast_cancel")
        ]
    ]
    
    await message.answer(
        f"Попередній перегляд розсилки:\n\n{message.text}\n\n"
        "Відправити всім користувачам?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@main_router.callback_query(F.data == "broadcast_confirm", AdminBroadcastStates.waiting_for_message)
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Підтвердження розсилки"""
    data = await state.get_data()
    message_text = data.get("broadcast_message")
    
    if not message_text:
        await callback.answer("❌ Помилка: текст не знайдено", show_alert=True)
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE blocked = 0")
        users = cursor.fetchall()
        conn.close()
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await bot.send_message(user['user_id'], message_text)
                sent += 1
            except TelegramBadRequest:
                failed += 1
            except Exception as e:
                logger.error(f"Broadcast error for user {user['user_id']}: {e}")
                failed += 1
        
        await callback.message.answer(
            f"✅ Розсилка завершена!\n"
            f"Відправлено: {sent}\n"
            f"Помилок: {failed}"
        )
        
        logger.info(f"📢 Broadcast sent to {sent} users, {failed} failed")
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await callback.answer("❌ Помилка при розсилці", show_alert=True)
    
    await state.clear()
    await callback.answer()

@main_router.callback_query(F.data == "broadcast_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Скасування розсилки"""
    await state.clear()
    await callback.message.answer("❌ Розсилка скасована")
    await callback.answer()

@main_router.callback_query(F.data == "admin_orders")
async def callback_admin_orders(callback: CallbackQuery) -> None:
    """Замовлення для управління"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, order_number, user_id, status, total
            FROM orders
            WHERE status IN ('pending', 'new')
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            await callback.answer("Немає чекаючих замовлень")
            return
        
        text = "<b>📦 Замовлення, що чекають обробки:</b>\n\n"
        for order in orders:
            text += (
                f"<b>№{order['order_number']}</b> | "
                f"користувач: {order['user_id']} | "
                f"{order['total']} грн\n"
            )
        
        await callback.message.answer(text)
    except Exception as e:
        logger.error(f"Orders error: {e}")
        await callback.answer("❌ Помилка", show_alert=True)
    
    await callback.answer()

@main_router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery) -> None:
    """Користувачі"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role IN ('admin', 'manager')")
        staff_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE blocked = 1")
        blocked_users = cursor.fetchone()['count']
        
        conn.close()
        
        text = f"""
<b>👥 КОРИСТУВАЧІ</b>

📊 Всього: {total_users}
👔 Персонал: {staff_users}
🚫 Заблоковано: {blocked_users}
        """
        
        await callback.message.answer(text)
    except Exception as e:
        logger.error(f"Users error: {e}")
        await callback.answer("❌ Помилка", show_alert=True)
    
    await callback.answer()

# ═══════════════════════════════════════════════════════════════════
# 👤 TEXT MESSAGE HANDLERS
# ═══════════════════════════════════════════════════════════════════

@main_router.message()
async def handle_text(message: Message) -> None:
    """Обробка звичайних текстових повідомлень"""
    await message.answer(
        "Вибачте, я розумію тільки команди.\n\n"
        "Використайте /help для списку команд або "
        "натисніть '🛍️ Відкрити Магазин' для покупок."
    )

# ═══════════════════════════════════════════════════════════════════
# 🔗 REGISTER ROUTERS
# ═══════════════════════════════════════════════════════════════════

dp.include_router(main_router)

# ═══════════════════════════════════════════════════════════════════
# 🚀 STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════

async def on_startup() -> None:
    """При запуску бота"""
    logger.info("🚀 Bot starting...")
    logger.info(f"🌐 Web App URL: {WEB_APP_URL}")

async def on_shutdown() -> None:
    """При зупинці бота"""
    logger.info("⛔ Bot shutting down...")
    await bot.session.close()

async def main() -> None:
    """Головна функція запуску бота"""
    logger.info("━" * 60)
    logger.info("🤖 TELEGRAM BOT v3.3.0 (Aiogram 3.x)")
    logger.info("━" * 60)
    
    # Запустити бота
    try:
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        await on_startup()
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    finally:
        await on_shutdown()

# ═══════════════════════════════════════════════════════════════════
# 🏃 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # For sync entry point, use asyncio.run()
    asyncio.run(main())
    
    """
    MIGRATION FROM AIOGRAM 2.x to 3.x:
    ─────────────────────────────────────
    1. Removed: executor.start_polling(dp, ...)
    2. Added: dp.start_polling(bot, ...)
    
    3. Router instead of Dispatcher message handlers
    4. F filter instead of lambda_handler
    
    5. FSM: fsm.storage instead of storage in Dispatcher
    
    6. No more @dp.message_handler()
       Use: @main_router.message(CommandStart())
    
    7. CallbackQuery -> callback: CallbackQuery type hint
    
    Перевагі новой версії:
    ✅ Краща типізація (Type Hints)
    ✅ Модульна структура (Router)
    ✅ Асинхронність за замовчуванням
    ✅ Краща обробка помилок
    ✅ Нативна підтримка Telegram Bot API 7.x
    """
