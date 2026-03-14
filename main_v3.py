"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 FASTAPI WEB APPLICATION - TELEGRAM MINI APP SHOP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Современний веб-сервер для Telegram Mini App магазину
Features: Async REST API, Admin Panel, WebSocket, Telegram Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import json
import hashlib
import hmac
import sqlite3
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

# Імпорти проекту
from database import (
    get_db_connection, init_db, log_audit,
    generate_order_number
)
from nova_poshta import NovaPoshtaAPI

# ═══════════════════════════════════════════════════════════════════
# 📋 КОНФІГУРАЦІЯ
# ═══════════════════════════════════════════════════════════════════

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '8140568883:AAFAu9spWaeCuuC52Hb3uYmnwUNtn-VoUgY'

# Web App Settings
WEB_APP_URL = 'http://127.0.0.1:8000'
DEV_URL = 'http://127.0.0.1:8000'

# Database
DB_NAME = 'shop.db'

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
UPLOADS_DIR = STATIC_DIR / 'uploads'
BANNERS_DIR = STATIC_DIR / 'banners'

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True, parents=True)
BANNERS_DIR.mkdir(exist_ok=True, parents=True)

# ═══════════════════════════════════════════════════════════════════
# 🔧 LOGGING
# ═══════════════════════════════════════════════════════════════════

logger.remove()  # Remove default handler
logger.add(
    "logs/api.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
    level="INFO",
    rotation="500 MB"
)

# ═══════════════════════════════════════════════════════════════════
# 🎯 FASTAPI APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Telegram Mini App E-Commerce API",
    description="REST API для інтернет-магазину в Telegram",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ─────────────────────────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://telegram.org",
        "https://cuddly-wasps-dance.loca.lt",
        "https://*.loca.lt",  # localtunnel wildcard
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5000",  # Dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────
# Static Files
# ─────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# 📦 PYDANTIC MODELS (для валідації)
# ═══════════════════════════════════════════════════════════════════

