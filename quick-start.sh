#!/bin/bash

# Швидкий старт GraphRAG Web Platform
# Цей скрипт автоматично налаштовує та запускає систему

set -e

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# ASCII Art логотип
echo -e "${PURPLE}"
cat << "EOF"
   ____                 _     _____            _____ 
  / ___|_ __ __ _ _ __ | |__ |  _  \     /\   / ____|
 | |  _| '__/ _` | '_ \| '_ \| |_) |    /  \ | |  __ 
 | |_| | | | (_| | |_) | | | |  _ <    / /\ \| | |_ |
  \____|_|  \__,_| .__/|_| |_|_| \_\  / ____ \ |__| |
                 | |                /_/    \_\_____|
                 |_|                                 
   Web Platform for Knowledge Graphs
EOF
echo -e "${NC}"

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

# Функція для перевірки команд
check_command() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# Перевірка системних вимог
step "Перевірка системних вимог..."

# Перевірка операційної системи
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    info "✅ Linux OS виявлено"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    info "✅ macOS виявлено"
else
    warn "⚠️  Не перевірена операційна система: $OSTYPE"
fi

# Перевірка Docker
if check_command docker; then
    info "✅ Docker встановлено"
    if docker --version | grep -q "Docker version"; then
        DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
        info "   Версія: $DOCKER_VERSION"
    fi
else
    error "❌ Docker не встановлено. Встановіть Docker і спробуйте знову."
fi

# Перевірка Docker Compose
if check_command docker-compose || docker compose version &>/dev/null; then
    info "✅ Docker Compose доступний"
else
    error "❌ Docker Compose не встановлено"
fi

# Перевірка Node.js
if check_command node; then
    info "✅ Node.js встановлено"
    NODE_VERSION=$(node --version)
    info "   Версія: $NODE_VERSION"
    
    # Перевірка мінімальної версії
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        warn "⚠️  Рекомендується Node.js 18+, поточна версія: $NODE_VERSION"
    fi
else
    error "❌ Node.js не встановлено. Встановіть Node.js 18+ і спробуйте знову."
fi

# Перевірка npm
if check_command npm; then
    info "✅ npm встановлено"
    NPM_VERSION=$(npm --version)
    info "   Версія: $NPM_VERSION"
else
    error "❌ npm не встановлено"
fi

# Перевірка Python (опціонально)
if check_command python3; then
    info "✅ Python 3 встановлено"
    PYTHON_VERSION=$(python3 --version)
    info "   Версія: $PYTHON_VERSION"
else
    warn "⚠️  Python 3 не встановлено (потрібно для ручного запуску)"
fi

echo

# Меню вибору способу запуску
step "Виберіть спосіб запуску:"
echo "1) Docker Compose (рекомендовано)"
echo "2) Локальна розробка"
echo "3) Тестування API"
echo "4) Перевірка налаштувань"
echo

read -p "Введіть номер (1-4): " choice

