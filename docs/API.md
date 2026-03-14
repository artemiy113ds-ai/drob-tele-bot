# API Documentation

## Base URL
```
/api
```

## Authentication
All requests should include:
```
Authorization: Bearer <token>
```

Or for Telegram WebApp:
- Include `init_data` in request body (for POST requests)

## Endpoints

### Auth
- **POST /auth/login** - Authenticate user
  - Body: `{user_id, init_data}`
  - Response: `{success, role, user_id}`

### Products
- **GET /products** - List all products
  - Query: `category_id, brand_id, search, sort, skip, limit`
  - Response: `{products: [...]}`

- **GET /product/{id}** - Get product details
  - Response: `{id, name, description, price, variants, reviews}`

### Orders
- **POST /order/create** - Create order
  - Body: `{user_id, customer_name, customer_phone, delivery_method, delivery_city, items, total_price}`
  - Response: `{success, order_number, order_id}`

- **GET /orders** - List user orders
  - Query: `user_id, skip, limit`
  - Response: `{orders: [...]}`

- **POST /order/status** - Update order status
  - Body: `{order_id, status, ttn}`
  - Response: `{success}`

### Nova Poshta
- **GET /np/cities** - Search cities
  - Query: `q` (search query)
  - Response: `{cities: [{ref, description}]}`

- **GET /np/warehouses** - Get warehouses in city
  - Query: `city_ref`
  - Response: `{warehouses: [{ref, description, phone}]}`

### Favorites
- **POST /favorite/toggle** - Add/remove favorite
  - Body: `{user_id, product_id}`
  - Response: `{success, added}`

- **GET /favorites/list** - List user favorites
  - Query: `user_id`
  - Response: `{favorites: [...]}`

### Gamification
- **GET /user/profile** - User profile with gamification data
  - Query: `user_id`
  - Response: `{level, points, tier_name, achievements, referral_code}`

- **GET /leaderboard** - Top users by points
  - Query: `limit` (default 10)
  - Response: `{leaderboard: [{user_id, first_name, total_points}]}`

### Promocodes
- **POST /promocode/validate** - Validate promocode
  - Body: `{code, user_id, cart_total}`
  - Response: `{valid, message, discount, discount_type}`

- **POST /promocode** - Create new promocode (admin)
  - Body: `{code, discount_value, discount_type, max_uses, valid_until}`
  - Response: `{success}`

### Admin
- **POST /admin/dashboard** - Dashboard stats
  - Response: `{total_orders, total_users, total_revenue, revenue_chart}`

- **GET /admin/orders** - All orders
  - Response: `{orders: [...]}`

## Error Responses

All errors follow this format:
```json
{
    "detail": "Error message",
    "status": 400
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error