class UserLogin(BaseModel):
    """Дані для входу користувача"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    auth_date: Optional[int] = None
    hash: Optional[str] = None

class OrderCreate(BaseModel):
    """Дані для створення замовлення"""
    user_id: int
    items: List[Dict[str, Any]]  # [{product_id, quantity, variant_id}]
    customer_name: str
    customer_phone: str
    city_ref: Optional[str] = None
    warehouse_ref: Optional[str] = None
    street_ref: Optional[str] = None
    building: Optional[str] = None
    flat: Optional[str] = None
    promocode: Optional[str] = None
    delivery_type: str = "warehouse"  # warehouse or address

class PromoCodeValidate(BaseModel):
    """Валідація промокоду"""
    code: str
    total: float = 0

class ProductCreate(BaseModel):
    """Створення/редагування товара"""
    name: str
    sku: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    price: float
    price_old: Optional[float] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    is_top: bool = False
    stock_quantity: int = 0

class BrandCreate(BaseModel):
    """Створення/редагування бренду"""
    name: str
    slug: Optional[str] = None
    sort_order: int = 0

class CategoryCreate(BaseModel):
    """Створення/редагування категорії"""
    name: str
    icon: Optional[str] = None
    sort_order: int = 0

# ═══════════════════════════════════════════════════════════════════
# 🔐 SECURITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def validate_telegram_init_data(init_data: str) -> Dict:
    """
    Валідація initData від Telegram WebApp
    Повертає parsed дані або None
    """
    try:
        if not init_data:
            return None
        
        parsed = dict(urllib.parse.parse_qsl(init_data))
        
        if 'hash' not in parsed:
            return None
        
        received_hash = parsed.pop('hash')
        
        # Create data-check-string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Create secret key
        secret_key = hmac.new(
            "WebAppData".encode(),
            TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash == received_hash:
            return parsed
        
        return None
    
    except Exception as e:
        logger.error(f"Init data validation error: {e}")
        return None

async def get_user_from_request(request: Request) -> Optional[Dict]:
    """Отримання користувача з request"""
    try:
        body = await request.json()
        user_id = body.get('user_id')
        
        if not user_id:
            return None
        
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        
        return dict(user) if user else None
    except:
        return None

# ═══════════════════════════════════════════════════════════════════
# 🏠 FRONTEND ROUTES (HTML Pages)
# ═══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    """Головна сторінка - Telegram Mini App"""
    try:
        conn = get_db_connection()
        
        # Налаштування
        settings_row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        settings = dict(settings_row) if settings_row else {}
        
        # Категорії
        categories = [dict(row) for row in conn.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, name"
        ).fetchall()]
        
        # Бренди
        brands = [dict(row) for row in conn.execute(
            "SELECT * FROM brands WHERE is_active = 1 ORDER BY sort_order, name"
        ).fetchall()]
        
        # Товари
        products = conn.execute("""
            SELECT 
                p.*,
                c.name as category_name,
                c.icon as category_icon,
                b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.is_active = 1
            ORDER BY p.is_top DESC, p.created_at DESC
        """).fetchall()
        
        products_list = []
        for product in products:
            p_dict = dict(product)
            
            # Parse JSON
            if p_dict.get('images_json'):
                try:
                    p_dict['images'] = json.loads(p_dict['images_json'])
                except:
                    p_dict['images'] = []
            else:
                p_dict['images'] = []
            
            # Варіанти
            variants = conn.execute(
                "SELECT * FROM product_variants WHERE product_id = ? AND is_active = 1",
                (p_dict['id'],)
            ).fetchall()
            
            p_dict['variants'] = [dict(v) for v in variants]
            products_list.append(p_dict)
        
        # Банери
        banners = [dict(row) for row in conn.execute(
            "SELECT * FROM banners WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()]
        
        # Stories
        stories = [dict(row) for row in conn.execute(
            "SELECT * FROM stories WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()]
        
        # Прочитати HTML файл
        index_path = BASE_DIR / 'index.html'
        if index_path.exists():
            html_content = index_path.read_text(encoding='utf-8')
            
            # Вставити дані в HTML
            html_content = html_content.replace(
                '<!--PRODUCTS_JSON-->',
                f'<script>window.PRODUCTS = {json.dumps(products_list, ensure_ascii=False)}</script>'
            )
            
            return html_content
        
        return "<h1>Mini App Shop</h1>"
    
    except Exception as e:
        logger.error(f"Index error: {e}")
        return f"<h1>Error: {e}</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Адмін панель"""
    admin_path = BASE_DIR / 'admin.html'
    
    if admin_path.exists():
        return admin_path.read_text(encoding='utf-8')
    
    return "<h1>Admin Panel</h1>"