case $choice in
    1)
        step "🐳 Запуск через Docker Compose"
        
        # Перевірка .env файлу
        if [ ! -f ".env" ]; then
            info "Створення .env файлу з прикладу..."
            cp env.example .env
            warn "⚠️  ВАЖЛИВО: Відредагуйте .env файл та додайте свій OpenAI API key!"
            echo
            read -p "Натисніть Enter після редагування .env файлу..."
        fi
        
        # Перевірка API key
        if grep -q "sk-your-openai-api-key-here" .env; then
            error "❌ Будь ласка, замініть 'sk-your-openai-api-key-here' на справжній OpenAI API key у .env файлі"
        fi
        
        info "OpenAI API key знайдено ✅"
        
        # Збірка frontend
        step "Збірка frontend..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            info "Встановлення npm залежностей..."
            npm install
        fi
        
        info "Збірка Next.js додатку..."
        npm run build
        cd ..
        
        # Запуск Docker Compose
        step "Запуск Docker контейнерів..."
        
        # Вибір compose команди
        if command -v docker-compose &> /dev/null; then
            COMPOSE_CMD="docker-compose"
        else
            COMPOSE_CMD="docker compose"
        fi
        
        # Збірка і запуск
        $COMPOSE_CMD build
        $COMPOSE_CMD up -d
        
        # Очікування запуску
        info "Очікування запуску сервісів..."
        sleep 15
        
        # Перевірка здоров'я
        step "Перевірка стану сервісів..."
        
        if curl -f http://localhost:8000/health &>/dev/null; then
            info "✅ Backend працює (http://localhost:8000)"
        else
            warn "⚠️  Backend не відповідає"
        fi
        
        if curl -f http://localhost:3000 &>/dev/null; then
            info "✅ Frontend працює (http://localhost:3000)"
        else
            warn "⚠️  Frontend не відповідає"
        fi
        
        echo
        info "🎉 Запуск завершено!"
        echo
        echo "📋 Доступні сервіси:"
        echo "  🌐 Frontend: http://localhost:3000"
        echo "  🔗 Backend API: http://localhost:8000"
        echo "  📚 API Docs: http://localhost:8000/docs"
        echo "  💚 Health: http://localhost:8000/health"
        echo
        echo "📊 Корисні команди:"
        echo "  Логи: $COMPOSE_CMD logs -f"
        echo "  Зупинка: $COMPOSE_CMD down"
        echo "  Перезапуск: $COMPOSE_CMD restart"
        ;;
        
    2)
        step "🛠️  Налаштування локальної розробки"
        
        # Backend
        info "Налаштування backend..."
        cd backend
        
        if [ ! -d "venv" ]; then
            info "Створення Python virtual environment..."
            python3 -m venv venv
        fi
        
        info "Активація venv та встановлення залежностей..."
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        cd ..
        
        # Frontend
        info "Налаштування frontend..."
        cd frontend
        
        if [ ! -d "node_modules" ]; then
            info "Встановлення npm залежностей..."
            npm install
        fi
        cd ..
        
        # Створення .env
        if [ ! -f ".env" ]; then
            cp env.example .env
        fi
        
        # Створення startup скриптів
        cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF
        
        cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
        
        chmod +x start-backend.sh start-frontend.sh
        
        echo
        info "🎉 Локальна розробка налаштована!"
        echo
        echo "📋 Для запуску:"
        echo "  Backend: ./start-backend.sh"
        echo "  Frontend: ./start-frontend.sh"
        echo
        echo "⚠️  Не забудьте додати OpenAI API key у .env файл!"
        ;;
        
    3)
        step "🧪 Тестування API"
        
        # Перевірка, чи працює backend
        if ! curl -f http://localhost:8000/health &>/dev/null; then
            error "❌ Backend не працює. Запустіть спочатку систему."
        fi
        
        info "✅ Backend доступний"
        
        # Тестування основних endpoints
        echo
        info "Тестування endpoints..."
        
        # Health check
        echo -n "Health check: "
        if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' &>/dev/null; then
            echo -e "${GREEN}✅ OK${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
        
        # Files endpoint
        echo -n "Files API: "
        if curl -s http://localhost:8000/api/files &>/dev/null; then
            echo -e "${GREEN}✅ OK${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
        
        # Chat health
        echo -n "Chat API: "
        if curl -s http://localhost:8000/api/chat/health &>/dev/null; then
            echo -e "${GREEN}✅ OK${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
        
        echo
        info "🎉 Тестування завершено!"
        ;;
        
    4)
        step "🔍 Перевірка налаштувань"
        
        # Перевірка .env
        if [ -f ".env" ]; then
            info "✅ .env файл існує"
            
            if grep -q "OPENAI_API_KEY=sk-" .env && ! grep -q "sk-your-openai-api-key-here" .env; then
                info "✅ OpenAI API key налаштований"
            else
                warn "⚠️  OpenAI API key не налаштований правильно"
            fi
        else
            warn "⚠️  .env файл не знайдено"
        fi
        
        # Перевірка структури проєкту
        info "Перевірка структури проєкту..."
        
        directories=("backend" "frontend" "config" "scripts" "data")
        for dir in "${directories[@]}"; do
            if [ -d "$dir" ]; then
                echo "  ✅ $dir/"
            else
                echo "  ❌ $dir/ (відсутня)"
            fi
        done
        
        # Перевірка Docker
        if [ -f "docker-compose.yml" ]; then
            info "✅ docker-compose.yml знайдено"
        else
            warn "⚠️  docker-compose.yml не знайдено"
        fi
        
        # Перевірка портів
        info "Перевірка доступності портів..."
        
        ports=(3000 8000)
        for port in "${ports[@]}"; do
            if lsof -i :$port &>/dev/null; then
                warn "⚠️  Порт $port зайнятий"
            else
                echo "  ✅ Порт $port вільний"
            fi
        done
        
        echo
        info "🎉 Перевірка завершена!"
        ;;
        
    *)
        error "❌ Невірний вибір. Використовуйте 1-4."
        ;;
esac

echo
echo -e "${PURPLE}======================================${NC}"
echo -e "${PURPLE}  GraphRAG Web Platform${NC}"
echo -e "${PURPLE}  Готово до використання!${NC}"
echo -e "${PURPLE}======================================${NC}"
echo
echo "📚 Додаткові ресурси:"
echo "  📖 Документація: README.md"
echo "  🔧 API приклади: examples/api_examples.md"
echo "  🚀 Деплоймент: scripts/deploy.sh"
echo "  💾 Backup: scripts/backup.sh"
echo
echo "❓ Потрібна допомога? Перевірте README.md або створіть issue на GitHub"
