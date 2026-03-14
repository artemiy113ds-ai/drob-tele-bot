#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# 🚀 TELEGRAM MINI APP E-COMMERCE - INSTALLATION SCRIPT
# ═══════════════════════════════════════════════════════════════════
# Run with: chmod +x install.sh && ./install.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ───────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ───────────────────────────────────────────────────────────────────

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ───────────────────────────────────────────────────────────────────
# CHECK REQUIREMENTS
# ───────────────────────────────────────────────────────────────────

print_header "🔍 Перевірка вимог"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 3 знайдено ($PYTHON_VERSION)"
else
    print_error "Python 3 не встановлено!"
    echo "Встановіть Python 3.12+ з https://python.org"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_success "pip знайдено"
else
    print_error "pip не встановлено!"
    exit 1
fi

# Check git (optional)
if command -v git &> /dev/null; then
    print_success "Git знайдено"
else
    print_warning "Git не встановлено (опціонально)"
fi

# ───────────────────────────────────────────────────────────────────
# CHECK OPTIONAL: DOCKER
# ───────────────────────────────────────────────────────────────────

DOCKER_AVAILABLE=false
if command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
    print_success "Docker знайдено"
else
    print_warning "Docker не встановлено. Ви зможете встановити локально, але Docker рекомендується для production."
fi

# ───────────────────────────────────────────────────────────────────
# CREATE VIRTUAL ENVIRONMENT
# ───────────────────────────────────────────────────────────────────

print_header "🐍 Створення Virtual Environment"

if [ -d "venv" ]; then
    print_warning "venv уже існує"
    read -p "Видалити вже існуючий venv? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual Environment創建ено"
    fi
else
    python3 -m venv venv
    print_success "Virtual Environment創建ено"
fi

# Activate venv
source venv/bin/activate
print_success "Virtual Environment активовано"

# ───────────────────────────────────────────────────────────────────
# INSTALL DEPENDENCIES
# ───────────────────────────────────────────────────────────────────

print_header "📦 Встановлення залежностей"

# Upgrade pip
print_info "Оновлення pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "pip оновлено"

# Install requirements
if [ -f "requirements.txt" ]; then
    print_info "Встановлення из requirements.txt..."
    pip install -r requirements.txt
    print_success "Залежності встановлено"
else
    print_error "requirements.txt не знайдено!"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────────────────────────

print_header "⚙️  Конфігурація"

# Check if .env exists
if [ -f ".env" ]; then
    print_warning ".env файл уже існує"
    read -p "Перезаписати? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Пропускаємо конфігурацію"
        goto_next="true"
    fi
fi

if [ "$goto_next" != "true" ]; then
    # Copy .env template
    cp .env.example .env 2>/dev/null || {
        print_warning ".env.example не знайдено, створюю базовий .env"
        cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_token_here
ADMIN_PASSWORD=123
NOVA_POSHTA_API_KEY=your_key_here
EOF
    }
    
    print_success ".env файл створено"
    
    print_info "Редагування .env файлу:"
    echo "  - Відкрийте .env у текстовому редакторі"
    echo "  - Встановіть TELEGRAM_BOT_TOKEN від @BotFather"
    echo "  - Встановіть NOVA_POSHTA_API_KEY (якщо потрібно)"
    
    read -p "Натисніть Enter коли завершите редагування..."
fi

# ───────────────────────────────────────────────────────────────────
# CREATE DIRECTORIES
# ───────────────────────────────────────────────────────────────────

print_header "📁 Створення директорій"

mkdir -p logs
print_success "logs/ створено"

mkdir -p static/uploads
print_success "static/uploads/ створено"

mkdir -p static/banners
print_success "static/banners/ створено"

# ───────────────────────────────────────────────────────────────────
# INITIALIZE DATABASE
# ───────────────────────────────────────────────────────────────────

print_header "💾 Ініціалізація бази даних"

python3 << 'EOF'
from database import init_db
from gamification import create_gamification_tables

print("Creating main database schema...")
init_db()
print("✅ Main schema created")

print("Creating gamification tables...")
create_gamification_tables()
print("✅ Gamification tables created")

print("\n✅ Database initialized successfully!")
EOF

# ───────────────────────────────────────────────────────────────────
# DOCKER SETUP (optional)
# ───────────────────────────────────────────────────────────────────

if [ "$DOCKER_AVAILABLE" = true ]; then
    print_header "🐳 Docker Setup (опціонально)"
    
    read -p "Налаштувати Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Будування Docker образів..."
        docker-compose build
        print_success "Docker образи побудовані"
        
        read -p "Запустити Docker контейнери? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose up -d
            print_success "Docker контейнери запущені!"
            echo -e "\n${GREEN}Доступні адреси:${NC}"
            echo "  🌐 Web App: http://localhost:8000"
            echo "  ⚙️  Admin: http://localhost:8000/admin"
            echo "  📚 API Docs: http://localhost:8000/api/docs"
        fi
    fi
fi

# ───────────────────────────────────────────────────────────────────
# FINAL INSTRUCTIONS
# ───────────────────────────────────────────────────────────────────

print_header "✅ Встановлення завершено!"

echo -e "${GREEN}Наступні кроки:${NC}\n"

if [ "$DOCKER_AVAILABLE" = true ] && [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "1. Docker контейнери вже запущені!"
    echo "2. Перейдіть на http://localhost:8000"
    echo "3. Відкрийте Telegram бот і протестуйте"
else
    echo "1. Активуйте virtual environment:"
    echo "   ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo "2. Запустіть Telegram Bot в одному терміналі:"
    echo "   ${YELLOW}python bot_v3.py${NC}"
    echo ""
    echo "3. Запустіть FastAPI у другому терміналі:"
    echo "   ${YELLOW}uvicorn main_v3:app --reload${NC}"
    echo ""
    echo "4. Перейдіть на http://127.0.0.1:8000"
fi

echo ""
echo -e "${GREEN}Корисні команди:${NC}"
echo "  ${YELLOW}python -m pytest tests/${NC}              - Запустити тести"
echo "  ${YELLOW}python -m black .${NC}                   - Форматувати код"
echo "  ${YELLOW}docker-compose logs -f${NC}              - Переглянути логи"
echo ""
echo -e "${GREEN}Документація:${NC}"
echo "  📖 README.md         - Основна документація"
echo "  📚 docs/API.md       - API документація"
echo "  🐳 docker-compose.yml - Docker конфіг"
echo ""

print_success "В`єм питання? Відкрийте issue на GitHub!"