# ═══════════════════════════════════════════════════════════════════
# 🔐 AUTH API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/auth/login")
async def auth_login(user_data: UserLogin):
    """Вхід користувача або реєстрація"""
    try:
        conn = get_db_connection()
        
        # Перевірити чи користувач існує
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_data.user_id,)
        ).fetchone()
        
        if not user:
            # Реєстрація нового користувача
            conn.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, role, created_at)
                VALUES (?, ?, ?, ?, 'user', ?)
            ''', (
                user_data.user_id,
                user_data.username or '',
                user_data.first_name or '',
                user_data.last_name or '',
                datetime.now()
            ))
            conn.commit()
            logger.info(f"✅ New user registered: {user_data.user_id}")
        
        conn.close()
        
        return {
            'success': True,
            'user_id': user_data.user_id,
            'message': 'Login successful'
        }
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/balance")
async def get_user_balance(request: Request):
    """Отримати баланс користувача"""
    try:
        user = await get_user_from_request(request)
        
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        conn = get_db_connection()
        balance = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (user['user_id'],)
        ).fetchone()
        
        conn.close()
        
        return {
            'success': True,
            'balance': balance[0] if balance else 0
        }
    
    except Exception as e:
        logger.error(f"Balance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test.html", response_class=HTMLResponse)
async def test_page():
    """Test page for debugging WebView"""
    try:
        with open('test.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<h1>Error loading test page: {e}</h1>"

# ═══════════════════════════════════════════════════════════════════
# 📦 PRODUCTS API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/products")
async def get_products(
    category: str = Query(None),
    brand: str = Query(None),
    search: str = Query(None),
    sort: str = Query("new")
):
    """Отримати список товарів з фільтрами"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                p.*,
                c.name as category_name,
                b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.is_active = 1
        """
        
        params = []
        
        if category and category != 'all':
            query += " AND p.category_id = ?"
            params.append(int(category))
        
        if brand and brand != 'all':
            query += " AND p.brand_id = ?"
            params.append(int(brand))
        
        if search:
            query += " AND (p.name LIKE ? OR p.description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Сортування
        if sort == "price_asc":
            query += " ORDER BY p.price ASC"
        elif sort == "price_desc":
            query += " ORDER BY p.price DESC"
        elif sort == "top":
            query += " ORDER BY p.rating DESC"
        else:  # new
            query += " ORDER BY p.created_at DESC"
        
        products = conn.execute(query, params).fetchall()
        conn.close()
        
        result = []
        for p in products:
            p_dict = dict(p)
            try:
                p_dict['images'] = json.loads(p_dict.get('images_json', '[]'))
            except:
                p_dict['images'] = []
            result.append(p_dict)
        
        return {
            'success': True,
            'count': len(result),
            'products': result
        }
    
    except Exception as e:
        logger.error(f"Products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product/{product_id}")
async def get_product_detail(product_id: int):
    """Деталі товара"""
    try:
        conn = get_db_connection()
        
        product = conn.execute("""
            SELECT 
                p.*,
                c.name as category_name,
                b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.id = ?
        """, (product_id,)).fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        p_dict = dict(product)
        
        # Варіанти
        variants = conn.execute(
            "SELECT * FROM product_variants WHERE product_id = ? AND is_active = 1",
            (product_id,)
        ).fetchall()
        
        p_dict['variants'] = [dict(v) for v in variants]
        
        # Відгуки
        reviews = conn.execute(
            "SELECT * FROM reviews WHERE product_id = ? AND is_approved = 1 ORDER BY created_at DESC LIMIT 10",
            (product_id,)
        ).fetchall()
        
        p_dict['reviews'] = [dict(r) for r in reviews]
        
        # Зображення
        try:
            p_dict['images'] = json.loads(p_dict.get('images_json', '[]'))
        except:
            p_dict['images'] = []
        
        conn.close()
        
        return {
            'success': True,
            'product': p_dict
        }
    
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product")
async def create_or_update_product(request: Request, product: ProductCreate):
    """Створення/редагування товара (тільки для адмінів)"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        
        if product.id:  # Update
            conn.execute('''
                UPDATE products SET
                    name = ?, sku = ?, category_id = ?, brand_id = ?,
                    price = ?, price_old = ?, short_description = ?,
                    description = ?, is_top = ?, stock_quantity = ?
                WHERE id = ?
            ''', (
                product.name, product.sku, product.category_id, product.brand_id,
                product.price, product.price_old, product.short_description,
                product.description, product.is_top, product.stock_quantity,
                product.id
            ))
        else:  # Create
            conn.execute('''
                INSERT INTO products 
                (name, sku, category_id, brand_id, price, price_old, 
                 short_description, description, is_top, stock_quantity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.name, product.sku, product.category_id, product.brand_id,
                product.price, product.price_old, product.short_description,
                product.description, product.is_top, product.stock_quantity,
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Product saved: {product.name}")
        
        return {'success': True, 'message': 'Product saved successfully'}
    
    except Exception as e:
        logger.error(f"Product save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product/delete")
async def delete_product(request: Request, product_id: int):
    """Видалення товара"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Product deleted: {product_id}")
        
        return {'success': True, 'message': 'Product deleted'}
    
    except Exception as e:
        logger.error(f"Product delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# 🛒 CART & ORDERS API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/order/create")
async def create_order(order_data: OrderCreate):
    """Створення замовлення"""
    try:
        conn = get_db_connection()
        
        # Валідація товарів
        total = 0
        for item in order_data.items:
            product = conn.execute(
                "SELECT price FROM products WHERE id = ?",
                (item['product_id'],)
            ).fetchone()
            
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
            
            total += product[0] * item['quantity']
        
        # Промокод
        discount = 0
        if order_data.promocode:
            promo = validate_promocode(order_data.promocode, total)
            if promo:
                discount = promo.get('discount_value', 0)
        
        total -= discount
        
        # Генерувати номер замовлення
        order_number = generate_order_number()
        
        # Створити замовлення
        conn.execute('''
            INSERT INTO orders 
            (user_id, order_number, status, total, customer_name, customer_phone,
             city_ref, warehouse_ref, delivery_type, promocode, discount, created_at)
            VALUES (?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data.user_id,
            order_number,
            total,
            order_data.customer_name,
            order_data.customer_phone,
            order_data.city_ref,
            order_data.warehouse_ref,
            order_data.delivery_type,
            order_data.promocode,
            discount,
            datetime.now()
        ))
        
        conn.commit()
        
        # Отримати ID замовлення
        order = conn.execute(
            "SELECT id FROM orders WHERE order_number = ?",
            (order_number,)
        ).fetchone()
        
        order_id = order[0]
        
        # Додати товари в замовлення
        for item in order_data.items:
            conn.execute('''
                INSERT INTO order_items 
                (order_id, product_id, variant_id, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                order_id,
                item['product_id'],
                item.get('variant_id'),
                item['quantity'],
                conn.execute("SELECT price FROM products WHERE id = ?", 
                           (item['product_id'],)).fetchone()[0]
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Order created: #{order_number}")
        
        return {
            'success': True,
            'order_id': order_id,
            'order_number': order_number,
            'total': total
        }
    
    except Exception as e:
        logger.error(f"Order creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/status")
async def update_order_status(request: Request, order_id: int, status: str):
    """Оновити статус замовлення"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        conn.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                    (status, datetime.now(), order_id))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Order status updated: {order_id} -> {status}")
        
        return {'success': True, 'message': 'Order status updated'}
    
    except Exception as e:
        logger.error(f"Order update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders")
