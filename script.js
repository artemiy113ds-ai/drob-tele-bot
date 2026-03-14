/**
 * 🛍️ FASTAPI MINI APP - script.js
 * Updated for FastAPI endpoints (main_v3.py)
 */

const API = '/api';
const tg = window.Telegram?.WebApp;
let CART = JSON.parse(localStorage.getItem('cart')) || [];
let USER = null, PRODUCTS = [];
let FAVORITES = new Set();
let CURRENT_PRODUCT = null;

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App init...');
    
    if (tg) {
        tg.ready();
        tg.expand();
        USER = tg.initDataUnsafe?.user;
        
        if (USER) {
            console.log('👤 User:', USER.id);
            await authenticateUser();
            await loadProfile();
            await loadFavorites();
        }
    }
    
    await loadProducts();
    renderProducts();
    setupEventListeners();
    updateCartBadge();
});

async function authenticateUser() {
    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: USER.id,
                init_data: tg?.initData || ''
            })
        });
        const data = await res.json();
        console.log('✅ Auth:', data.role);
    } catch (e) {
        console.error('❌ Auth error:', e);
    }
}

async function loadProducts() {
    try {
        const res = await fetch(`${API}/products`);
        const data = await res.json();
        PRODUCTS = data.products || [];
        console.log('📦 Loaded', PRODUCTS.length, 'products');
    } catch (e) {
        console.error('Error loading products:', e);
    }
}

async function loadProfile() {
    if (!USER) return;
    try {
        const res = await fetch(`${API}/user/profile`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: USER.id})
        });
        const data = await res.json();
        updateProfileUI(data);
    } catch (e) {
        console.error('Profile error:', e);
    }
}

async function loadFavorites() {
    if (!USER) return;
    try {
        const res = await fetch(`${API}/favorites/list`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: USER.id})
        });
        const data = await res.json();
        FAVORITES = new Set(data.favorites || []);
    } catch (e) {
        console.error('Favorites error:', e);
    }
}

function updateProfileUI(data) {
    const name = USER?.first_name || 'Користувач';
    const avatar = USER?.first_name?.[0] || '👤';
    
    document.getElementById('user-name').textContent = name;
    document.getElementById('user-avatar').textContent = avatar;
    document.getElementById('user-balance').textContent = `💰 ${data.balance || 0}₴`;
    document.getElementById('profile-level').textContent = data.level || 1;
    document.getElementById('profile-points').textContent = data.points || 0;
    document.getElementById('profile-achievements').textContent = data.achievements_count || 0;
    document.getElementById('profile-rank').textContent = `#${data.rank || '-'}`;
    
    // Referral
    document.getElementById('referral-code').value = data.referral_code || '';
    document.getElementById('referral-count').textContent = data.referred_count || 0;
    document.getElementById('referral-earnings').textContent = `${data.referral_earnings || 0}₴`;
}

function setupEventListeners() {
    document.getElementById('search-input')?.addEventListener('input', (e) => {
        filterProducts(e.target.value);
    });
    
    document.getElementById('sort-select')?.addEventListener('change', (e) => {
        sortProducts(e.target.value);
    });
    
    document.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            navigateTo(e.target.closest('[data-nav]').dataset.nav);
        });
    });
    
    // City search
    document.getElementById('city-search')?.addEventListener('input', searchCities);
}

// ═══════════════════════════════════════════════════════════════
// NAVIGATION & VIEWS
// ═══════════════════════════════════════════════════════════════

function navigateTo(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`${view}-view`).classList.add('active');
    
    document.querySelectorAll('[data-nav]').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.nav === view) btn.classList.add('active');
    });
    
    if (view === 'favorites') renderFavorites();
    if (view === 'profile') loadProfile();
    if (view === 'cart') renderCart();
}

// ═══════════════════════════════════════════════════════════════
// PRODUCTS
// ═══════════════════════════════════════════════════════════════

function renderProducts(products = PRODUCTS) {
    const container = document.getElementById('products-container');
    if (!container) return;
    
    if (products.length === 0) {
        container.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; color:#999;">📦 Товарів не знайдено</div>';
        return;
    }
    
    container.innerHTML = products.map(p => `
        <div class="product-card"onclick="openProduct(${p.id})">
            <div class="product-image" style="background-image: url(${p.image || '/static/placeholder.jpg'})">
                ${p.total_quantity <= 0 ? '<div class="badge-stock">ЗАКІНЧ.</div>' : ''}
                <button class="btn-favorite ${FAVORITES.has(p.id) ? 'active' : ''}" onclick="event.stopPropagation(); toggleFavorite(${p.id})">❤️</button>
            </div>
            <div class="product-info">
                <h4>${p.name}</h4>
                <div class="product-price">
                    <span class="price">${p.base_price}₴</span>
                    ${p.old_price > p.base_price ? `<strike>${p.old_price}₴</strike>` : ''}
                </div>
                <button class="btn-primary" onclick="event.stopPropagation(); addToCart()" style="width:100%; padding:8px;">Додати</button>
            </div>
        </div>
    `).join('');
}

