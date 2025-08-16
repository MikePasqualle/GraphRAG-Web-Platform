#!/bin/bash

# Скрипт резервного копіювання GraphRAG Web Platform
# Використання: ./backup.sh [backup-directory]

set -e

# Параметри
BACKUP_DIR=${1:-"/opt/graphrag-backups"}
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="graphrag_backup_$TIMESTAMP"

# Кольори
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

info "🗄️  Початок резервного копіювання GraphRAG Web Platform"

# Створення директорії для backup
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$BACKUP_PATH"

info "Backup буде збережено у: $BACKUP_PATH"

# Функція backup для Docker
backup_docker() {
    info "Створення backup Docker середовища..."
    
    cd "$PROJECT_DIR"
    
    # Backup docker-compose конфігурації
    cp docker-compose.yml "$BACKUP_PATH/"
    cp .env "$BACKUP_PATH/" 2>/dev/null || warn ".env файл не знайдено"
    
    # Backup даних контейнерів
    if docker-compose ps | grep -q "Up"; then
        info "Створення backup томів Docker..."
        
        # Backup Redis даних (якщо використовується)
        if docker-compose ps redis | grep -q "Up"; then
            docker-compose exec -T redis redis-cli BGSAVE
            sleep 5
            docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis_dump.rdb"
        fi
        
        # Backup файлів з контейнера backend
        docker cp $(docker-compose ps -q backend):/app/data "$BACKUP_PATH/backend_data"
        docker cp $(docker-compose ps -q backend):/app/logs "$BACKUP_PATH/backend_logs"
    else
        warn "Docker контейнери не запущені. Backup буде створено з локальних файлів."
    fi
}

# Функція backup для systemd
backup_systemd() {
    info "Створення backup systemd середовища..."
    
    INSTALL_DIR="/opt/graphrag-web-platform"
    
    if [ -d "$INSTALL_DIR" ]; then
        # Backup даних
        cp -r "$INSTALL_DIR/data" "$BACKUP_PATH/"
        cp -r "$INSTALL_DIR/logs" "$BACKUP_PATH/"
        cp -r "$INSTALL_DIR/config" "$BACKUP_PATH/"
        cp "$INSTALL_DIR/.env" "$BACKUP_PATH/" 2>/dev/null || warn ".env файл не знайдено"
        
        # Backup systemd сервісів
        mkdir -p "$BACKUP_PATH/systemd"
        cp /etc/systemd/system/graphrag-*.service "$BACKUP_PATH/systemd/" 2>/dev/null || warn "Systemd сервіси не знайдено"
        
        # Backup Nginx конфігурації
        mkdir -p "$BACKUP_PATH/nginx"
        cp /etc/nginx/sites-available/graphrag "$BACKUP_PATH/nginx/" 2>/dev/null || warn "Nginx конфігурація не знайдена"
        cp -r /etc/nginx/ssl "$BACKUP_PATH/nginx/" 2>/dev/null || warn "SSL сертифікати не знайдені"
    else
        error "Установка GraphRAG не знайдена у $INSTALL_DIR"
    fi
}

# Визначення типу установки та виконання backup
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    backup_docker
elif [ -d "/opt/graphrag-web-platform" ]; then
    backup_systemd
else
    error "Не вдалося визначити тип установки GraphRAG"
fi

# Backup коду проекту
info "Копіювання коду проекту..."
cp -r "$PROJECT_DIR/backend" "$BACKUP_PATH/"
cp -r "$PROJECT_DIR/frontend" "$BACKUP_PATH/"
cp -r "$PROJECT_DIR/config" "$BACKUP_PATH/" 2>/dev/null || true
cp -r "$PROJECT_DIR/scripts" "$BACKUP_PATH/"
cp "$PROJECT_DIR/README.md" "$BACKUP_PATH/" 2>/dev/null || true

# Створення метаданих backup
info "Створення метаданих backup..."
cat > "$BACKUP_PATH/backup_info.txt" << EOL
GraphRAG Web Platform Backup
============================
Дата створення: $(date)
Версія: 1.0.0
Hostname: $(hostname)
User: $(whoami)
Backup path: $BACKUP_PATH

Вміст backup:
- Код додатку (backend, frontend)
- Дані користувачів (uploads, output, metadata)
- Логи системи
- Конфігураційні файли
- Systemd сервіси (якщо застосовно)
- Nginx конфігурація (якщо застосовно)

Для відновлення:
1. Розпакуйте backup у відповідну директорію
2. Відновіть .env файл з налаштуваннями
3. Перезапустіть сервіси
EOL

# Створення архіву
info "Створення архіву..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Перевірка розміру backup
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
info "✅ Backup успішно створено: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"

# Очищення старих backup (збереження останніх 7)
info "Очищення старих backup..."
cd "$BACKUP_DIR"
ls -t graphrag_backup_*.tar.gz | tail -n +8 | xargs -r rm
REMAINING_BACKUPS=$(ls -1 graphrag_backup_*.tar.gz 2>/dev/null | wc -l)
info "Залишилося backup файлів: $REMAINING_BACKUPS"

# Фінальна інформація
echo
info "🎉 Backup завершено!"
echo "📁 Розташування: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "📊 Розмір: $BACKUP_SIZE"
echo
echo "📋 Для відновлення:"
echo "  1. Розпакуйте архів: tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  2. Скопіюйте дані у відповідні директорії"
echo "  3. Відновіть сервіси та конфігурацію"
echo
echo "💡 Рекомендується регулярно створювати backup та зберігати їх у безпечному місці"
