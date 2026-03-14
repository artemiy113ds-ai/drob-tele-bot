#!/usr/bin/env python3
"""
Database initialization and helper functions for SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

DB_PATH = 'shop.db'

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE NOT NULL,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active',
        balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Products
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT,
        is_active INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        logo_url TEXT,
        is_active INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE,
        description TEXT,
        category_id INTEGER,
        brand_id INTEGER,
        base_price REAL NOT NULL,
        old_price REAL,
        image TEXT,
        images TEXT,
        status TEXT DEFAULT 'active',
        is_active INTEGER DEFAULT 1,
        total_quantity INTEGER DEFAULT 0,
        views_count INTEGER DEFAULT 0,
        sales_count INTEGER DEFAULT 0,
        avg_rating REAL DEFAULT 0,
        reviews_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(category_id) REFERENCES categories(id),
        FOREIGN KEY(brand_id) REFERENCES brands(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price_modifier REAL DEFAULT 0,
        quantity INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    
    # Orders
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        delivery_method TEXT,
        delivery_city TEXT,
        delivery_warehouse TEXT,
        delivery_city_ref TEXT,
        delivery_warehouse_ref TEXT,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        total_price REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        ttn TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        variant_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    
    # Favorites
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, product_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    
    # Promo codes
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT,
        discount_value REAL NOT NULL,
        max_uses INTEGER,
        current_uses INTEGER DEFAULT 0,
        valid_from TIMESTAMP,
        valid_until TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Audit log
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(admin_id) REFERENCES users(id)
    )''')
    
    # Settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        shop_name TEXT DEFAULT 'MiniShop',
        shop_description TEXT,
        currency TEXT DEFAULT 'UAH',
        logo_url TEXT,
        theme_color TEXT DEFAULT '#007AFF',
        notification_email TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert default settings if not exists
    c.execute("INSERT OR IGNORE INTO settings (id, shop_name) VALUES (1, 'MiniShop')")
    
    conn.commit()
    conn.close()
    print('✅ Database initialized')

def generate_order_number() -> str:
    """Generate unique order number"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT MAX(id) FROM orders")
    last_id = c.fetchone()[0] or 0
    conn.close()
    
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{last_id + 1:05d}"

def log_audit(admin_id: int, action: str, details: str = None):
    """Log admin action"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('INSERT INTO audit_log (admin_id, action, details) VALUES (?, ?, ?)',
              (admin_id, action, details))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