function filterProducts(query) {
    const filtered = PRODUCTS.filter(p =>
        p.name.toLowerCase().includes(query.toLowerCase())
    );
    renderProducts(filtered);
}

function sortProducts(type) {
    const sorted = [...PRODUCTS];
    
    switch(type) {
        case 'price-asc':
            sorted.sort((a, b) => a.base_price - b.base_price);
            break;
        case 'price-desc':
            sorted.sort((a, b) => b.base_price - a.base_price);
            break;
        case 'popular':
            sorted.sort((a, b) => (b.views_count || 0) - (a.views_count || 0));
            break;
    }
    
    renderProducts(sorted);
}

async function openProduct(productId) {
    const product = PRODUCTS.find(p => p.id === productId);
    if (!product) return;
    
    CURRENT_PRODUCT = product;
    
    document.getElementById('modal-title').textContent = product.name;
    document.getElementById('modal-image').src = product.image;
    document.getElementById('modal-price').textContent = `${product.base_price}₴`;
    document.getElementById('modal-desc').textContent = product.description || 'Опис відсутній';
    document.getElementById('qty-input').value = '1';
    
    // Variants
    const variantsEl = document.getElementById('modal-variants');
    if (product.variants?.length) {
        variantsEl.innerHTML = product.variants.map(v => `
            <button class="variant-btn" onclick="selectVariant(${v.id})">
                ${v.name} (+${v.price_modifier}₴)
            </button>
        `).join('');
        variantsEl.style.display = 'block';
    } else {
        variantsEl.style.display = 'none';
    }
    
    document.getElementById('product-modal').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
}

function closeModal() {
    document.getElementById('product-modal').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function incrementQty() {
    const input = document.getElementById('qty-input');
    input.value = Math.max(1, parseInt(input.value || 1) + 1);
}

function decrementQty() {
    const input = document.getElementById('qty-input');
    input.value = Math.max(1, parseInt(input.value || 1) - 1);
}

function addToCart() {
    if (!CURRENT_PRODUCT) return;
    
    const qty = parseInt(document.getElementById('qty-input').value || 1);
    const existing = CART.find(i => i.id === CURRENT_PRODUCT.id);
    
    if (existing) {
        existing.qty += qty;
    } else {
        CART.push({
            id: CURRENT_PRODUCT.id,
            name: CURRENT_PRODUCT.name,
            price: CURRENT_PRODUCT.base_price,
            image: CURRENT_PRODUCT.image,
            qty: qty
        });
    }
    
    saveCart();
    alert('✅ Додано в кошик!');
    closeModal();
}

async function toggleFavorite(productId) {
    if (!USER) {
        alert('⚠️ Увійдіть для додавання в вибране');
        return;
    }
    
    try {
        await fetch(`${API}/favorite/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: USER.id, product_id: productId})
        });
        
        if (FAVORITES.has(productId)) {
            FAVORITES.delete(productId);
        } else {
            FAVORITES.add(productId);
        }
        
        document.querySelectorAll(`[data-product="${productId}"] .btn-favorite`).forEach(btn => {
            btn.classList.toggle('active');
        });
        
        renderProducts(PRODUCTS);
    } catch (e) {
        console.error('Toggle favorite error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
// CART LOGIC
// ═══════════════════════════════════════════════════════════════

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(CART));
    updateCartBadge();
    renderCart();
}

function updateCartBadge() {
    const qty = CART.reduce((s, i) => s + i.qty, 0);
    const badge = document.getElementById('cart-count');
    if (badge) {
        badge.textContent = qty || '0';
        badge.style.display = qty > 0 ? 'block' : 'none';
    }
}

function renderCart() {
    const container = document.getElementById('cart-items');
    if (!container) return;
    
    if (CART.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:40px 20px; color:#999;">🛒 Кошик порожній</div>';
        document.getElementById('subtotal').textContent = '0₴';
        document.getElementById('total').textContent = '0₴';
        return;
    }
    
    let subtotal = 0;
    
    container.innerHTML = CART.map((item, i) => {
        const itemTotal = item.price * item.qty;
        subtotal += itemTotal;
        
        return `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}" style="width:60px; height:60px; object-fit:cover; border-radius:8px;">
                <div class="cart-details" style="flex:1; margin:0 10px;">
                    <div><strong>${item.name}</strong></div>
                    <div style="color:#999;">${item.price}₴</div>
                    <div class="qty-control" style="margin-top:5px;">
                        <button onclick="changeQty(${i}, -1)" style="width:24px; height:24px;">−</button>
                        <span style="margin:0 8px;">${item.qty}</span>
                        <button onclick="changeQty(${i}, 1)" style="width:24px; height:24px;">+</button>
                    </div>
                </div>
                <button onclick="removeFromCart(${i})" style="background:none; border:none; color:red; cursor:pointer; font-size:18px;">✕</button>
            </div>
        `;
    }).join('');
    
    const discount = APPLIED_PROMO?.discount || 0;
    const total = Math.max(0, subtotal - discount);
    
    document.getElementById('subtotal').textContent = `${subtotal}₴`;
    document.getElementById('total').textContent = `${total}₴`;
    
    if (discount > 0) {
        document.getElementById('discount-row').style.display = 'flex';
        document.getElementById('discount-amount').textContent = `-${discount}₴`;
    } else {
        document.getElementById('discount-row').style.display = 'none';
    }
}

function changeQty(index, delta) {
    CART[index].qty += delta;
    if (CART[index].qty <= 0) CART.splice(index, 1);
    saveCart();
}

function removeFromCart(index) {
    CART.splice(index, 1);
    saveCart();
}

// ═══════════════════════════════════════════════════════════════
// CHECKOUT
// ═══════════════════════════════════════════════════════════════

function showCheckout() {
    if (CART.length === 0) {
        alert('⚠️ Кошик порожній');
        return;
    }
    document.getElementById('checkout-form').style.display = 'block';
    document.getElementById('checkout-btn').style.display = 'none';
}

async function applyPromoCode() {
    const code = document.getElementById('promo-code').value.trim();
    if (!code) return;
    
    const total = CART.reduce((s, i) => s + i.price * i.qty, 0);
    
    try {
        const res = await fetch(`${API}/promocode/validate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `code=${code}&user_id=${USER?.id || 0}&cart_total=${total}`
        });
        const data = await res.json();
        
        if (data.valid) {
            APPLIED_PROMO = data;
            alert(`✅ ${data.message}`);
            renderCart();
        } else {
            alert('❌ ' + (data.message || 'Невірний промокод'));
        }
    } catch (e) {
        alert('❌ Помилка промокоду');
    }
}

