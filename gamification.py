"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 GAMIFICATION & ADVANCED FEATURES MODULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Додаткові таблиці для геймфікації, рефереалів, та advanced функціоналу
Інтегрується з основним database.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from database import get_db_connection
from loguru import logger

# ═══════════════════════════════════════════════════════════════════
# 🎮 GAMIFICATION TABLES
# ═══════════════════════════════════════════════════════════════════

def create_gamification_tables():
    """Створює таблиці для геймфікації"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("Creating gamification tables...")
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ LOYALTY TIERS (Рівні лояльності)                            │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            level INTEGER UNIQUE NOT NULL,
            
            -- Вимоги для рівня
            min_points INTEGER DEFAULT 0,
            min_orders INTEGER DEFAULT 0,
            min_spent REAL DEFAULT 0,
            
            -- Привілеї
            discount_percent REAL DEFAULT 0,
            free_shipping_orders INTEGER DEFAULT 0,
            bonus_multiplier REAL DEFAULT 1.0,
            
            -- Символи рівня
            icon TEXT,
            color TEXT DEFAULT '#FFFFFF',
            description TEXT,
            
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Базові рівні
    cursor.execute('''
        INSERT OR IGNORE INTO loyalty_tiers 
        (name, level, min_points, min_orders, min_spent, discount_percent, bonus_multiplier, icon, color)
        VALUES 
        ('Bronze', 1, 0, 0, 0, 0, 1.0, '🥉', '#CD7F32'),
        ('Silver', 2, 500, 3, 3000, 5, 1.2, '🥈', '#C0C0C0'),
        ('Gold', 3, 1500, 10, 10000, 10, 1.5, '🥇', '#FFD700'),
        ('Platinum', 4, 3000, 25, 25000, 15, 2.0, '💎', '#E5E4E2')
    ''')
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ USER LEVELS (Рівні користувачів)                            │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_levels (
            user_id INTEGER PRIMARY KEY,
            
            -- Рівень та очки
            current_level INTEGER DEFAULT 1,
            total_points INTEGER DEFAULT 0,
            points_this_month INTEGER DEFAULT 0,
            
            -- Рівень лояльності
            loyalty_tier_id INTEGER DEFAULT 1,
            tier_progress_percent REAL DEFAULT 0,
            
            -- Чемпіонати та лідерборди
            monthly_rank INTEGER,
            yearly_rank INTEGER,
            all_time_rank INTEGER,
            leaderboard_position INTEGER,
            
            -- Нові события
            level_up_at TIMESTAMP,
            tier_up_at TIMESTAMP,
            
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(loyalty_tier_id) REFERENCES loyalty_tiers(id)
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_levels_tier 
                      ON user_levels(loyalty_tier_id)''')
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ ACHIEVEMENTS (Досягнення)                                    │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            category TEXT,
            
            -- Умови
            trigger_type TEXT NOT NULL,
            trigger_value TEXT,
            
            -- Нагороди
            points_reward INTEGER DEFAULT 0,
            bonus_reward REAL DEFAULT 0,
            badge_image TEXT,
            
            -- Налаштування
            is_hidden INTEGER DEFAULT 0,
            is_secret INTEGER DEFAULT 0,
            rarity TEXT DEFAULT 'common',
            
            unlock_count INTEGER DEFAULT 0,
            
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Базові досягнення
    achievements_data = [
        ('first_purchase', 'Перша покупка', 'Зробили першу покупку в магазині', '🛍️', 'milestone', 
         'first_order', NULL, 50, 5.0),
        ('loyal_customer', 'Постійний клієнт', 'Зробили 10 замовлень', NULL, 'milestone', 
         'order_count', '10', 100, 10.0),
        ('shopaholic', 'Шопоголік', 'Витратили 50,000 грн', '🛒', 'milestone', 
         'total_spent', '50000', 500, 50.0),
        ('review_critic', 'Критик', 'Залишили 5 відгуків', '✍️', 'milestone', 
         'review_count', '5', 50, 10.0),
        ('wishlist_collector', 'Колекціонер', 'Додали 20 товарів в вибране', '❤️', 'milestone', 
         'wishlist_count', '20', 75, 15.0),
        ('super_referrer', 'Супер рефер', 'Запросили 5 друзів до магазину', '👥', 'referral', 
         'referral_count', '5', 200, 25.0),
        ('weekend_warrior', 'Воїн вихідного', 'Зробили покупку у вихідний день', '🌙', 'special', 
         'weekend_purchase', NULL, 25, 5.0),
    ]
    
    for achievement in achievements_data:
        cursor.execute('''
            INSERT OR IGNORE INTO achievements 
            (name, description, icon, category, trigger_type, trigger_value, 
             points_reward, bonus_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', achievement)
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ USER ACHIEVEMENTS (Досягнення користувачів)                 │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0,
            is_notified INTEGER DEFAULT 0,
            
            UNIQUE(user_id, achievement_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_achievements_user 
                      ON user_achievements(user_id)''')
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ DAILY TASKS (Щоденні завдання)                              │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            
            task_type TEXT NOT NULL,
            task_target INTEGER,
            
            -- Нагороди
            points_reward INTEGER DEFAULT 0,
            bonus_reward REAL DEFAULT 0,
            
            -- Період
            cycle TEXT DEFAULT 'daily',
            reset_time TEXT DEFAULT '03:00',
            
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Default tasks
    tasks_data = [
        ('Додай в вибране', 'Додай 3 товари в вибране', '❤️', 'wishlist', 3, 10, 2.0),
        ('Залиш огляд', 'Залиш огляд на товар', '⭐', 'review', 1, 20, 5.0),
        ('Виконай покупку', 'Зробили замовлення', '🛍️', 'purchase', 1, 50, 10.0),
        ('Запроси друга', 'Запроси одного друга в магазин', '👥', 'referral', 1, 100, 25.0),
    ]
    
    for task in tasks_data:
        cursor.execute('''
            INSERT OR IGNORE INTO daily_tasks 
            (title, description, icon, task_type, task_target, 
             points_reward, bonus_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', task)
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ USER DAILY TASKS (Прогрес користувачів в завданнях)        │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            
            progress INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            
            date_assigned DATE DEFAULT CURRENT_DATE,
            
            UNIQUE(user_id, task_id, date_assigned),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(task_id) REFERENCES daily_tasks(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_tasks_user_date 
                      ON user_daily_tasks(user_id, date_assigned)''')
    
    # ═══════════════════════════════════════════════════════════════
    # 🤝 REFERRAL SYSTEM TABLES
    # ═══════════════════════════════════════════════════════════════
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ REFERRAL REWARDS (Реверальні нагороди)                     │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            
            -- События
            reward_type TEXT DEFAULT 'signup',
            amount REAL NOT NULL,
            
            description TEXT,
            
            -- Обробка
            is_processed INTEGER DEFAULT 0,
            processed_at TIMESTAMP,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY(referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(referred_user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_referral_referrer 
                      ON referral_rewards(referrer_id, created_at)''')
    
    # ═══════════════════════════════════════════════════════════════
    # 💰 GAMIFICATION POINTS LOG
    # ═══════════════════════════════════════════════════════════════
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            
            amount INTEGER NOT NULL,
            operation_type TEXT NOT NULL,
            reason TEXT,
            
            source_entity_type TEXT,
            source_entity_id INTEGER,
            
            previous_balance INTEGER DEFAULT 0,
            new_balance INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_points_user 
                      ON points_log(user_id, created_at)''')
    
    # ═══════════════════════════════════════════════════════════════
    # 🔔 WISHLIST ALERTS SYSTEM
    # ═══════════════════════════════════════════════════════════════
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ WISHLIST ALERTS (Сповіщення про бажане)                    │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishlist_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            
            -- Типи сповіщень
            alert_type TEXT DEFAULT 'back_in_stock',
            
            -- Параметри сповіщення
            price_drop_percent REAL,
            min_alert_price REAL,
            
            -- Статус
            is_active INTEGER DEFAULT 1,
            is_notified INTEGER DEFAULT 0,
            last_notified_at TIMESTAMP,
            
            -- Логування
            alert_triggered_count INTEGER DEFAULT 0,
            last_triggered_at TIMESTAMP,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_wishlist_alerts_user 
                      ON wishlist_alerts(user_id, is_active)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_wishlist_alerts_product 
                      ON wishlist_alerts(product_id, is_active)''')
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 PRICE HISTORY & ANALYTICS
    # ═══════════════════════════════════════════════════════════════
    
    # ┌─────────────────────────────────────────────────────────────┐
    # │ PRODUCT PRICE HISTORY (Історія цін товарів)                │
    # └─────────────────────────────────────────────────────────────┘
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            
            price REAL NOT NULL,
            old_price REAL,
            
            change_reason TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        )
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_price_history_product 
                      ON product_price_history(product_id, created_at)''')
    
    # Commit all changes
    conn.commit()
    logger.info("✅ Gamification tables created successfully")
    
    conn.close()

# ═══════════════════════════════════════════════════════════════════
# 🎮 GAMIFICATION BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════════

def add_points(user_id: int, points: int, reason: str, source_type: str = None, 
               source_id: int = None) -> bool:
    """Добавляє очки користувачу з логуванням"""
    try:
        conn = get_db_connection()
        
        # Отримати поточний баланс
        user = conn.execute(
            "SELECT total_points FROM user_levels WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        current_balance = user['total_points'] if user else 0
        new_balance = current_balance + points
        
        # Надати очки
        conn.execute('''
            INSERT INTO user_levels (user_id, total_points, points_this_month)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_points = total_points + ?,
                points_this_month = points_this_month + ?
        ''', (user_id, points, points, points, points))
        
        # Залогувати операцію
        conn.execute('''
            INSERT INTO points_log 
            (user_id, amount, operation_type, reason, source_entity_type, 
             source_entity_id, previous_balance, new_balance)
            VALUES (?, ?, 'add', ?, ?, ?, ?, ?)
        ''', (user_id, points, reason, source_type, source_id, current_balance, new_balance))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Added {points} points to user {user_id}: {reason}")
        return True
    
    except Exception as e:
        logger.error(f"Points addition error: {e}")
        return False

def unlock_achievement(user_id: int, achievement_id: int) -> bool:
    """Розблоковує досягнення для користувача"""
    try:
        conn = get_db_connection()
        
        # Отримати досягнення
        achievement = conn.execute(
            "SELECT * FROM achievements WHERE id = ?",
            (achievement_id,)
        ).fetchone()
        
        if not achievement:
            return False
        
        # Додати досягнення користувачу
        conn.execute('''
            INSERT OR IGNORE INTO user_achievements 
            (user_id, achievement_id, unlocked_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, achievement_id))
        
        # Добавити бонусні очки
        if achievement['points_reward'] > 0:
            add_points(user_id, achievement['points_reward'],
                      f"Achievement: {achievement['name']}", "achievement", achievement_id)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Achievement unlocked: {achievement['name']} for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Achievement unlock error: {e}")
        return False

def check_user_level_up(user_id: int) -> Optional[int]:
    """Перевіряє чи користувач піднявся на новий рівень"""
    try:
        conn = get_db_connection()
        
        user = conn.execute(
            "SELECT current_level, total_points FROM user_levels WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            return None
        
        # Базова прогресія: 100 точок за рівень
        new_level = 1 + (user['total_points'] // 100)
        
        if new_level > user['current_level']:
            conn.execute('''
                UPDATE user_levels 
                SET current_level = ?, level_up_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_level, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"⬆️ User {user_id} leveled up to {new_level}")
            return new_level
        
        conn.close()
        return None
    
    except Exception as e:
        logger.error(f"Level check error: {e}")
        return None

def add_wishlist_alert(user_id: int, product_id: int, alert_type: str = 'back_in_stock') -> bool:
    """Добавляє сповіщення про товар у вибраному"""
    try:
        conn = get_db_connection()
        
        conn.execute('''
            INSERT OR REPLACE INTO wishlist_alerts 
            (user_id, product_id, alert_type, is_active, created_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, product_id, alert_type))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Wishlist alert added for product {product_id} (user {user_id})")
        return True
    
    except Exception as e:
        logger.error(f"Wishlist alert error: {e}")
        return False

def get_user_leaderboard_position(user_id: int) -> Optional[Dict]:
    """Отримує позицію користувача в лідербоарді"""
    try:
        conn = get_db_connection()
        
        # All-time leaderboard
        leaderboard = conn.execute('''
            SELECT 
                user_id, 
                total_points,
                ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank
            FROM user_levels
            WHERE total_points > 0
            ORDER BY total_points DESC
            LIMIT 100
        ''').fetchall()
        
        position = None
        for i, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user_id:
                position = i
                break
        
        conn.close()
        
        return {'rank': position, 'total_entries': len(leaderboard)} if position else None
    
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════
# 🚀 INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    create_gamification_tables()
    logger.info("✅ Gamification module initialized")
