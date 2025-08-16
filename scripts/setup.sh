#!/bin/bash

# Скрипт налаштування GraphRAG Web Platform на Ubuntu Server
# Використання: sudo ./setup.sh

set -e

echo "🚀 Встановлення GraphRAG Web Platform..."

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функції для виводу
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

# Перевірка прав root
if [[ $EUID -ne 0 ]]; then
   error "Цей скрипт повинен виконуватися від root (sudo)"
fi

# Оновлення системи
info "Оновлення системних пакетів..."
apt update && apt upgrade -y

# Встановлення базових залежностей
info "Встановлення базових залежностей..."
apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    nginx \
    supervisor \
    htop \
    unzip

# Встановлення Python 3.11
info "Встановлення Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-dev python3.11-venv python3-pip

# Встановлення Node.js 18
info "Встановлення Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Встановлення Docker (опціонально)
info "Встановлення Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Створення користувача graphrag
info "Створення користувача graphrag..."
if ! id "graphrag" &>/dev/null; then
    useradd -m -s /bin/bash graphrag
    usermod -aG docker graphrag
fi

# Створення директорій
info "Створення структури директорій..."
INSTALL_DIR="/opt/graphrag-web-platform"
mkdir -p $INSTALL_DIR/{backend,frontend,data/{uploads,output,metadata,cache},logs,config}

# Встановлення правильних прав доступу
chown -R graphrag:graphrag $INSTALL_DIR
chmod -R 755 $INSTALL_DIR

# Копіювання файлів проекту
info "Копіювання файлів проекту..."
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Backend
cp -r $PROJECT_DIR/backend/* $INSTALL_DIR/backend/
cp $PROJECT_DIR/config/settings.yml $INSTALL_DIR/config/

# Frontend (тільки збірка)
if [ -d "$PROJECT_DIR/frontend/.next" ]; then
    cp -r $PROJECT_DIR/frontend/.next $INSTALL_DIR/frontend/
    cp $PROJECT_DIR/frontend/package.json $INSTALL_DIR/frontend/
    cp $PROJECT_DIR/frontend/next.config.js $INSTALL_DIR/frontend/
else
    warn "Frontend збірка не знайдена. Виконайте 'npm run build' у frontend директорії"
fi

# Створення Python virtual environment
info "Створення Python virtual environment..."
cd $INSTALL_DIR
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Встановлення Node.js залежностей для frontend
info "Встановлення Node.js залежностей..."
cd $INSTALL_DIR/frontend
npm ci --only=production

# Копіювання systemd сервісів
info "Налаштування systemd сервісів..."
cp $PROJECT_DIR/systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# Налаштування Nginx
info "Налаштування Nginx..."
cp $PROJECT_DIR/nginx/nginx.conf /etc/nginx/sites-available/graphrag
ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Створення SSL сертифікатів (self-signed для development)
info "Створення SSL сертифікатів..."
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=UA/ST=Ukraine/L=Kyiv/O=GraphRAG/OU=IT/CN=localhost"

# Налаштування файрволу
info "Налаштування файрволу..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Створення .env файлу
info "Створення .env файлу..."
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > $ENV_FILE << EOL
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# GraphRAG Configuration
GRAPHRAG_LLM_MODEL=gpt-4o-2024-11-20
GRAPHRAG_EMBEDDING_MODEL=text-embedding-3-large
GRAPHRAG_REASONING_EFFORT=high
GRAPHRAG_MAX_COMPLETION_TOKENS=4096

# Application Configuration
UPLOAD_MAX_SIZE=104857600
UPLOAD_DIR=$INSTALL_DIR/data/uploads
OUTPUT_DIR=$INSTALL_DIR/data/output
METADATA_DIR=$INSTALL_DIR/data/metadata
CACHE_DIR=$INSTALL_DIR/data/cache

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://localhost,https://your-domain.com

# Worker Configuration
WORKER_THREADS=4
MAX_CONCURRENT_INDEXING=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=$INSTALL_DIR/logs/app.log

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
DEBUG=False
EOL
    chown graphrag:graphrag $ENV_FILE
    chmod 600 $ENV_FILE
fi

# Встановлення прав доступу
chown -R graphrag:graphrag $INSTALL_DIR
chmod +x $INSTALL_DIR/backend/app/main.py

# Створення логротate конфігурації
info "Налаштування ротації логів..."
cat > /etc/logrotate.d/graphrag << EOL
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 graphrag graphrag
    postrotate
        systemctl reload graphrag-backend graphrag-frontend graphrag-worker
    endscript
}
EOL

# Запуск сервісів
info "Запуск сервісів..."
systemctl enable nginx
systemctl enable graphrag-backend
systemctl enable graphrag-frontend
systemctl enable graphrag-worker

systemctl start nginx
systemctl start graphrag-backend
sleep 5
systemctl start graphrag-frontend
systemctl start graphrag-worker

# Перевірка статусу
info "Перевірка статусу сервісів..."
sleep 10

if systemctl is-active --quiet graphrag-backend; then
    info "✅ Backend service запущено"
else
    error "❌ Backend service не запущено"
fi

if systemctl is-active --quiet graphrag-frontend; then
    info "✅ Frontend service запущено"
else
    warn "⚠️  Frontend service не запущено (можливо, потребує збірки)"
fi

if systemctl is-active --quiet nginx; then
    info "✅ Nginx запущено"
else
    error "❌ Nginx не запущено"
fi

# Завершення
info "🎉 Встановлення завершено!"
echo
echo "📋 Наступні кроки:"
echo "1. Відредагуйте $ENV_FILE та додайте свій OpenAI API key"
echo "2. Перезапустіть сервіси: systemctl restart graphrag-backend graphrag-frontend"
echo "3. Відкрийте https://your-server-ip у браузері"
echo
echo "📊 Корисні команди:"
echo "  Статус сервісів: systemctl status graphrag-backend graphrag-frontend"
echo "  Перегляд логів: journalctl -fu graphrag-backend"
echo "  Перезапуск: systemctl restart graphrag-backend"
echo
echo "📁 Структура проекту:"
echo "  Код: $INSTALL_DIR"
echo "  Дані: $INSTALL_DIR/data"
echo "  Логи: $INSTALL_DIR/logs"
echo "  Конфігурація: $INSTALL_DIR/.env"
