# Architecture & Design

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Telegram Mini App (Frontend)            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ index.html + script.js + style.css                  │ │
│  │ - Products catalog                                   │ │
│  │ - Shopping cart                                      │ │
│  │ - Gamification UI (levels, achievements)             │ │
│  │ - Referral system                                    │ │
│  │ - Profile & Leaderboard                              │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────
                           ↑
                         HTTPS
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Nginx Reverse Proxy                     │
│  - SSL/TLS termination                                    │
│  - Request routing                                        │
│  - Static file serving                                    │
│  - Rate limiting                                          │
└─────────────────────────────────────────────────────────┘
                           ↑
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                   ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  FastAPI     │  │   Telegram   │  │    Redis     │
│  (main_v3.py)│  │   Bot        │  │   (Cache)    │
│              │  │ (bot_v3.py)  │  │              │
│ - REST API   │  │              │  └──────────────┘
│ - WebApp     │  │ - Commands   │
│ - Admin      │  │ - Callbacks  │
└──────────────┘  │ - Broadcasts │
        ↑         └──────────────┘
        │                ↑
        └────────────────┼────────────────┐
                         ↓                │
                  ┌─────────────────┐    │
                  │   SQLite3 DB    │    │
                  │                 │    │
                  │ - Products      │    │
                  │ - Orders        │    │
                  │ - Users         │    │
                  │ - Gamification  │    │
                  └─────────────────┘    │
                                         │
                  ┌──────────────────────┘
                  ↓
           ┌─────────────────┐
           │ Nova Poshta API │
           │   (Logistics)   │
           └─────────────────┘
```

## Component Architecture

### Frontend Layer (Client-Side)
**Technology**: Vanilla JavaScript + Telegram WebApp SDK

```
index.html (Main App)
├── Shop View
│   ├── Product Grid
│   ├── Search/Filter
│   ├── Gamification Widget
│   └── Daily Tasks
├── Profile View
│   ├── User Stats
│   ├── Achievements
│   ├── Leaderboard
│   └── Referral Program
├── Favorites View
├── Cart View
│   └── Checkout Form
└── Modals (Product Detail, etc.)

admin.html (Admin Panel)
├── Dashboard
├── Products Management
├── Orders Management
├── Users Management
├── Gamification Admin
└── Settings
```

### API Layer (Backend)
**Technology**: FastAPI + uvicorn + Pydantic

```
FastAPI App (main_v3.py)
├── Auth Endpoints
│   ├── POST /auth/login
│   └── POST /user/balance
├── Product Endpoints
│   ├── GET /products
│   ├── GET /product/{id}
│   └── POST /product (admin)
├── Order Endpoints
│   ├── POST /order/create
│   ├── GET /orders
│   ├── POST /order/status
│   └── POST /order/{id}/ttn
├── Nova Poshta Integration
│   ├── GET /np/cities
│   ├── GET /np/warehouses
│   └── POST /np/ttn/create
├── Favorites Endpoints
│   ├── POST /favorite/toggle
│   └── GET /favorites/list
├── Gamification Endpoints
│   ├── GET /user/profile
│   ├── GET /leaderboard
│   ├── POST /achievement/unlock
│   └── POST /task/complete
├── Promo Endpoints
│   ├── POST /promocode/validate
│   └── POST /promocode (admin)
└── Admin Endpoints
    ├── GET /admin/dashboard
    ├── GET /admin/orders
    ├── GET /admin/users
    └── GET /admin/gamification
```

### Bot Layer
**Technology**: Aiogram 3.x + async

```
Telegram Bot (bot_v3.py)
├── Main Router
│   ├── Commands
│   │   ├── /start
│   │   ├── /help
│   │   ├── /admin
│   │   └── /orders
│   ├── Admin Features
│   │   ├── Statistics
│   │   ├── Broadcast
│   │   └── User Management
│   └── Callbacks
│       ├── Main Menu
│       ├── Profile
│       └── Orders
├── FSM (Finite State Machine)
│   └── AdminBroadcastStates
└── Database Integration
    └── User registration/updates
```

### Database Layer
**Technology**: SQLite3 + Raw SQL

```
SQLite3 (shop.db)
├── User Management
│   └── users
├── Products
│   ├── products
│   ├── categories
│   ├── brands
│   ├── product_variants
│   └── reviews
├── Orders
│   ├── orders
│   └── order_items
├── Gamification
│   ├── loyalty_tiers
│   ├── user_levels
│   ├── achievements
│   ├── user_achievements
│   ├── daily_tasks
│   ├── user_daily_tasks
│   ├── referral_rewards
│   ├── wishlist_alerts
│   └── points_log
├── Commerce
│   ├── promocodes
│   ├── promocode_usage
│   ├── favorites
│   ├── cart_items
│   └── abandoned_carts
└── System
    ├── settings
    ├── audit_log
    └── search_queries
