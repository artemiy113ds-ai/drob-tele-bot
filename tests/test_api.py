"""
Tests for FastAPI endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from main_v3 import app

@pytest.mark.asyncio
async def test_get_products():
    """Test GET /api/products"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data

@pytest.mark.asyncio
async def test_auth_login():
    """Test POST /api/auth/login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "user_id": 12345,
            "init_data": "test_data"
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

@pytest.mark.asyncio
async def test_create_order():
    """Test POST /api/order/create"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/order/create", json={
            "user_id": 12345,
            "customer_name": "Test User",
            "customer_phone": "+380123456789",
            "delivery_method": "nova_poshta",
            "delivery_city": "Київ",
            "delivery_warehouse": "test_warehouse",
            "items": [{"product_id": 1, "quantity": 1, "price": 100}],
            "total_price": 100
        })
        assert response.status_code == 200 or response.status_code == 201

@pytest.mark.asyncio
async def test_nova_poshta_cities():
    """Test GET /api/np/cities"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/np/cities?q=Київ")
        assert response.status_code == 200
        data = response.json()
        assert "cities" in data

@pytest.mark.asyncio
async def test_toggle_favorite():
    """Test POST /api/favorite/toggle"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/favorite/toggle", json={
            "user_id": 12345,
            "product_id": 1
        })
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_validate_promocode():
    """Test POST /api/promocode/validate"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/promocode/validate", data={
            "code": "INVALID_CODE",
            "user_id": 12345,
            "cart_total": 100
        })
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