async def get_user_orders(request: Request):
    """Отримати замовлення користувача"""
    try:
        user = await get_user_from_request(request)
        
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        conn = get_db_connection()
        
        orders = conn.execute('''
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user['user_id'],)).fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'orders': [dict(o) for o in orders]
        }
    
    except Exception as e:
        logger.error(f"Orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_ttn")
async def create_ttn_endpoint(request: Request, order_id: int):
    """Створити TTN через Nova Poshta"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        
        order = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Створити TTN
        ttn = create_ttn(
            order_id=order_id,
            recipient_phone=order['customer_phone'],
            recipient_name=order['customer_name'],
            recipient_city_ref=order['city_ref'],
            recipient_warehouse_ref=order['warehouse_ref'],
            cost=order['total']
        )
        
        # Зберегти TTN в замовленні
        conn.execute(
            "UPDATE orders SET ttn_number = ? WHERE id = ?",
            (ttn, order_id)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"✅ TTN created: {ttn}")
        
        return {
            'success': True,
            'ttn': ttn
        }
    
    except Exception as e:
        logger.error(f"TTN creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# 📮 NOVA POSHTA API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/np/cities")
async def np_cities(query: str = Query(..., min_length=2)):
    """Пошук міст в Nova Poshta"""
    try:
        cities = get_cities(query)
        
        return {
            'success': True,
            'cities': cities
        }
    
    except Exception as e:
        logger.error(f"Cities search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/np/warehouses")
async def np_warehouses(city_ref: str = Query(...)):
    """Отримати відділення для міста"""
    try:
        warehouses = get_warehouses(city_ref)
        
        return {
            'success': True,
            'warehouses': warehouses
        }
    
    except Exception as e:
        logger.error(f"Warehouses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# ❤️ FAVORITES API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/favorite/toggle")
async def toggle_favorite(request: Request, product_id: int):
    """Додати/видалити з вибраного"""
    try:
        user = await get_user_from_request(request)
        
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        conn = get_db_connection()
        
        # Перевірити чи вже в улюблених
        fav = conn.execute(
            "SELECT * FROM favorites WHERE user_id = ? AND product_id = ?",
            (user['user_id'], product_id)
        ).fetchone()
        
        if fav:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
                (user['user_id'], product_id)
            )
            action = "removed"
        else:
            conn.execute(
                "INSERT INTO favorites (user_id, product_id, created_at) VALUES (?, ?, ?)",
                (user['user_id'], product_id, datetime.now())
            )
            action = "added"
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Favorite {action}: {product_id}")
        
        return {
            'success': True,
            'action': action
        }
    
    except Exception as e:
        logger.error(f"Favorite toggle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/favorites/list")
async def get_favorites(request: Request):
    """Отримати список вибраного"""
    try:
        user = await get_user_from_request(request)
        
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        conn = get_db_connection()
        
        favorites = conn.execute('''
            SELECT p.* FROM products p
            JOIN favorites f ON p.id = f.product_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user['user_id'],)).fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'favorites': [dict(f) for f in favorites]
        }
    
    except Exception as e:
        logger.error(f"Favorites list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# 🎟️ PROMOCODES API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/promocode/validate")