async function submitOrder() {
    const name = document.getElementById('order-name').value.trim();
    const phone = document.getElementById('order-phone').value.trim();
    const city = document.getElementById('city-search').value.trim();
    const warehouse = document.getElementById('warehouse-select').value;
    
    if (!name || !phone || !city || !warehouse) {
        alert('⚠️ Заповніть усі поля');
        return;
    }
    
    const orderData = {
        user_id: USER?.id || 0,
        init_data: tg?.initData || '',
        customer_name: name,
        customer_phone: phone,
        delivery_method: 'nova_poshta',
        delivery_city: city,
        delivery_warehouse: warehouse,
        items: CART.map(i => ({product_id: i.id, quantity: i.qty, price: i.price})),
        total_price: CART.reduce((s, i) => s + i.price * i.qty, 0)
    };
    
    try {
        const res = await fetch(`${API}/order/create`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(orderData)
        });
        const data = await res.json();
        
        if (data.success) {
            CART = [];
            saveCart();
            alert(`✅ Замовлення #${data.order_number} створено!\n\nМи зв'яжемось з вами найближчим часом.`);
            navigateTo('shop');
        } else {
            alert('❌ Помилка: ' + (data.detail || data.error || 'Невідома помилка'));
        }
    } catch (e) {
        alert('❌ Помилка створення замовлення');
    }
}

// ═══════════════════════════════════════════════════════════════
// NOVA POSHTA
// ═══════════════════════════════════════════════════════════════

async function searchCities(e) {
    const q = e.target.value.trim();
    const suggestions = document.getElementById('city-suggestions');
    
    if (q.length < 2) {
        suggestions.innerHTML = '';
        return;
    }
    
    try {
        const res = await fetch(`${API}/np/cities?q=${q}`);
        const data = await res.json();
        
        suggestions.innerHTML = (data.cities || []).map(city => `
            <div class="suggestion-item" onclick="selectCity('${city.ref}', '${city.description}')">
                ${city.description}
            </div>
        `).join('');
    } catch (e) {
        console.error('City search error:', e);
    }
}

async function selectCity(ref, description) {
    document.getElementById('city-search').value = description;
    document.getElementById('city-suggestions').innerHTML = '';
    document.getElementById('warehouse-select').style.display = 'block';
    
    try {
        const res = await fetch(`${API}/np/warehouses?city_ref=${ref}`);
        const data = await res.json();
        
        const select = document.getElementById('warehouse-select');
        select.innerHTML = '<option>Оберіть відділення</option>';
        
        (data.warehouses || []).forEach(wh => {
            const opt = document.createElement('option');
            opt.value = wh.ref;
            opt.textContent = wh.description;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Warehouse load error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
// FAVORITES
// ═══════════════════════════════════════════════════════════════

function renderFavorites() {
    const container = document.getElementById('favorites-grid');
    const favProducts = PRODUCTS.filter(p => FAVORITES.has(p.id));
    
    if (favProducts.length === 0) {
        container.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px;">❤️ Немає улюблених</div>';
        return;
    }
    
    renderProducts(favProducts);
}

// ═══════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════

function copyReferralCode() {
    const code = document.getElementById('referral-code').value;
    if (!code) return;
    navigator.clipboard.writeText(code);
    alert('✅ Скопійовано!');
}

function shareReferralCode() {
    const code = document.getElementById('referral-code').value;
    if (!code) return;
    
    if (navigator.share) {
        navigator.share({
            title: 'MiniShop',
            text: `Приєднайтеся за кодом: ${code}`
        });
    } else {
        alert('Код: ' + code);
    }
}

console.log('✅ App loaded');