```

## Data Flow

### Product Viewing Flow
```
1. User opens Mini App (/api/products)
2. Frontend requests GET /api/products
3. FastAPI queries SQLite
4. Database returns product list + variants
5. Frontend renders product grid
6. User clicks product → GET /api/product/{id}
7. Modal displays full details with variants
```

### Order Creation Flow
```
1. User fills checkout form
2. Frontend requests POST /order/create
3. FastAPI validates data + init_data
4. Database creates order record
5. Generates unique order number
6. Broadcasts to admin bot
7. Returns success + order number
8. Frontend clears cart
9. Admin receives notification
```

### Gamification Flow
```
1. User makes order
2. Bot log_action triggers → add 50 points
3. gamification.add_points() updates user_levels
4. check_user_level_up() calculates new level
5. If new level reached → unlock achievement
6. achievement triggers referral rewards update
7. User profile updated with new stats
8. Next API call returns updated stats
```

### Nova Poshta Integration
```
1. User enters city name
2. Frontend calls GET /np/cities?q=...
3. FastAPI calls nova_poshta.search_cities()
4. API returns suggestions
5. User selects city
6. Frontend calls GET /np/warehouses?city_ref=...
7. FastAPI calls nova_poshta.get_warehouses()
8. Warehouse list displayed
9. User selects warehouse
10. Order sent with warehouse ref
```

## Security Architecture

### Authentication
```
┌─────────────────────────────────────────┐
│  Telegram Secure Init Data              │
│  - Signed by Telegram                   │
│  - Contains user_id + timestamp         │
│  - BOT_TOKEN verification               │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  FastAPI validate_telegram_init_data()  │
│  - Check signature                      │
│  - Verify timestamp (live < 3600s)      │
│  - Extract user data                    │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Role-Based Access Control (RBAC)       │
│  - user: view products, create orders   │
│  - admin: manage products, stats        │
│  - manager: limited admin access       │
└─────────────────────────────────────────┘
```

### Data Protection
```
✓ HTTPS/TLS for all communication
✓ SQLite encryption (WAL mode)
✓ Parameterized SQL queries (no injection)
✓ Rate limiting (Nginx)
✓ CORS configured for Telegram WebApp
✓ Audit logging for admin actions
✓ Password hasing (future: bcrypt)
```

## Scalability Considerations

### Current (Monolithic)
```
Single Server
├── Nginx
├── FastAPI
├── Bot
├── SQLite (file-based)
└── Redis (optional)

Supports ~10K concurrent users
```

### Future (Microservices)
```
API Gateway (Nginx)
├── API Service (horizontal scaling)
├── Bot Service
├── Gamification Service
├── Notification Service
└── Analytics Service

Database
├── PostgreSQL (replicated)
├── Redis Cluster (session store)
└── Elasticsearch (logs)

Supports ~1M+ concurrent users
```

## Performance Optimization

### Caching Strategy
```
┌────────────────────────────────┐
│  Browser Cache (1 hour)         │
│  - Static assets                │
│  - Product images               │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│  Redis Cache (FastAPI)          │
│  - Product catalog (24h)        │
│  - Leaderboard (1h)             │
│  - City/warehouse lists (7d)    │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│  Database Queries               │
│  - Indexed on user_id, status   │
│  - Connection pooling           │
│  - Query optimization           │
└────────────────────────────────┘
```

### Response Time Targets
```
GET /products        : < 200ms
POST /order/create   : < 500ms
GET /np/cities       : < 300ms
GET /leaderboard     : < 150ms
```

## Monitoring & Logging

```
┌──────────────────┐
│  Application     │
│   Logs           │
│  (loguru)        │
└──────────────────┘
        ↓
┌──────────────────┐
│ Structured JSON  │
│  Logs            │
└──────────────────┘
        ↓
┌──────────────────────────────────┐
│ Log Aggregation (Future)         │
│  - ELK Stack or                  │
│  - Datadog or                    │
│  - CloudWatch                    │
└──────────────────────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Development/Small Scale)
- All services in single host
- SQLite database
- Redis optional
- Good for < 1000 daily users

### Option 2: Cloud VPS (DigitalOcean/Linode)
- Ubuntu VM (2GB RAM, 2vCPU)
- Docker containers
- Nginx reverse proxy
- DigitalOcean backup
- Good for 1K-10K daily users

### Option 3: Kubernetes (Enterprise)
- Containerized services
- Auto-scaling
- PostgreSQL + Redis clusters
- CDN for static assets
- Monitoring + logging
- Good for 10K+ daily users
