#!/bin/bash

# Скрипт деплойменту GraphRAG Web Platform
# Використання: ./deploy.sh [production|development]

set -e

# Параметри
ENVIRONMENT=${1:-development}
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функції
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Перевірка середовища
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "development" ]]; then
    error "Невідоме середовище: $ENVIRONMENT. Використовуйте 'production' або 'development'"
fi

step "🚀 Деплоймент GraphRAG Web Platform ($ENVIRONMENT)"

# Перевірка наявності Docker
if ! command -v docker &> /dev/null; then
    error "Docker не встановлено. Встановіть Docker та спробуйте знову."
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    error "Docker Compose не встановлено. Встановіть Docker Compose та спробуйте знову."
fi

# Функція для docker compose (підтримка обох версій)
docker_compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Перехід до директорії проекту
cd "$PROJECT_DIR"

# Перевірка .env файлу
step "Перевірка конфігурації..."
if [ ! -f ".env" ]; then
    warn ".env файл не знайдено. Створюємо з прикладу..."
    cp env.example .env
    warn "⚠️  Відредагуйте .env файл та додайте свій OpenAI API key"
fi

# Валідація OpenAI API key
if grep -q "sk-your-openai-api-key-here" .env; then
    error "❌ Будь ласка, встановіть справжній OpenAI API key у .env файлі"
fi

# Збірка frontend (тільки якщо не в Docker режимі)
step "Перевірка frontend..."

# Перевірка наявності Node.js для локальної збірки
if command -v node &> /dev/null; then
    info "Node.js знайдено, підготовка frontend..."
    cd frontend
    
    # Встановлення залежностей якщо потрібно
    if [ ! -d "node_modules" ]; then
        info "Встановлення npm залежностей..."
        npm install
    fi
    
    # Перевіряємо чи потрібна збірка (для development)
    if [ ! -d ".next" ] && [ "$ENVIRONMENT" = "development" ]; then
        info "Збірка frontend додатку..."
        npm run build
    fi
    
    cd ..
else
    info "Node.js не знайдено, збірка буде виконана в Docker контейнері"
fi

# Збірка та запуск контейнерів
step "Збірка Docker образів..."
docker_compose build --no-cache

step "Запуск сервісів..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker_compose -f docker-compose.yml up -d
else
    docker_compose up -d
fi

# Очікування запуску сервісів
step "Очікування запуску сервісів..."
sleep 15

# Перевірка здоров'я сервісів
step "Перевірка здоров'я сервісів..."

# Перевірка backend
if curl -f http://localhost:8000/health &>/dev/null; then
    info "✅ Backend service працює"
else
    error "❌ Backend service не відповідає"
fi

# Перевірка frontend
if curl -f http://localhost:3000 &>/dev/null; then
    info "✅ Frontend service працює"
else
    warn "⚠️  Frontend service може ще запускатися..."
fi

# Перевірка Redis
if docker_compose ps redis | grep -q "Up"; then
    info "✅ Redis працює"
else
    warn "⚠️  Redis не запущено"
fi

# Відображення статусу
step "Статус контейнерів:"
docker_compose ps

# Відображення логів (останні 20 рядків)
step "Останні логи backend:"
docker_compose logs --tail=20 backend

# Інструкції для користувача
step "🎉 Деплоймент завершено!"
echo
echo "📋 Інформація про сервіси:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API документація: http://localhost:8000/docs"
echo "  Health check: http://localhost:8000/health"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "  Nginx: http://localhost (якщо налаштовано)"
fi

echo
echo "📊 Корисні команди:"
echo "  Перегляд логів: docker-compose logs -f [service-name]"
echo "  Перезапуск: docker-compose restart [service-name]"
echo "  Зупинка: docker-compose down"
echo "  Статус: docker-compose ps"
echo
echo "🔧 Налаштування:"
echo "  Конфігурація: .env"
echo "  GraphRAG налаштування: config/settings.yml"
echo "  Дані зберігаються у: ./data/"

# Додаткові інструкції для production
if [ "$ENVIRONMENT" = "production" ]; then
    echo
    echo "🔒 Рекомендації для production:"
    echo "  1. Налаштуйте SSL сертифікати у nginx/ssl/"
    echo "  2. Змініть SECRET_KEY у .env файлі"
    echo "  3. Налаштуйте файрвол та обмежте доступ"
    echo "  4. Налаштуйте резервне копіювання директорії ./data/"
    echo "  5. Налаштуйте моніторинг та логування"
fi

# Перевірка помилок
if [ $? -eq 0 ]; then
    info "✅ Деплоймент успішно завершено!"
else
    error "❌ Сталися помилки під час деплойменту"
fi