async def validate_promocode(promo: PromoCodeValidate):
    """Валідація промокоду"""
    try:
        result = validate_promocode(promo.code, promo.total)
        
        if result:
            return {
                'success': True,
                'valid': True,
                'discount': result.get('discount_value', 0)
            }
        else:
            return {
                'success': False,
                'valid': False
            }
    
    except Exception as e:
        logger.error(f"Promo validation error: {e}")
        return {
            'success': False,
            'valid': False
        }

@app.post("/api/promocode")
async def create_promocode(request: Request, 
                          code: str,
                          discount_type: str,
                          discount_value: float):
    """Створити промокод (тільки адмін)"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        
        conn.execute('''
            INSERT INTO promocodes 
            (code, discount_type, discount_value, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        ''', (code, discount_type, discount_value, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Promo created: {code}")
        
        return {'success': True, 'message': 'Promocode created'}
    
    except Exception as e:
        logger.error(f"Promo creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# 🎛️ ADMIN ENDPOINTS (Categories, Brands, etc.)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/category")
async def save_category(request: Request, category: CategoryCreate):
    """Зберегти категорію"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        
        conn.execute('''
            INSERT INTO categories 
            (name, icon, sort_order, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        ''', (category.name, category.icon, category.sort_order, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Category created: {category.name}")
        
        return {'success': True, 'message': 'Category saved'}
    
    except Exception as e:
        logger.error(f"Category save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brand")
async def save_brand(request: Request, brand: BrandCreate):
    """Зберегти бренд"""
    try:
        user = await get_user_from_request(request)
        
        if not user or user.get('role') not in ['admin', 'manager']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        conn = get_db_connection()
        
        slug = brand.slug or brand.name.lower().replace(' ', '-')
        
        conn.execute('''
            INSERT INTO brands 
            (name, slug, sort_order, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        ''', (brand.name, slug, brand.sort_order, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Brand created: {brand.name}")
        
        return {'success': True, 'message': 'Brand saved'}
    
    except Exception as e:
        logger.error(f"Brand save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# 🚀 STARTUP & SHUTDOWN EVENTS
# ═══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """При запуску додатку"""
    logger.info("━" * 60)
    logger.info("🚀 FASTAPI APPLICATION STARTED")
    logger.info("━" * 60)
    
    # Ініціалізувати БД
    init_db()
    
    logger.info("✅ All systems ready!")
    logger.info(f"📱 Mini App: {DEV_URL}")
    logger.info(f"⚙️ Admin Panel: {DEV_URL}/admin")
    logger.info(f"📚 API Docs: {DEV_URL}/api/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """При зупинці додатку"""
    logger.info("⛔ FASTAPI APPLICATION SHUTTING DOWN")

# ═══════════════════════════════════════════════════════════════════
# 🏃 RUN APPLICATION (for development)
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_v3:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
